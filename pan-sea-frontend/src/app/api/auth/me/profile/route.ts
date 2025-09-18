import { NextResponse, NextRequest } from "next/server";

const RAW = process.env.API_URL_BASED ?? "";
const BASE =
  process.env.NODE_ENV !== "production"
    ? "http://localhost:8000/api/v1"
    : RAW.replace("0.0.0.0", "localhost").replace(/\/$/, "");

export async function GET(req: NextRequest) {
  try {
    if (!BASE) {
      return NextResponse.json({ message: "Backend configuration error" }, { status: 500 });
    }

    let token = req.headers.get("authorization");
    if (!token) {
      const cookieToken = req.cookies.get("auth-token")?.value;
      if (cookieToken) token = `Bearer ${cookieToken}`;
    }

    const url = new URL(req.url);
    const limit = url.searchParams.get("limit") ?? "50";

    const upstream = await fetch(`${BASE}/users/me/profile?limit=${encodeURIComponent(limit)}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
        ...(token ? { Authorization: token } : {}),
      },
      cache: "no-store",
    });

    const ct = upstream.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const body = isJson ? await upstream.json().catch(() => ({})) : await upstream.text();

    if (!upstream.ok) {
      const message = typeof body === "string" ? body : (body as any)?.message || `HTTP ${upstream.status}`;
      return NextResponse.json({ message }, { status: upstream.status });
    }

    return isJson
      ? NextResponse.json(body, { status: upstream.status })
      : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "application/json" } });
  } catch (err: unknown) {
    const error = err as Error;
    return NextResponse.json({ message: error?.message || "Failed to fetch profile" }, { status: 500 });
  }
}


