import { NextRequest, NextResponse } from "next/server";
import { isPublicHttpsOrigin, resolveApiOrigin } from "@/lib/api-origin";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

type RouteContext = { params: Promise<{ path: string[] }> };

function hopByHop(name: string): boolean {
  return [
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
    "host",
    "content-length",
  ].includes(name.toLowerCase());
}

function forwardRequestHeaders(source: Headers): Headers {
  const headers = new Headers();
  source.forEach((value, key) => {
    if (!hopByHop(key) && key.toLowerCase() !== "accept-encoding") {
      headers.set(key, value);
    }
  });
  return headers;
}

function forwardResponseHeaders(source: Headers): Headers {
  const headers = new Headers();
  source.forEach((value, key) => {
    if (!hopByHop(key) && key.toLowerCase() !== "content-encoding") {
      headers.set(key, value);
    }
  });
  headers.set("cache-control", "no-store");
  return headers;
}

async function proxy(request: NextRequest, path: string[]): Promise<Response> {
  const origin = resolveApiOrigin();
  const onVercel = process.env.VERCEL === "1";
  if (onVercel && !isPublicHttpsOrigin(origin)) {
    return NextResponse.json(
      {
        detail:
          "API_ORIGIN must be set on Vercel (Phase 1 Railway HTTPS origin, no trailing slash).",
      },
      { status: 503 },
    );
  }

  const suffix = path.join("/");
  const url = new URL(`${origin}/${suffix}`);
  url.search = request.nextUrl.search;

  const method = request.method.toUpperCase();
  const init: RequestInit = {
    method,
    headers: forwardRequestHeaders(request.headers),
    cache: "no-store",
    redirect: "manual",
  };
  if (method !== "GET" && method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  let upstream: Response;
  try {
    upstream = await fetch(url, init);
  } catch {
    return NextResponse.json(
      { detail: `Could not reach the recommendation API at ${origin}.` },
      { status: 502 },
    );
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: forwardResponseHeaders(upstream.headers),
  });
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, (await context.params).path ?? []);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, (await context.params).path ?? []);
}

export async function OPTIONS(request: NextRequest, context: RouteContext) {
  return proxy(request, (await context.params).path ?? []);
}
