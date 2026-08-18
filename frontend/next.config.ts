import type { NextConfig } from "next";
import { isPublicHttpsOrigin, resolveApiOrigin } from "./lib/api-origin";

const API_ORIGIN = resolveApiOrigin();
const bakeRewrite = isPublicHttpsOrigin(API_ORIGIN);

console.info(
  "[tablepick] proxy /api/* → %s/* (%s)",
  API_ORIGIN,
  bakeRewrite ? "next.config rewrite" : "runtime /api route",
);

const nextConfig: NextConfig = {
  async rewrites() {
    if (!bakeRewrite) {
      return [];
    }
    // beforeFiles beats app/api/[...path] so Vercel can reverse-proxy (no 10s Hobby cap).
    return {
      beforeFiles: [
        {
          source: "/api/:path*",
          destination: `${API_ORIGIN}/:path*`,
        },
      ],
    };
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
