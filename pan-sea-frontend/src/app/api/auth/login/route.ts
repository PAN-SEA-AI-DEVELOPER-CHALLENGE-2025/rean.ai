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
// In development, force localhost to avoid stale env overrides
const BASE =
  process.env.NODE_ENV !== "production"
    ? "http://localhost:8000/api/v1"
    : RAW.replace("0.0.0.0", "localhost").replace(/\/$/, "");

export async function POST(req: NextRequest) {
  try {
    // Expect JSON body { email, password }
    const { email, password } = await req.json();
    const loginData = { email: email || '', password: password || '' };

    console.log("Login request:", { email: loginData.email, hasPassword: !!loginData.password });
    console.log("API_URL_BASED RAW:", RAW);
    console.log("Normalized BASE:", BASE);
    console.log("Backend URL:", `${BASE}/auth/login`);

    if (!BASE) {
      console.error("API_URL_BASED environment variable is not set");
      return NextResponse.json({ message: "Backend configuration error" }, { status: 500 });
    }

    const upstream = await fetch(`${BASE}/auth/login`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        Accept: "application/json" 
      },
      body: JSON.stringify(loginData),
      cache: "no-store",
    });

    const ct = upstream.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const body = isJson ? await upstream.json().catch(() => ({})) : await upstream.text();

    console.log("Backend response status:", upstream.status);

    if (!upstream.ok) {
      const message =
        (isJson && body && typeof body === "object" && "detail" in body)
          ? (Array.isArray((body as ApiErrorResponse).detail)
              ? ((body as ApiErrorResponse).detail as ApiErrorDetail[]).map((d: ApiErrorDetail) => d.msg).join(", ")
              : (body as ApiErrorResponse).detail)
          : (typeof body === "string" ? body : `HTTP ${upstream.status}`);
      
      console.log("Login error:", message);
      return NextResponse.json({ message }, { status: upstream.status });
    }

    console.log("Login successful");
    // Attempt to read token from upstream response body
    const token = isJson && body && typeof body === 'object' && ('token' in body || 'access_token' in body)
      ? (body.token || body.access_token)
      : undefined;

    if (token && typeof token === 'string') {
      const res = isJson
        ? NextResponse.json(body, { status: upstream.status })
        : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "text/plain" } });
      // Set HttpOnly cookie used by middleware; JWT remains in cookie only
      const isProd = process.env.NODE_ENV === 'production';
      res.cookies.set('auth-token', token, {
        httpOnly: true,
        secure: isProd,
        sameSite: 'lax',
        path: '/',
        maxAge: 60 * 60 * 24, // 1 day
      });
      return res;
    }

    return isJson
      ? NextResponse.json(body, { status: upstream.status })
      : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "text/plain" } });
  } catch (err: unknown) {
    const error = err as Error;
    console.error("Login API error:", err);
    return NextResponse.json({ 
      message: error?.message || "Login request failed" 
    }, { status: 500 });
  }
}