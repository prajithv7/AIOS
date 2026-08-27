"""Async SQLAlchemy dialect for Turso / libSQL.

The officially supported ``sqlalchemy-libsql`` package only provides a *sync*
DBAPI (``libsql_experimental``); its ``aiolibsql`` dialect incorrectly claims
``is_async=True`` while using a sync driver, so it cannot be used with
``create_async_engine`` / ``AsyncSession``.

This module adapts the *sync* ``libsql_experimental`` DBAPI to SQLAlchemy's
asyncio engine.  Each blocking call is offloaded to a thread via
``loop.run_in_executor`` and bridged back into the async engine using
SQLAlchemy's own ``await_only`` greenlet mechanism.  The AIOS schema, models,
migrations and services are left completely unchanged; only
``app/db/client.py`` points the engine at this dialect.

Auth: Turso requires the JWT to be passed as the ``auth_token`` keyword to
``libsql_experimental.connect()`` (it is NOT read from the URL query string).
"""

from __future__ import annotations

import asyncio
import collections
from typing import Any, Deque, Iterator, Optional, Sequence

import sqlite3

from sqlalchemy import pool, util
from sqlalchemy.dialects.sqlite.pysqlite import SQLiteDialect_pysqlite
from sqlalchemy.engine.url import URL
from sqlalchemy.util.concurrency import await_fallback
from sqlalchemy.util.concurrency import await_only
from sqlalchemy.util.concurrency import in_greenlet

import libsql_experimental


class AsyncAdapt_libsql_cursor:
    server_side = False
    __slots__ = (
        "_adapt_connection",
        "_connection",
        "await_",
        "_cursor",
        "_rows",
        "description",
        "rowcount",
        "lastrowid",
        "arraysize",
    )

    def __init__(self, adapt_connection: "AsyncAdapt_libsql_connection") -> None:
        self._adapt_connection = adapt_connection
        self._connection = adapt_connection._connection
        self.await_ = adapt_connection.await_
        self._cursor = self.await_(self._make_cursor())
        self.description: Optional[Any] = None
        self.rowcount = -1
        self.lastrowid = -1
        self.arraysize = 1
        self._rows: Deque = collections.deque()

    async def _make_cursor(self) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._connection.cursor)

    async def _async_soft_close(self) -> None:
        return

    def close(self) -> None:
        if self._cursor is not None and in_greenlet():
            self.await_(self._do_close())
        self._cursor = None
        self._rows.clear()

    async def _do_close(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._cursor.close)

    def execute(
        self,
        operation: Any,
        parameters: Optional[Any] = None,
    ) -> Any:
        try:
            self.await_(self._do_execute(operation, parameters))
            return self._cursor
        except Exception as error:
            self._adapt_connection._handle_exception(error)

    async def _do_execute(self, operation: Any, parameters: Optional[Any]) -> None:
        loop = asyncio.get_running_loop()
        if parameters is None:
            await loop.run_in_executor(None, self._cursor.execute, operation)
        else:
            await loop.run_in_executor(
                None, self._cursor.execute, operation, parameters
            )
        self.description = await loop.run_in_executor(
            None, lambda: self._cursor.description
        )
        self.lastrowid = await loop.run_in_executor(
            None, lambda: self._cursor.lastrowid
        )
        self.rowcount = await loop.run_in_executor(
            None, lambda: self._cursor.rowcount
        )
        if self.description and not self.server_side:
            rows = await loop.run_in_executor(None, self._cursor.fetchall)
            self._rows = collections.deque(rows)

    def executemany(
        self,
        operation: Any,
        seq_of_parameters: Sequence[Any],
    ) -> Any:
        try:
            self.await_(self._do_executemany(operation, seq_of_parameters))
            return self._cursor
        except Exception as error:
            self._adapt_connection._handle_exception(error)

    async def _do_executemany(
        self, operation: Any, seq_of_parameters: Sequence[Any]
    ) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self._cursor.executemany, operation, seq_of_parameters
        )
        self.description = None
        self.lastrowid = await loop.run_in_executor(
            None, lambda: self._cursor.lastrowid
        )
        self.rowcount = await loop.run_in_executor(
            None, lambda: self._cursor.rowcount
        )

    def setinputsizes(self, *inputsizes: Any) -> None:  # pragma: no cover
        pass

    def __iter__(self) -> Iterator[Any]:
        while self._rows:
            yield self._rows.popleft()

    def fetchone(self) -> Optional[Any]:
        if self._rows:
            return self._rows.popleft()
        return None

    def fetchmany(self, size: Optional[int] = None) -> Sequence[Any]:
        if size is None:
            size = self.arraysize
        rr = self._rows
        return [rr.popleft() for _ in range(min(size, len(rr)))]

    def fetchall(self) -> Sequence[Any]:
        retval = list(self._rows)
        self._rows.clear()
        return retval


class AsyncAdapt_libsql_ss_cursor(AsyncAdapt_libsql_cursor):
    server_side = True

    def close(self) -> None:
        if self._cursor is not None and in_greenlet():
            self.await_(self._do_close())
        self._cursor = None

    def fetchone(self) -> Optional[Any]:
        return self.await_(self._do_fetchone())

    async def _do_fetchone(self) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._cursor.fetchone)

    def fetchmany(self, size: Optional[int] = None) -> Any:
        return self.await_(self._do_fetchmany(size))

    async def _do_fetchmany(self, size: Optional[int]) -> Any:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._cursor.fetchmany, size)

    def fetchall(self) -> Sequence[Any]:
        return self.await_(self._do_fetchall())

    async def _do_fetchall(self) -> Sequence[Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._cursor.fetchall)


class AsyncAdapt_libsql_connection:
    await_ = staticmethod(await_only)
    __slots__ = ("dbapi", "_connection", "_execute_mutex")

    def __init__(self, dbapi: "AsyncAdapt_libsql_dbapi", connection: Any) -> None:
        self.dbapi = dbapi
        self._connection = connection
        self._execute_mutex = asyncio.Lock()

    def cursor(self, server_side: bool = False) -> AsyncAdapt_libsql_cursor:
        if server_side:
            return AsyncAdapt_libsql_ss_cursor(self)
        return AsyncAdapt_libsql_cursor(self)

    def execute(
        self,
        operation: Any,
        parameters: Optional[Any] = None,
    ) -> Any:
        cursor = self.cursor()
        cursor.execute(operation, parameters)
        return cursor

    def commit(self) -> None:
        try:
            self.await_(self._do_commit())
        except Exception as error:
            self._handle_exception(error)

    async def _do_commit(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connection.commit)

    def rollback(self) -> None:
        try:
            self.await_(self._do_rollback())
        except Exception as error:
            self._handle_exception(error)

    async def _do_rollback(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connection.rollback)

    def close(self) -> None:
        try:
            self.await_(self._do_close())
        except Exception as error:
            self._handle_exception(error)

    async def _do_close(self) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._connection.close)

    def _handle_exception(self, error: Exception) -> None:
        raise error

    @property
    def isolation_level(self) -> Optional[str]:
        try:
            return self._connection.isolation_level
        except Exception:
            return "SERIALIZABLE"

    @isolation_level.setter
    def isolation_level(self, value: Optional[str]) -> None:
        try:
            self._connection.isolation_level = value
        except Exception:
            pass


class AsyncAdaptFallback_libsql_connection(AsyncAdapt_libsql_connection):
    await_ = staticmethod(await_fallback)


class AsyncAdapt_libsql_dbapi:
    def __init__(self, libsql: Any) -> None:
        self.libsql = libsql
        self.paramstyle = "qmark"
        self._init_dbapi_attributes()

    def _init_dbapi_attributes(self) -> None:
        self.sqlite_version_info = getattr(
            self.libsql, "sqlite_version_info", sqlite3.sqlite_version_info
        )
        self.sqlite_version = getattr(
            self.libsql, "sqlite_version", sqlite3.sqlite_version
        )
        self.paramstyle = getattr(self.libsql, "paramstyle", "qmark")
        self.apilevel = "2.0"
        self.threadsafety = 1

        for name in ("Binary", "Date", "Time", "Timestamp"):
            setattr(self, name, getattr(sqlite3, name))

        try:
            from sqlite3 import dbapi2 as _dbapi2

            for name in ("STRING", "BINARY", "NUMBER", "DATETIME", "ROWID"):
                setattr(self, name, getattr(_dbapi2, name))
        except Exception:  # pragma: no cover
            class _DBAPIType:
                pass

            for name in ("STRING", "BINARY", "NUMBER", "DATETIME", "ROWID"):
                setattr(self, name, _DBAPIType())

        for name in (
            "Error",
            "Warning",
            "DatabaseError",
            "InterfaceError",
            "DataError",
            "OperationalError",
            "IntegrityError",
            "InternalError",
            "ProgrammingError",
            "NotSupportedError",
        ):
            setattr(self, name, getattr(self.libsql, name, Exception))

    def connect(self, *args: Any, **kwargs: Any) -> Any:
        async_fallback = kwargs.pop("async_fallback", False)

        async def _make() -> Any:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, lambda: self.libsql.connect(*args, **kwargs)
            )

        if util.asbool(async_fallback):
            connection = await_fallback(_make())
            return AsyncAdaptFallback_libsql_connection(self, connection)
        connection = await_only(_make())
        return AsyncAdapt_libsql_connection(self, connection)


class LibsqlAsyncDialect(SQLiteDialect_pysqlite):
    driver = "libsql"
    is_async = True
    supports_statement_cache = False

    @classmethod
    def import_dbapi(cls) -> AsyncAdapt_libsql_dbapi:
        return AsyncAdapt_libsql_dbapi(libsql_experimental)

    def create_connect_args(self, url: URL) -> Any:
        qs = dict(url.query)
        auth_token = qs.get("authToken")
        secure = str(qs.get("secure", "1")).lower() in ("1", "true", "yes", "on")
        scheme = "https" if secure else "http"
        host = url.host
        database = f"{scheme}://{host}"
        if url.database and url.database not in ("", "/"):
            database += url.database
        kw = {"auth_token": auth_token, "uri": True}
        return ([database], kw)

    @classmethod
    def get_pool_class(cls, url: URL) -> type:
        return pool.NullPool

    def on_connect(self) -> Any:
        # Remote libSQL (Turso/Hrana) does not support registering custom
        # user-defined functions (regexp, floor, ...).  Skip the pysqlite
        # on_connect UDF registration; the built-in SQL functions are present.
        def connect(conn: Any) -> None:
            pass

        return connect

    def get_isolation_level(self, dbapi_conn: Any) -> str:
        # Turso/Hrana does not support the pysqlite ``PRAGMA read_uncommitted``
        # probe; return a safe default instead of issuing a PRAGMA.
        return "SERIALIZABLE"

    def is_disconnect(
        self,
        e: Any,
        connection: Any,
        cursor: Any,
    ) -> bool:
        if isinstance(e, self.dbapi.OperationalError) and "no active connection" in str(
            e
        ):
            return True
        return super().is_disconnect(e, connection, cursor)

    def get_driver_connection(self, connection: Any) -> Any:
        return connection._connection

    def do_terminate(self, dbapi_connection: Any) -> None:
        dbapi_connection.terminate()


dialect = LibsqlAsyncDialect


def _register() -> None:
    from sqlalchemy.dialects import registry

    # Register the dialect object directly.  Using the string form
    # ``registry.register("libsql.async", "app.db.libsql_async", ...)`` would
    # make SQLAlchemy perform a ``getattr`` walk over the ``app.db`` package,
    # which fails because this module is imported while ``app.db`` is still
    # being initialised (circular import via ``app/db/__init__.py``).
    registry.impls["libsql.async"] = lambda: LibsqlAsyncDialect


_register()
