import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy delle chiamate API verso FastAPI in localhost:8000 (interno al Repl).
  // Il browser parla solo con Next.js (porta 3000 esposta), niente CORS.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    ];
  },
  // Permette di servire l'app dietro reverse proxy (Replit)
  experimental: {
    serverActions: {
      bodySizeLimit: "10mb", // upload reference image
    },
  },
};

export default nextConfig;
