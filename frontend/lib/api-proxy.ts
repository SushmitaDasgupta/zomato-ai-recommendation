import { NextRequest, NextResponse } from "next/server";
import { isPublicHttpsOrigin, resolveApiOrigin } from "@/lib/api-origin";

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
    "cookie",
    "authorization",
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

export function missingApiOriginResponse(): NextResponse {
  return NextResponse.json(
    {
      detail:
        "API_ORIGIN must be the Railway HTTPS origin (https://<service>.up.railway.app), not the Vercel URL.",
    },
    { status: 503, headers: { "Cache-Control": "no-store" } },
  );
}

export async function proxyToApi(request: NextRequest, apiPath: string): Promise<Response> {
  const origin = resolveApiOrigin();
  const onVercel = process.env.VERCEL === "1";
  if (onVercel && !isPublicHttpsOrigin(origin)) {
    return missingApiOriginResponse();
  }

  const url = new URL(apiPath.replace(/^\/+/, ""), `${origin}/`);
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

  try {
    const upstream = await fetch(url, init);
    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: forwardResponseHeaders(upstream.headers),
    });
  } catch {
    return NextResponse.json(
      { detail: `Could not reach the recommendation API at ${origin}.` },
      { status: 502, headers: { "Cache-Control": "no-store" } },
    );
  }
}
