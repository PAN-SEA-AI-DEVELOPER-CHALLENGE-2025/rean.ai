// src/app/api/auth/register/route.ts
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

// Type definitions for API error responses
interface ApiErrorDetail {
  msg: string;
  type?: string;
}

interface ApiErrorResponse {
  detail?: string | ApiErrorDetail[];
  message?: string;
}

const RAW = process.env.API_URL_BASED ?? "";
// Mirror login route behavior: in development, always use localhost v1 to avoid env drift
const BASE =
  process.env.NODE_ENV !== "production"
    ? "http://localhost:8000/api/v1"
    : RAW.replace("0.0.0.0", "localhost").replace(/\/$/, "");

// Debug logging
if (!RAW) {
  console.error("API_URL_BASED environment variable is not set");
}
console.log("Normalized BASE:", BASE);

export async function POST(req: NextRequest) {
  try {
    if (!BASE) {
      return NextResponse.json(
        { message: "Backend API URL is not configured" },
        { status: 500 }
      );
    }

    const json = await req.json();

    const upstream = await fetch(`${BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(json),
      cache: "no-store",
    });

    console.log("Upstream response status:", upstream.status);
    console.log("Upstream response headers:", Object.fromEntries(upstream.headers.entries()));

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

    // If backend returns token on register, set HttpOnly cookie like login
    const token = isJson && body && typeof body === 'object' && ('token' in body || 'access_token' in body)
      ? (body.token || body.access_token)
      : undefined;

    if (token && typeof token === 'string') {
      const res = isJson
        ? NextResponse.json(body, { status: upstream.status })
        : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "text/plain" } });
      const isProd = process.env.NODE_ENV === 'production';
      res.cookies.set('auth-token', token, {
        httpOnly: true,
        secure: isProd,
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24,
      });
      return res;
    }

    return isJson
      ? NextResponse.json(body, { status: upstream.status })
      : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "text/plain" }});
  } catch (err: unknown) {
    const error = err as Error;
    console.error("API route error:", err);
    
    // Handle fetch errors (network issues, etc.)
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      return NextResponse.json(
        { message: "Unable to connect to backend server. Please check if the backend is running." },
        { status: 503 }
      );
    }
    
    return NextResponse.json(
      { message: error?.message || "Invalid request" },
      { status: 400 }
    );
  }
}
