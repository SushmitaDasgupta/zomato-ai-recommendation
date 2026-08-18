/**
 * Phase 2: Next rewrites /api/* → {API_ORIGIN}/*. Vercel bakes this at build.
 * Local default is FastAPI on :8000. Never put Groq keys in this file or Vercel.
 */

const LOCAL_API_ORIGIN = "http://127.0.0.1:8000";
const LOCALHOST_ORIGIN = /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i;

export function resolveApiOrigin(env: NodeJS.Dict<string> = process.env): string {
  const raw = (env.API_ORIGIN ?? "").trim().replace(/\/+$/, "");
  const onVercel = env.VERCEL === "1";

  if (onVercel) {
    if (!raw) {
      throw new Error(
        "API_ORIGIN must be set at build time on Vercel (Phase 1 Railway HTTPS origin, no trailing slash).",
      );
    }
    if (LOCALHOST_ORIGIN.test(raw)) {
      throw new Error(
        "API_ORIGIN on Vercel must be the public Railway HTTPS origin, not localhost.",
      );
    }
    if (!raw.toLowerCase().startsWith("https://")) {
      throw new Error("API_ORIGIN on Vercel must be an https origin with no trailing slash.");
    }
    return raw;
  }

  return raw || LOCAL_API_ORIGIN;
}
