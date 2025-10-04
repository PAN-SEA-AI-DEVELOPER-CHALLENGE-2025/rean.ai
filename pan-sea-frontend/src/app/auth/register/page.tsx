"use client";

import { useState, useTransition } from "react";
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/hooks/useAuth';
import WaveDecoration from '@/components/WaveDecoration';

export default function RegisterPage() {
  const [pending, startTransition] = useTransition();
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const router = useRouter();
  const { login } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    full_name: '',
    role: '',
    phone_number: '',
    bio: '',
    password: '',
  });

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }));
  };

  const validateStep1 = () => {
    return formData.email && formData.username && formData.full_name && formData.role;
  };

  const nextStep = () => {
    if (validateStep1()) {
      setCurrentStep(2);
      setErr(null);
    } else {
      setErr("Please fill in all required fields in Step 1");
    }
  };

  const prevStep = () => {
    setCurrentStep(1);
    setErr(null);
  };

  async function submit() {
    setMsg(null); setErr(null);
    const payload = {
      email: formData.email,
      username: formData.username,
      full_name: formData.full_name,
      role: formData.role,
      phone_number: formData.phone_number,
      bio: formData.bio,
      password: formData.password,
    };

    const res = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      setErr(data?.message || `Failed: ${res.status}`);
      return;
    }

    const data = await res.json().catch(() => ({}));
    setMsg(`Registered as ${data?.username ?? payload.username}`);

    // If registration returns a token, store it. Otherwise, perform a login.
    let token: string | undefined = (data && (data.token || data.access_token)) as string | undefined;

    if (!token) {
      const loginRes = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ email: formData.email, password: formData.password }),
        cache: 'no-store',
      });
      const loginData = await loginRes.json().catch(() => ({}));
      if (loginRes.ok) {
        token = (loginData && (loginData.token || loginData.access_token)) as string | undefined;
      }
    }

    if (token) {
      // Prefer role from backend response if present
      let userInfo: { id: string; username: string; email: string; full_name: string; role: string };
      let decoded: any = {};
      try {
        const payloadPart = token.split('.')[1];
        decoded = JSON.parse(atob(payloadPart));
      } catch {}

      const apiUser = (data as any)?.user;
      userInfo = {
        id: String(apiUser?.id ?? decoded?.sub ?? '1'),
        username: apiUser?.username || decoded?.user_metadata?.username || decoded?.email || formData.username || formData.email,
        email: apiUser?.email || decoded?.email || formData.email,
        full_name: apiUser?.full_name || decoded?.user_metadata?.full_name || formData.full_name || 'User',
        role: apiUser?.role || decoded?.user_metadata?.role || decoded?.role || formData.role || 'student',
      };

      login(token, userInfo);
    }

    router.push('/dashboard');
  }

  return (
    <main className="min-h-screen bg-white text-slate-800 relative">
      {/* Content */}
      <section className="relative overflow-hidden">
        <div className="mx-auto max-w-7xl px-6 py-14 md:py-20 grid lg:grid-cols-2 items-center gap-12">
          {/* Left copy */}
          <div className="max-lg:order-last">
            <h1 className="text-4xl sm:text-5xl font-extrabold leading-tight tracking-tight">
              Join <span className="text-sky-700">rean.ai</span> today
            </h1>
            <p className="mt-5 max-w-xl text-slate-600">
              Start your journey with AI-powered learning tools. Record lectures, 
              generate transcripts, create summaries, and build custom quizzes and flashcards.
            </p>
          </div>

          {/* Form card */}
          <div className="w-full">
            <div className="mx-auto max-w-md rounded-2xl border border-slate-200 shadow-sm bg-white">
              <div className="px-6 py-7">
                {/* Progress indicator */}
                <div className="flex items-center justify-center mb-6">
                  <div className="flex items-center">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      currentStep >= 1 ? 'bg-sky-600 text-white' : 'bg-slate-200 text-slate-600'
                    }`}>
                      1
                    </div>
                    <div className={`w-16 h-1 mx-2 ${
                      currentStep > 1 ? 'bg-sky-600' : 'bg-slate-200'
                    }`} />
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      currentStep >= 2 ? 'bg-sky-600 text-white' : 'bg-slate-200 text-slate-600'
                    }`}>
                      2
                    </div>
                  </div>
                </div>

                <h2 className="text-xl font-bold">
                  {currentStep === 1 ? 'Basic Information' : 'Complete Your Profile'}
                </h2>
                <p className="text-sm text-slate-500 mt-1">
                  {currentStep === 1 
                    ? 'Fill in your basic details to get started.' 
                    : 'Add additional information and set your password.'}
                </p>

                {currentStep === 1 ? (
                  /* Step 1 Form */
                  <div className="mt-6 grid gap-4">
                    <div className="grid gap-2">
                      <label htmlFor="email" className="text-sm font-medium">
                        Email *
                      </label>
                      <input
                        id="email"
                        name="email"
                        type="email"
                        required
                        value={formData.email}
                        onChange={handleInputChange}
                        autoComplete="email"
                        placeholder="you@example.com"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>

                    <div className="grid gap-2">
                      <label htmlFor="username" className="text-sm font-medium">
                        Username *
                      </label>
                      <input
                        id="username"
                        name="username"
                        type="text"
                        required
                        value={formData.username}
                        onChange={handleInputChange}
                        autoComplete="username"
                        placeholder="johndoe"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>

                    <div className="grid gap-2">
                      <label htmlFor="full_name" className="text-sm font-medium">
                        Full Name *
                      </label>
                      <input
                        id="full_name"
                        name="full_name"
                        type="text"
                        required
                        value={formData.full_name}
                        onChange={handleInputChange}
                        autoComplete="name"
                        placeholder="John Doe"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>

                    <div className="grid gap-2">
                      <label htmlFor="role" className="text-sm font-medium">
                        Role *
                      </label>
                      <select
                        id="role"
                        name="role"
                        required
                        value={formData.role}
                        onChange={handleInputChange}
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                      >
                        <option value="">Select your role</option>
                        <option value="student">Student</option>
                        <option value="teacher">Teacher</option>
                      </select>
                    </div>

                    <button
                      type="button"
                      onClick={nextStep}
                      className="w-full rounded-lg bg-sky-600 px-4 py-2.5 font-semibold text-white shadow-sm hover:bg-sky-700"
                    >
                      Continue to Step 2
                    </button>
                  </div>
                ) : (
                  /* Step 2 Form */
                  <form
                    onSubmit={(e) => { e.preventDefault(); startTransition(() => submit()); }}
                    className="mt-6 grid gap-4"
                    noValidate
                  >
                    <div className="grid gap-2">
                      <label htmlFor="phone_number" className="text-sm font-medium">
                        Phone Number
                      </label>
                      <input
                        id="phone_number"
                        name="phone_number"
                        type="tel"
                        value={formData.phone_number}
                        onChange={handleInputChange}
                        autoComplete="tel"
                        placeholder="+1 (555) 000-0000"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>

                    <div className="grid gap-2">
                      <label htmlFor="bio" className="text-sm font-medium">
                        Bio
                      </label>
                      <textarea
                        id="bio"
                        name="bio"
                        rows={3}
                        value={formData.bio}
                        onChange={handleInputChange}
                        placeholder="Tell us a bit about yourself..."
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500 resize-none"
                      />
                    </div>

                    <div className="grid gap-2">
                      <label htmlFor="password" className="text-sm font-medium">
                        Password *
                      </label>
                      <input
                        id="password"
                        name="password"
                        type="password"
                        required
                        value={formData.password}
                        onChange={handleInputChange}
                        autoComplete="new-password"
                        placeholder="••••••••"
                        className="w-full rounded-lg border border-slate-300 px-3 py-2 outline-none focus:ring-2 focus:ring-sky-500"
                      />
                    </div>

                    <div className="flex gap-3">
                      <button
                        type="button"
                        onClick={prevStep}
                        className="flex-1 rounded-lg border border-slate-300 bg-white px-4 py-2.5 font-semibold text-slate-700 hover:bg-slate-50"
                      >
                        Back
                      </button>
                      <button
                        type="submit"
                        disabled={pending || !formData.password}
                        className="flex-1 rounded-lg bg-sky-600 px-4 py-2.5 font-semibold text-white shadow-sm hover:bg-sky-700 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {pending ? "Creating..." : "Create account"}
                      </button>
                    </div>

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
                )}

                {/* Error and success messages */}
                {err && (
                  <div className="mt-4 rounded-lg bg-red-50 border border-red-200 px-3 py-2">
                    <p className="text-sm text-red-600">{err}</p>
                  </div>
                )}

                {msg && (
                  <div className="mt-4 rounded-lg bg-green-50 border border-green-200 px-3 py-2">
                    <p className="text-sm text-green-600">{msg}</p>
                  </div>
                )}
              </div>
              <p className="text-center text-sm text-slate-600 mb-7">
                Already have an account?{' '}
                <Link href="/auth/login" className="font-semibold text-sky-700 hover:underline">
                  Sign in
                </Link>
              </p>
            </div>

            <p className="mt-4 text-center text-sm text-slate-600">
              By creating an account, you agree to our{' '}
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
