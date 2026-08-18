/**
 * Phase 2: Next proxies /api/* → {API_ORIGIN}/*.
 * Prefer a public HTTPS origin (Railway). Local default is FastAPI on :8000.
 * Never put Groq keys in this file or on Vercel.
 */

const LOCAL_API_ORIGIN = "http://127.0.0.1:8000";
const LOCALHOST_ORIGIN = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i;

export function stripOrigin(raw: string): string {
  return raw.trim().replace(/\/+$/, "");
}

export function isLocalhostOrigin(origin: string): boolean {
  return LOCALHOST_ORIGIN.test(origin);
}

export function isPublicHttpsOrigin(origin: string): boolean {
  return origin.toLowerCase().startsWith("https://") && !isLocalhostOrigin(origin);
}

export function resolveApiOrigin(env: NodeJS.Dict<string> = process.env): string {
  const raw = stripOrigin(env.API_ORIGIN ?? "");
  return raw || LOCAL_API_ORIGIN;
}
