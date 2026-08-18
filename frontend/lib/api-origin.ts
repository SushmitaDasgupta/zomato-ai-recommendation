/**
 * Phase 2: Next proxies /api/* → {API_ORIGIN}/*.
 * Value is origin only (https://host, no path, no trailing slash).
 * Local default is FastAPI on :8000. Never put Groq keys here or on Vercel.
 */

const LOCAL_API_ORIGIN = "http://127.0.0.1:8000";
const LOCALHOST_ORIGIN = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i;

export function stripOrigin(raw: string): string {
  const trimmed = raw.trim();
  if (!trimmed) {
    return "";
  }
  try {
    const url = new URL(trimmed.includes("://") ? trimmed : `https://${trimmed}`);
    if (url.hostname.endsWith(".vercel.app") || url.hostname === "vercel.app") {
      return "";
    }
    return url.origin.replace(/\/+$/, "");
  } catch {
    return trimmed.replace(/\/+$/, "");
  }
}

export function isLocalhostOrigin(origin: string): boolean {
  return LOCALHOST_ORIGIN.test(origin);
}

export function isPublicHttpsOrigin(origin: string): boolean {
  if (!origin.toLowerCase().startsWith("https://") || isLocalhostOrigin(origin)) {
    return false;
  }
  try {
    const host = new URL(origin).hostname;
    return !host.endsWith(".vercel.app") && host !== "vercel.app";
  } catch {
    return false;
  }
}

export function resolveApiOrigin(env: NodeJS.Dict<string> = process.env): string {
  const raw = stripOrigin(env.API_ORIGIN ?? "");
  return raw || LOCAL_API_ORIGIN;
}
