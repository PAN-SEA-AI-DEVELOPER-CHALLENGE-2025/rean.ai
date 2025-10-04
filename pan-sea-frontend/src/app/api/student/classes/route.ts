import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface ApiErrorDetail {
  msg: string;
  type?: string;
}

interface ApiErrorResponse {
  detail?: string | ApiErrorDetail[];
  message?: string;
}

const RAW = process.env.API_URL_BASED ?? "";
const BASE =
  process.env.NODE_ENV !== "production"
    ? "http://localhost:8000/api/v1"
    : RAW.replace("0.0.0.0", "localhost").replace(/\/$/, "");

export async function GET(req: NextRequest) {
  try {
    const url = new URL(req.url);
    const limit = url.searchParams.get('limit') || '50';
    const offset = url.searchParams.get('offset') || '0';

    if (!BASE) {
      return NextResponse.json({ message: "Backend configuration error" }, { status: 500 });
    }

    const upstream = await fetch(`${BASE}/student/classes?limit=${encodeURIComponent(limit)}&offset=${encodeURIComponent(offset)}` , {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(req.headers.get('authorization') && {
          'Authorization': req.headers.get('authorization')!,
        })
      },
      cache: "no-store",
    });

    const ct = upstream.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const body = isJson ? await upstream.json().catch(() => ({})) : await upstream.text();

    if (!upstream.ok) {
      const message =
        (isJson && body && typeof body === "object" && "detail" in body)
          ? (Array.isArray((body as ApiErrorResponse).detail)
              ? ((body as ApiErrorResponse).detail as ApiErrorDetail[]).map((d: ApiErrorDetail) => d.msg).join(", ")
              : (body as ApiErrorResponse).detail)
          : (typeof body === "string" ? body : `HTTP ${upstream.status}`);
      return NextResponse.json({ message }, { status: upstream.status });
    }

    return isJson
      ? NextResponse.json(body, { status: upstream.status })
      : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "application/json" }});
  } catch (err: unknown) {
    const error = err as Error;
    return NextResponse.json({ message: error?.message || "Failed to fetch student classes" }, { status: 500 });
  }
}


