import type { NextConfig } from "next";

const nextConfig: NextConfig = {
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
