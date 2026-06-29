import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const COOKIE_NAME = "snaptoon_token";

/**
 * Middleware Next.js: redirect a /login se il cookie auth non è presente.
 *
 * Verifica solo la PRESENZA del cookie (non valida il JWT). La validazione
 * vera avviene su FastAPI quando si fa fetch dell'API. Se il cookie è
 * scaduto/invalido, gli endpoint risponderanno 401 e il client redirigerà.
 */
export function middleware(request: NextRequest) {
  const token = request.cookies.get(COOKIE_NAME);
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*"],
};
