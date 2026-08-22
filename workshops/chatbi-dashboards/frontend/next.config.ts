import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Proxy /api/* to the backend so the browser only needs to reach the
  // frontend port. BACKEND_URL is resolved at server startup (runtime),
  // so it works both in docker (http://backend:8000) and dev (localhost:8000).
  async rewrites() {
    const backend = process.env.BACKEND_URL || "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${backend}/:path*` }];
  },
};

export default nextConfig;
