"use client";

import { useEffect, useState } from "react";
import { fetchMyProfile } from "@/services/auth";
import { ProfileResponse } from "@/types/api";
import Link from "next/link";
import { useAuth } from "@/hooks/useAuth";

export default function ProfilePage() {
  const [data, setData] = useState<ProfileResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const { logout } = useAuth();

  useEffect(() => {
    let mounted = true;
    (async () => {
      try {
        setIsLoading(true);
        const res = await fetchMyProfile(50);
        if (!mounted) return;
        setData(res);
      } catch (err: any) {
        if (!mounted) return;
        setError(err?.message || "Failed to load profile");
      } finally {
        if (mounted) setIsLoading(false);
      }
    })();
    return () => {
      mounted = false;
    };
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-600">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-sky-600 border-t-transparent" />
          Loading profile…
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-700">
          {error}
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-slate-600">No profile data.</p>
      </div>
    );
  }

  const { user, classes } = data;
  const totalClasses = classes?.length ?? 0;
  const totalStudents = (classes || []).reduce((sum, c) => sum + (c.students?.length ?? 0), 0);
  const totalDurationMinutes = (classes || []).reduce((sum, c) => sum + (c.duration ?? 0), 0);
  const totalDurationHours = Math.round((totalDurationMinutes / 60) * 10) / 10;

  return (
    <section className="mx-auto max-w-6xl px-6 py-10">
      <nav className="mb-6 text-sm text-slate-500">
        <Link href="/dashboard" className="inline-flex items-center gap-1 hover:text-slate-700">
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          Back
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">Profile</span>
      </nav>

      {/* Header */}
      <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-tr from-sky-50 via-white to-indigo-50 p-6">
        <div className="pointer-events-none absolute right-[-40px] top-[-40px] h-40 w-40 rounded-full bg-sky-200/30 blur-2xl" />
        <div className="flex flex-col items-start gap-6 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-sky-600/10 text-sky-700 ring-1 ring-sky-200 font-semibold">
              {user.full_name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div>
              <h1 className="text-lg font-semibold text-slate-900">{user.full_name || 'Unnamed User'}</h1>
              <p className="text-sm text-slate-600">{user.email}</p>
              <div className="mt-2 inline-flex items-center gap-2 rounded-full bg-white/80 px-3 py-1 text-xs font-medium text-slate-700 ring-1 ring-slate-200 backdrop-blur">
                <span className="inline-flex h-2 w-2 rounded-full bg-sky-500" />
                {user.role}
              </div>
            </div>
          </div>
          <div className="flex gap-2">
            <Link href="/dashboard" className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-sm font-medium text-white shadow-sm hover:bg-slate-800">
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 12l2-2 4 4 8-8 4 4"/></svg>
              Go to Dashboard
            </Link>
            <button
              onClick={logout}
              className="inline-flex items-center gap-2 rounded-lg border border-rose-200 px-3 py-2 text-sm font-medium text-rose-700 hover:bg-rose-50"
              aria-label="Logout"
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                <polyline points="16 17 21 12 16 7" />
                <line x1="21" y1="12" x2="9" y2="12" />
              </svg>
              Logout
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
            <div className="text-xs text-slate-500">Total Classes</div>
            <div className="mt-1 flex items-baseline gap-2">
              <div className="text-xl font-semibold text-slate-900">{totalClasses}</div>
              <span className="text-xs text-slate-500">classes</span>
            </div>
          </div>
          <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
            <div className="text-xs text-slate-500">Total Students</div>
            <div className="mt-1 flex items-baseline gap-2">
              <div className="text-xl font-semibold text-slate-900">{totalStudents}</div>
              <span className="text-xs text-slate-500">enrolled</span>
            </div>
          </div>
          <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200">
            <div className="text-xs text-slate-500">Total Duration</div>
            <div className="mt-1 flex items-baseline gap-2">
              <div className="text-xl font-semibold text-slate-900">{isFinite(totalDurationHours) ? totalDurationHours : 0}</div>
              <span className="text-xs text-slate-500">hours</span>
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="mt-8 grid gap-6 lg:grid-cols-3">
        {/* Account details */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 lg:col-span-1">
          <h2 className="text-sm font-semibold text-slate-900">Account</h2>
          <div className="mt-4 space-y-4">
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs text-slate-500">Full name</div>
                <div className="text-sm font-medium text-slate-900">{user.full_name || '—'}</div>
              </div>
            </div>
            <div className="h-px bg-slate-100" />
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs text-slate-500">Email</div>
                <div className="text-sm font-medium text-slate-900">{user.email}</div>
              </div>
            </div>
            <div className="h-px bg-slate-100" />
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="text-xs text-slate-500">Role</div>
                <div className="text-sm font-medium text-slate-900 capitalize">{user.role}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Classes list */}
        <div className="rounded-2xl border border-slate-200 bg-white p-6 lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-900">My Classes</h2>
            <span className="text-xs text-slate-500">{classes?.length || 0} total</span>
          </div>
          {(!classes || classes.length === 0) ? (
            <div className="flex items-center justify-between rounded-xl border border-dashed border-slate-200 p-6 text-sm text-slate-600">
              <span>No classes yet.</span>
              <Link href="/dashboard" className="inline-flex items-center gap-2 rounded-lg bg-slate-900 px-3 py-2 text-xs font-medium text-white shadow-sm hover:bg-slate-800">
                Go to Dashboard
              </Link>
            </div>
          ) : (
            <div className="overflow-hidden rounded-xl border border-slate-200">
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50/60">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Class</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Grade</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Teacher</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Created</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600">Students</th>
                      <th className="px-4 py-3" />
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {classes.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-3 text-sm text-slate-800">
                          <div className="flex items-center gap-3">
                            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-sky-50 text-sky-700 ring-1 ring-sky-100 text-xs font-semibold">
                              {c.subject?.[0]?.toUpperCase() || 'C'}
                            </span>
                            <div className="min-w-0">
                              <div className="truncate font-medium text-slate-900">{c.subject}</div>
                              <div className="text-xs text-slate-500">Code: {c.class_code}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-xs text-slate-600">{c.grade || '—'}</td>
                        <td className="px-4 py-3 text-xs text-slate-600">{c.teacher_name || '—'}</td>
                        <td className="px-4 py-3 text-xs text-slate-600">{new Date(c.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
                        <td className="px-4 py-3 text-right text-xs text-slate-700">{c.students?.length ?? 0}</td>
                        <td className="px-4 py-3 text-right">
                          <Link href={`/dashboard/class_detail/${c.id}`} className="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50">
                            View
                            <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18l6-6-6-6"/></svg>
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


