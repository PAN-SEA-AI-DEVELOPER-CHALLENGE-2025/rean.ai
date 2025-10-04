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
const BASE =
  process.env.NODE_ENV !== "production"
    ? "http://localhost:8000/api/v1"
    : RAW.replace("0.0.0.0", "localhost").replace(/\/$/, "");

// Decode a JWT payload (Node/Edge safe)
function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const base64 = parts[1].replace(/-/g, '+').replace(/_/g, '/')
    const padded = base64.padEnd(base64.length + (4 - (base64.length % 4 || 4)) % 4, '=')
    const binary = Buffer.from(padded, 'base64')
    const json = binary.toString('utf8')
    return JSON.parse(json) as Record<string, unknown>
  } catch {
    return null
  }
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    
    console.log("Creating new class:", body);
    console.log("Backend URL:", `${BASE}/classes/`);

    if (!BASE) {
      console.error("API_URL_BASED environment variable is not set");
      return NextResponse.json({ message: "Backend configuration error" }, { status: 500 });
    }

    // RBAC: prevent students from creating classes
    const authHeader = req.headers.get('authorization') || '';
    const bearer = authHeader.toLowerCase().startsWith('bearer ')
      ? authHeader.slice(7).trim()
      : undefined;
    const cookieToken = req.cookies.get('auth-token')?.value;
    const token = bearer || cookieToken;

    if (token) {
      const payload = decodeJwtPayload(token);
      const role = (payload?.role || (payload as any)?.user_role || (payload as any)?.claims?.role) as string | undefined;
      if (role && role.toLowerCase() === 'student') {
        return NextResponse.json({ message: 'Students are not allowed to create classes' }, { status: 403 });
      }
    }

    const upstream = await fetch(`${BASE}/classes/`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        Accept: "application/json",
        // Forward authorization header if present
        ...(req.headers.get('authorization') && {
          'Authorization': req.headers.get('authorization')!
        })
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const ct = upstream.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const responseData = isJson ? await upstream.json().catch(() => ({})) : await upstream.text();

    console.log("Backend response status:", upstream.status);
    console.log("Backend response:", responseData);

    if (!upstream.ok) {
      const message =
        (isJson && responseData && typeof responseData === "object" && "detail" in responseData)
          ? (Array.isArray((responseData as ApiErrorResponse).detail)
              ? ((responseData as ApiErrorResponse).detail as ApiErrorDetail[]).map((d: ApiErrorDetail) => d.msg).join(", ")
              : (responseData as ApiErrorResponse).detail)
          : (typeof responseData === "string" ? responseData : `HTTP ${upstream.status}`);
      
      console.log("Create class API error:", message);
      return NextResponse.json({ message }, { status: upstream.status });
    }

    console.log("Class created successfully");
    return isJson
      ? NextResponse.json(responseData, { status: upstream.status })
      : new NextResponse(responseData as string, { 
          status: upstream.status, 
          headers: { "content-type": ct || "application/json" }
        });
  } catch (err: unknown) {
    const error = err as Error;
    console.error("Create class API error:", err);
    return NextResponse.json({ 
      message: error?.message || "Failed to create class" 
    }, { status: 500 });
  }
}
