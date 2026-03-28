import type { NextConfig } from "next";

// In production (Railway), set API_URL to the FastAPI service's public URL,
// e.g. https://rowboat-api.up.railway.app
// In local dev this falls back to the local API server.
// Strip trailing slash to avoid double-slash in rewrite destination.
const API_URL = (process.env.API_URL || "http://127.0.0.1:8000").replace(/\/+$/, "");

function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}

const nextConfig: NextConfig = {
  async rewrites() {
    if (!isValidUrl(API_URL)) {
      console.warn(
        `[next.config] API_URL "${API_URL}" is not a valid URL — /api/* rewrites disabled. ` +
        `Set API_URL to the backend's public Railway URL.`
      );
      return [];
    }
    return [
      {
        source: "/api/:path*",
        destination: `${API_URL}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
