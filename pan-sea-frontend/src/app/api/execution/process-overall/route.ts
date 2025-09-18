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

export async function POST(req: NextRequest) {
  try {
    const formData = await req.formData();

    const file = formData.get("file");
    const classId = formData.get("class_id");
    const lectureTitle = formData.get("lecture_title");
    const language = formData.get("language");
    const subject = formData.get("subject");

    if (!file || !(file instanceof File)) {
      return NextResponse.json({ message: "File is required" }, { status: 400 });
    }

    if (!classId || typeof classId !== "string") {
      return NextResponse.json({ message: "class_id is required" }, { status: 400 });
    }

    if (!lectureTitle || typeof lectureTitle !== "string") {
      return NextResponse.json({ message: "lecture_title is required" }, { status: 400 });
    }

    if (!language || typeof language !== "string") {
      return NextResponse.json({ message: "language is required" }, { status: 400 });
    }

    if (!subject || typeof subject !== "string") {
      return NextResponse.json({ message: "subject is required" }, { status: 400 });
    }

    if (!BASE) {
      return NextResponse.json({ message: "Backend configuration error" }, { status: 500 });
    }

    const upstreamForm = new FormData();
    upstreamForm.append("file", file);
    upstreamForm.append("class_id", classId);
    upstreamForm.append("lecture_title", lectureTitle);
    upstreamForm.append("language", language);
    upstreamForm.append("subject", subject);

    const upstream = await fetch(`${BASE}/execution/process-overall`, {
      method: "POST",
      headers: {
        Accept: "application/json",
        ...(req.headers.get("authorization") && {
          Authorization: req.headers.get("authorization")!,
        }),
      },
      body: upstreamForm,
      cache: "no-store",
    });

    const ct = upstream.headers.get("content-type") || "";
    const isJson = ct.includes("application/json");
    const body = isJson ? await upstream.json().catch(() => ({})) : await upstream.text();

    if (!upstream.ok) {
      let message =
        (isJson && body && typeof body === "object" && "detail" in body)
          ? (Array.isArray((body as ApiErrorResponse).detail)
              ? ((body as ApiErrorResponse).detail as ApiErrorDetail[]).map((d: ApiErrorDetail) => d.msg).join(", ")
              : (body as ApiErrorResponse).detail)
          : (typeof body === "string" ? body : "");

      // Fallbacks to ensure we always return something actionable
      if (!message || String(message).trim().length === 0) {
        message = `HTTP ${upstream.status}`;
      }

      return NextResponse.json({ message, status: upstream.status, raw: isJson ? body : String(body) }, { status: upstream.status });
    }

    return isJson
      ? NextResponse.json(body, { status: upstream.status })
      : new NextResponse(body as string, { status: upstream.status, headers: { "content-type": ct || "application/json" } });
  } catch (err: unknown) {
    const error = err as Error;
    return NextResponse.json({ message: error?.message || "Failed to process upload" }, { status: 500 });
  }
}


