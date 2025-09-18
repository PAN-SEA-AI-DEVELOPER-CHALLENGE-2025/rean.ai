'use client';

import Link from 'next/link';
import { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import WaveDecoration from '@/components/WaveDecoration';

function LoginForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: 'testing99@gmail.com',
    password: 'testing99'
  });
  
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  
  const redirectTo = searchParams.get('redirect') || '/dashboard';

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: formData.email, password: formData.password }),
      });

      const data = await response.json();

      if (response.ok) {
        // Login successful
        console.log('Login successful:', data);
        
        // Use the auth context to store user data
        const token = data.token || data.access_token;
        if (token) {
          // Prefer user info returned by backend response
          let userInfo: { id: string; username: string; email: string; full_name: string; role: string };
          let decoded: any = {};

          try {
            const payload = token.split('.')[1];
            decoded = JSON.parse(atob(payload));
            console.log('Decoded JWT payload:', decoded);
          } catch (e) {
            console.warn('JWT decode failed, will rely on API user payload where possible');
          }

          // Use user from login response; if missing role, call /api/auth/me
          let apiUser = data?.user as any;
          if (!apiUser || !apiUser.role) {
            try {
              const meRes = await fetch('/api/auth/me', { headers: { Authorization: `Bearer ${token}` }, cache: 'no-store' });
              if (meRes.ok) {
                const me = await meRes.json();
                apiUser = me?.user || me; // support either { user: {...} } or direct object
              }
            } catch {}
          }
          userInfo = {
            id: String(apiUser?.id ?? decoded?.sub ?? '1'),
            username: apiUser?.username || decoded?.user_metadata?.username || decoded?.email || formData.email,
            email: apiUser?.email || decoded?.email || formData.email,
            full_name: apiUser?.full_name || decoded?.user_metadata?.full_name || 'User',
            // Critical fix: role should come from backend user if present; else support decoded.role; fallback to 'student'
            role: apiUser?.role || decoded?.user_metadata?.role || decoded?.role || 'student',
          };

          console.log('Using user info:', userInfo);
          login(token, userInfo);
          
          // Redirect to intended page or dashboard
          router.push(redirectTo);
        } else {
          setError('Invalid response from server');
        }

        // Redirect to dashboard
      } else {
        // Login failed
        setError(data.message || 'Login failed');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError('Network error. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <main className="min-h-screen bg-white text-slate-800 relative">
      {/* Content */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-6 py-14 md:py-20 grid lg:grid-cols-2 items-center gap-12">
          {/* Left copy */}
          <div className="max-lg:order-last">
            <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight tracking-tight">
              Welcome back to <span className="text-sky-700">rean.ai</span>
            </h1>
            <p className="mt-5 max-w-xl text-slate-600">
              Pick up where you left off — access your recordings, transcripts, summaries,
              quizzes, and flashcards across all your classes.
            </p>
          </div>

          {/* Form card */}
          <div className="w-full">
            <div className="mx-auto max-w-md rounded-2xl border border-slate-200 shadow-sm bg-white">
              <div className="px-6 py-7">
                <h2 className="text-xl font-bold">Sign in</h2>
                <p className="text-sm text-slate-500 mt-1">
                  Use your username and password to continue.
                </p>

                {error && (
                  <div className="mt-4 p-3 rounded-lg bg-red-50 border border-red-200">
                    <p className="text-sm text-red-600">{error}</p>
                  </div>
                )}

                <form
                  className="mt-6 grid gap-4"
                  onSubmit={handleSubmit}
                  noValidate
                >
                  <div className="grid gap-2">
                    <label htmlFor="email" className="text-sm font-medium">
                      Email
                    </label>
                    <input
                      id="email"
                      name="email"
                      type="email"
                      required
                      autoComplete="email"
                      placeholder="Enter your email"
                      value={formData.email}
                      onChange={handleInputChange}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                    />
                  </div>

                  <div className="grid gap-2">
                    <div className="flex items-center justify-between">
                      <label htmlFor="password" className="text-sm font-medium">
                        Password
                      </label>
                      <Link
                        href="#"
                        className="text-sm font-semibold text-sky-700 hover:underline"
                      >
                        Forgot?
                      </Link>
                    </div>
                    <input
                      id="password"
                      name="password"
                      type="password"
                      required
                      autoComplete="current-password"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={handleInputChange}
                      className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isLoading}
                    className="w-full rounded-lg bg-sky-600 px-4 py-2.5 font-semibold text-white hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isLoading ? 'Signing in...' : 'Sign in'}
                  </button>

                  <div className="relative my-2">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-slate-200" />
                    </div>
                    <div className="relative flex justify-center">
                      <span className="bg-white px-2 text-xs text-slate-500">or</span>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="rounded-lg border border-slate-300 bg-white px-4 py-2.5 font-semibold text-slate-700 hover:bg-slate-50"
                  >
                    Continue with Google
                  </button>
                </form>
              </div>
              <p className="text-center text-sm text-slate-600 mb-7">
                New here?{' '}
                <Link href="/auth/register" className="font-semibold text-sky-700 hover:underline">
                  Create an account
                </Link>
              </p>
            </div>

            <p className="mt-4 text-center text-sm text-slate-600">
              By continuing, you agree to our{' '}
              <Link href="#" className="font-semibold text-sky-700 hover:underline">
                Terms
              </Link>{' '}
              and{' '}
              <Link href="#" className="font-semibold text-sky-700 hover:underline">
                Privacy Policy
              </Link>
              .
            </p>
          </div>
        </div>
      </section>

      {/* Wave decoration at bottom of screen */}
      <WaveDecoration />
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm />
    </Suspense>
  );
}