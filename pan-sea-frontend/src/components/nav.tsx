'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import Image from 'next/image';
import { useAuth } from '@/hooks/useAuth';

const NAV_BASE = [
  { label: 'Home', href: '/' },
  { label: 'Use Guides', href: '/user-guide' },
  { label: 'Pricing', href: '/price' },
];

export default function NavBar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const { token, user } = useAuth();

  const NAV = [
    ...NAV_BASE,
    token ? { label: 'Dashboard', href: '/dashboard' } : { label: 'Login', href: '/auth/login' },
  ];

  const isActive = (href?: string) =>
    href && (pathname === href || pathname.startsWith(href + '/'));

  return (
    <header className="sticky top-0 z-40 w-full bg-white/80 border-b border-blue-100">
      <nav className="mx-auto max-w-6xl px-4 flex h-16 items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center space-x-2 focus:outline-none">
          <Image src="/logo.png" alt="Rean.ai logo" width={36} height={36} className="rounded" />
          <span className="hidden sm:block font-bold text-slate-900"><span className="text-blue-700">Rean</span>.ai</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-1">
          {NAV.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className={`px-3 py-2 rounded-md focus:outline-none ${isActive(item.href) ? 'bg-blue-50 text-blue-700 ring-1 ring-blue-100' : 'text-slate-700 hover:text-blue-700 hover:bg-blue-50'}`}
            >
              {item.label}
            </Link>
          ))}
          {token && (
            <Link
              href="/auth/profile"
              aria-label="Profile"
              className="ml-1 inline-flex h-9 w-9 items-center justify-center rounded-full border border-blue-200 bg-white text-blue-700 hover:bg-blue-50 focus:outline-none"
              title="Profile"
            >
              {(user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase()) ? (
                <span className="text-sm font-semibold">
                  {user?.full_name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase()}
                </span>
              ) : (
                <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
              )}
            </Link>
          )}
        </div>

        {/* Mobile hamburger */}
        <button
          className="md:hidden p-2 rounded-md border border-blue-200 text-blue-700 focus:outline-none bg-white/90"
          onClick={() => setOpen((v) => !v)}
          aria-label="Open menu"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>
      </nav>

      {/* Mobile Drawer */}
      {open && (
        <div className="md:hidden fixed inset-0 bg-black/30 z-50" onClick={() => setOpen(false)}>
          <div
            className="absolute top-0 right-0 w-64 bg-white h-full shadow-lg p-6 flex flex-col gap-4"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="self-end mb-4 p-1 focus:outline-none"
              onClick={() => setOpen(false)}
              aria-label="Close menu"
            >
              <svg className="w-6 h-6 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            {NAV.map((item) => (
              <Link
                key={item.label}
                href={item.href}
                className="py-1 text-slate-700 hover:text-blue-700 focus:outline-none"
                onClick={() => setOpen(false)}
              >
                {item.label}
              </Link>
            ))}
            {token && (
              <Link
                href="/auth/profile"
                className="mt-2 inline-flex items-center gap-2 rounded-md border border-blue-200 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50"
                onClick={() => setOpen(false)}
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                  <circle cx="12" cy="7" r="4" />
                </svg>
                Profile
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
