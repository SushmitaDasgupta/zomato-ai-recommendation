import { NextRequest, NextResponse } from "next/server";
import fallbackFilters from "@/lib/catalog-filters.json";
import { proxyToApi } from "@/lib/api-proxy";

export const dynamic = "force-dynamic";
export const revalidate = 0;
export const runtime = "nodejs";

export async function GET(request: NextRequest) {
  const upstream = await proxyToApi(request, "/meta/filters");
  if (upstream.ok) {
    const headers = new Headers(upstream.headers);
    headers.set("cache-control", "no-store");
    return new Response(upstream.body, { status: 200, headers });
  }
  return NextResponse.json(fallbackFilters, {
    status: 200,
    headers: { "Cache-Control": "no-store" },
  });
}
