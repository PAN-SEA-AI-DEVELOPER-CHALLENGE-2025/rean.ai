import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

interface ApiErrorDetail {
  msg: string;
  type: string;
}

interface ApiErrorResponse {
  detail: string | ApiErrorDetail[];
}

const RAW = process.env.API_URL_BASED ?? "";
const BASE =
  process.env.NODE_ENV !== "production"
    ? "http://localhost:8000/api/v1"
    : RAW.replace("0.0.0.0", "localhost").replace(/\/$/, "");

export async function GET(
  req: NextRequest,
  { params }: { params: Promise<{ teacherId: string }> }
) {
  try {
    const { teacherId } = await params;
    const { searchParams } = new URL(req.url);
    const limit = searchParams.get('limit') || '50';

    console.log("Fetching classes for teacher:", teacherId, "with limit:", limit);
    console.log("Backend URL:", `${BASE}/classes/teacher/${teacherId}`);

    if (!BASE) {
      console.error("API_URL_BASED environment variable is not set");
      return NextResponse.json({ message: "Backend configuration error" }, { status: 500 });
    }

    const upstream = await fetch(`${BASE}/classes/teacher/${teacherId}?limit=${limit}`, {
      method: "GET",
      headers: { 
        Accept: "application/json",
        // Forward authorization header if present
        ...(req.headers.get('authorization') && {
          'Authorization': req.headers.get('authorization')!
        })
      },
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
      
      console.log("Classes API error:", message);
      return NextResponse.json({ message }, { status: upstream.status });
    }

    console.log("Classes fetched successfully");
    return isJson
      ? NextResponse.json(body, { status: upstream.status })
      : new NextResponse(body as string, { 
          status: upstream.status, 
          headers: { "content-type": ct || "application/json" }
        });
  } catch (err: unknown) {
    const error = err as Error;
    console.error("Classes API error:", err);
    return NextResponse.json({ 
      message: error?.message || "Failed to fetch classes" 
    }, { status: 500 });
  }
}
