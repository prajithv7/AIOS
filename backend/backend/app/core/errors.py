from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import uuid


ERROR_MESSAGES = {
    "AUTH_REQUIRED": "Authentication required",
    "FORBIDDEN": "Access denied",
    "INVALID_REQUEST": "Invalid request parameters",
    "MODEL_NOT_FOUND": "Model not found",
    "PROVIDER_NOT_FOUND": "Provider not found",
    "PROVIDER_UNAUTHORIZED": "Provider API key invalid or missing",
    "PROVIDER_UNAVAILABLE": "The selected AI provider is temporarily unavailable",
    "MODEL_UNAVAILABLE": "The selected model is temporarily unavailable",
    "RATE_LIMITED": "Rate limit exceeded",
    "CONTEXT_TOO_LARGE": "Conversation context exceeds model limit",
    "AI_REQUEST_FAILED": "AI request failed",
    "INTERNAL_ERROR": "Internal server error",
}


class AppError(Exception):
    def __init__(self, code: str, message: str = None, status_code: int = 400, details: dict = None):
        self.code = code
        self.message = message or ERROR_MESSAGES.get(code, "Error")
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


def error_response(code: str, message: str = None, status_code: int = None, details: dict = None, request_id: str = None) -> JSONResponse:
    request_id = request_id or str(uuid.uuid4())[:8]
    return JSONResponse(
        status_code=status_code or 400,
        content={"error": {"code": code, "message": message or ERROR_MESSAGES.get(code, "Error"), "requestId": request_id, **(details or {})}},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response("INVALID_REQUEST", "Validation failed", 422, {"errors": exc.errors()})


async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return error_response("INVALID_REQUEST", exc.detail, exc.status_code)


async def app_error_handler(request: Request, exc: AppError):
    return error_response(exc.code, exc.message, exc.status_code, exc.details)


async def generic_exception_handler(request: Request, exc: Exception):
    return error_response("INTERNAL_ERROR", "Internal server error", 500)