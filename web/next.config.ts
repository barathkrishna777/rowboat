import type { NextConfig } from "next";

// In production (Railway), set API_URL to the FastAPI service's public URL,
// e.g. https://rowboat-api.up.railway.app
// In local dev this falls back to the local API server.
const API_URL = process.env.API_URL || "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
