import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  // Protect dashboard via matcher below. Trust only presence of HttpOnly cookie.
  const hasCookie = Boolean(request.cookies.get('auth-token')?.value);
  if (!hasCookie) {
    const loginUrl = new URL('/auth/login', request.url);
    const redirectTo = pathname + (search || '');
    loginUrl.searchParams.set('redirect', redirectTo);
    const response = NextResponse.redirect(loginUrl);
    // Clear any stray cookie value
    response.cookies.set('auth-token', '', { path: '/', expires: new Date(0) });
    return response;
  }

  return NextResponse.next();
}

export const config = {
  // Protect only dashboard routes
  matcher: ['/dashboard/:path*'],
};
