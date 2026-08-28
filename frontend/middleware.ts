import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PROTECTED = ["/app"];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  const isProtected = PROTECTED.some((p) => pathname === p || pathname.startsWith(p + "/"));
  if (!isProtected) return NextResponse.next();

  const refreshToken = request.cookies.get("refresh_token")?.value;
  if (!refreshToken) {
    return NextResponse.redirect(new URL("/login", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*"],
};
