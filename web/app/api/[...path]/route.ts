/**
 * Catch-all API proxy: inoltra TUTTE le richieste /api/* a FastAPI backend
 * su localhost:8000 (interno al Repl).
 *
 * Sostituisce i rewrites() di next.config.ts che si comportano in modo
 * inconsistente in produzione su Replit (curl arriva, browser via dominio
 * pubblico no). Un'API route esplicita è 100% deterministica.
 *
 * Gestisce:
 *   - Tutti i metodi HTTP (GET/POST/PATCH/PUT/DELETE/OPTIONS)
 *   - Body binario o JSON via arrayBuffer
 *   - Cookie auth (httpOnly snaptoon_token) forward attraverso headers
 *   - Set-Cookie nella response (per login/logout)
 *   - Streaming responses (SSE per /api/kids/.../generate-stream)
 */
import { NextRequest, NextResponse } from "next/server";

const BACKEND = process.env.BACKEND_URL || "http://localhost:8000";

// Disabilita lo static optimization, il proxy è sempre dinamico
export const dynamic = "force-dynamic";

async function handler(
  request: NextRequest,
  ctx: { params: Promise<{ path: string[] }> }
): Promise<NextResponse> {
  const { path } = await ctx.params;
  const pathStr = path.join("/");
  const targetUrl = `${BACKEND}/api/${pathStr}${request.nextUrl.search}`;

  // Copia gli headers, rimuovendo quelli problematici
  const fwdHeaders = new Headers(request.headers);
  fwdHeaders.delete("host");
  fwdHeaders.delete("connection");
  fwdHeaders.delete("transfer-encoding");

  const init: RequestInit = {
    method: request.method,
    headers: fwdHeaders,
    redirect: "manual",
    // @ts-expect-error: 'duplex' è richiesto da node fetch per i body
    duplex: "half",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    init.body = await request.arrayBuffer();
  }

  let res: Response;
  try {
    res = await fetch(targetUrl, init);
  } catch (err) {
    return NextResponse.json(
      { detail: `Backend unreachable: ${err instanceof Error ? err.message : String(err)}` },
      { status: 502 }
    );
  }

  // Rinconfeziona la risposta preservando lo stream (per SSE)
  const respHeaders = new Headers(res.headers);
  // Lascia che Next.js gestisca encoding del body
  respHeaders.delete("transfer-encoding");
  respHeaders.delete("connection");

  return new NextResponse(res.body, {
    status: res.status,
    statusText: res.statusText,
    headers: respHeaders,
  });
}

export const GET = handler;
export const POST = handler;
export const PATCH = handler;
export const PUT = handler;
export const DELETE = handler;
export const OPTIONS = handler;
