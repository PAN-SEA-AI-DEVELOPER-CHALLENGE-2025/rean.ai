import { NextRequest, NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

interface ApiErrorDetail { msg: string; type?: string }
interface ApiErrorResponse { detail?: string | ApiErrorDetail[]; message?: string }

const RAW_RAG = (process.env.RAG_API_URL_BASED ?? process.env.API_URL_BASED ?? '').replace(/\/$/, '');
const BASE = RAW_RAG.replace('0.0.0.0', 'localhost');

export async function POST(req: NextRequest, { params }: { params: Promise<{ lessonId: string }> }) {
  try {
    const { lessonId } = await params;
    const body = await req.json().catch(() => ({}));
    const { question, top_k } = body || {};
    const topK = typeof top_k === 'number' ? top_k : 8;

    console.log(`RAG API Route - Lesson ID: ${lessonId}, Question: ${question}, top_k: ${top_k}`);

    if (!question || typeof question !== 'string') {
      return NextResponse.json({ message: 'question is required' }, { status: 400 });
    }

    if (!BASE) {
      console.error('RAG API configuration error - BASE URL not set:', {
        RAW_RAG,
        BASE,
        RAG_API_URL_BASED: process.env.RAG_API_URL_BASED,
        API_URL_BASED: process.env.API_URL_BASED
      });
      return NextResponse.json({ 
        message: 'Backend configuration error - RAG API URL not configured',
        debug: {
          RAG_API_URL_BASED: process.env.RAG_API_URL_BASED,
          API_URL_BASED: process.env.API_URL_BASED
        }
      }, { status: 500 });
    }

    const targetUrl = `${BASE}/rag/lessons/${lessonId}/ask`;
    console.log(`Making request to RAG API: ${targetUrl}`);

    // Prefer Authorization header from the incoming request; fallback to auth-token cookie
    const incomingAuth = req.headers.get('authorization');
    const cookieToken = req.cookies.get('auth-token')?.value;
    const authHeader = incomingAuth || (cookieToken ? `Bearer ${cookieToken}` : undefined);

    const upstream = await fetch(targetUrl, {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'Content-Type': 'application/json',
        ...(authHeader && { Authorization: authHeader }),
      },
      body: JSON.stringify({ question, top_k: topK }),
      cache: 'no-store',
    });

    console.log(`RAG API Response Status: ${upstream.status}`);

    const ct = upstream.headers.get('content-type') || '';
    const isJson = ct.includes('application/json');
    const respBody = isJson ? await upstream.json().catch(() => ({})) : await upstream.text();

    if (!upstream.ok) {
      console.error('RAG API Error:', {
        status: upstream.status,
        body: respBody,
        url: targetUrl
      });
      
      const message =
        (isJson && respBody && typeof respBody === 'object' && 'detail' in respBody)
          ? (Array.isArray((respBody as ApiErrorResponse).detail)
              ? ((respBody as ApiErrorResponse).detail as ApiErrorDetail[]).map((d) => d.msg).join(', ')
              : (respBody as ApiErrorResponse).detail)
          : (typeof respBody === 'string' ? respBody : `HTTP ${upstream.status}`);
      return NextResponse.json({ message, debug: { targetUrl, status: upstream.status } }, { status: upstream.status });
    }

    console.log('RAG API Success:', { responseType: isJson ? 'json' : 'text' });
    
    return isJson
      ? NextResponse.json(respBody, { status: upstream.status })
      : new NextResponse(respBody as string, { status: upstream.status, headers: { 'content-type': ct || 'application/json' } });
  } catch (err: unknown) {
    const error = err as Error;
    console.error('RAG API Route Error:', error);
    return NextResponse.json({ 
      message: error?.message || 'Failed to ask RAG',
      error: error?.name,
      stack: error?.stack
    }, { status: 500 });
  }
}


