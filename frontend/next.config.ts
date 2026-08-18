import type { NextConfig } from "next";
import { resolveApiOrigin } from "./lib/api-origin";

const API_ORIGIN = resolveApiOrigin();

console.info("[tablepick] proxy /api/* → %s/*", API_ORIGIN);

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${API_ORIGIN}/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/api/:path*",
        headers: [{ key: "Cache-Control", value: "no-store" }],
      },
    ];
  },
};

export default nextConfig;
