import type { NextConfig } from "next";

// Replit serve l'app dietro un proxy iframe su un dominio diverso: il dev
// server di Next va autorizzato a ricevere richieste cross-origin per /_next/*.
const allowedDevOrigins = [
  process.env.REPLIT_DEV_DOMAIN,
  process.env.REPLIT_DOMAINS?.split(",")[0],
].filter((d): d is string => Boolean(d));

const nextConfig: NextConfig = {
  ...(allowedDevOrigins.length > 0 ? { allowedDevOrigins } : {}),
  // NB: il proxy /api/* → FastAPI è gestito da web/app/api/[...path]/route.ts
  // (API route catch-all). I `rewrites()` con destination esterna su Replit
  // si comportano in modo inconsistente — l'API route esplicita è 100%
  // deterministica e gestisce anche streaming (SSE) + Set-Cookie.
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb",
    },
  },
};

export default nextConfig;
