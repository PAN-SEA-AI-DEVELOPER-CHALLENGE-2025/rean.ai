// components/Footer.tsx
import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="relative border-t border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100 text-slate-700">
      <div className="mx-auto max-w-7xl px-6 pt-14 pb-8">
        <div className="grid gap-10 md:grid-cols-5">
          {/* Brand */}
          <div className="md:col-span-2">
            <Link href="/" className="flex items-center gap-4 group focus:outline-none focus:ring-0">
             <Image src="/logo.png" alt="rean.ai logo" width={100} height={100} />
            </Link>
            <p className="mt-6 max-w-md text-sm text-slate-600 leading-relaxed">
              AI-powered lecture recording, transcription, summaries, quizzes, and
              study tools—so students learn faster and remember more.
            </p>

            {/* Socials */}
            <div className="mt-6 flex items-center gap-3">
              <a
                href="#"
                aria-label="X / Twitter"
                className="rounded-full border border-slate-300 p-2.5 hover:text-blue-600 transition-colors duration-200 focus:outline-none focus:ring-0"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" className="text-slate-600 group-hover:text-blue-600">
                  <path
                    d="M4 4l16 16M20 4L4 20"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                  />
                </svg>
              </a>
              <a
                href="#"
                aria-label="YouTube"
                className="rounded-full border border-slate-300 p-2.5 hover:text-blue-600 transition-colors duration-200 focus:outline-none focus:ring-0"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" className="text-slate-600 group-hover:text-blue-600">
                  <path
                    d="M22 12s0-4-1-5-5-1-9-1-8 0-9 1-1 5-1 5 0 4 1 5 5 1 9 1 8 0 9-1 1-5 1-5z"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                  />
                  <path d="M10 9l5 3-5 3V9z" fill="currentColor" />
                </svg>
              </a>
              <a
                href="#"
                aria-label="Facebook"
                className="rounded-full border border-slate-300 p-2.5 hover:text-blue-600 transition-colors duration-200 focus:outline-none focus:ring-0"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" className="text-slate-600 group-hover:text-blue-600">
                  <path
                    d="M15 3h-3a4 4 0 0 0-4 4v3H5v3h3v8h3v-8h3l1-3h-4V7a1 1 0 0 1 1-1h3V3z"
                    fill="currentColor"
                  />
                </svg>
              </a>
              <a
                href="#"
                aria-label="LinkedIn"
                className="rounded-full border border-slate-300 p-2.5 hover:text-blue-600 transition-colors duration-200 focus:outline-none focus:ring-0"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" className="text-slate-600 group-hover:text-blue-600">
                  <path
                    d="M4 4a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM4 9h4v11H4zM10 9h4v2.5h.06A4.37 4.37 0 0 1 18 9c3 0 5 2 5 6v5h-4v-4c0-2-1-3-2.5-3S14 14 14 16v4h-4V9z"
                    fill="currentColor"
                  />
                </svg>
              </a>
            </div>
          </div>

          {/* Columns */}
          <div>
            <h3 className="text-sm font-bold text-slate-900 mb-4">Product</h3>
            <ul className="space-y-3 text-sm">
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Recorder</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Transcription</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Summaries</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Q&A</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Quizzes & Flashcards</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-900 mb-4">Company</h3>
            <ul className="space-y-3 text-sm">
              <li><Link href="/about_us" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">About us</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">News</Link></li>
              <li><Link href="/contact" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Contact</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Careers</Link></li>
            </ul>
          </div>

          <div>
            <h3 className="text-sm font-bold text-slate-900 mb-4">Resources</h3>
            <ul className="space-y-3 text-sm">
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Help Center</Link></li>
              <li><Link href="/faq" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">FAQ</Link></li>
              <li><Link href="/user-guide" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">User Guide</Link></li>
              <li><Link href="#" className="text-slate-600 hover:text-blue-600 transition-colors duration-200 font-medium focus:outline-none focus-visible:outline-none focus:ring-0 focus-visible:ring-0">Documentation</Link></li>
            </ul>
          </div>
        </div>

        {/* Newsletter + bottom bar */}
        <div className="mt-16 border-t border-slate-200 pt-8 md:flex md:items-center md:justify-between">
          <div className="mb-6 md:mb-0">
            <h4 className="text-sm font-bold text-slate-900 mb-2">Stay Updated</h4>
            <p className="text-sm text-slate-600 mb-4">Get the latest updates on new features and improvements.</p>
            <form
              className="flex w-full max-w-md items-center gap-3"
              method="post"
              action="/api/newsletter/subscribe"
              noValidate
            >
              <label htmlFor="newsletter" className="sr-only">
                Email for updates
              </label>
              <input
                id="newsletter"
                name="email"
                type="email"
                required
                placeholder="you@example.com"
                className="flex-1 rounded-lg border border-slate-300 px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-sm"
              />
              <button
                type="submit"
                className="rounded-lg bg-gradient-to-r from-blue-500 to-blue-600 px-6 py-2.5 font-semibold text-white hover:from-blue-600 hover:to-blue-700 shadow-lg hover:shadow-blue-500/25 transition-all duration-300 text-sm"
              >
                Subscribe
              </button>
            </form>
          </div>

          <div className="text-right">
            <p className="text-sm text-slate-500 mb-2">
              © {new Date().getFullYear()} Rean.ai. All rights reserved.
            </p>
            <div className="flex items-center justify-end gap-4 text-xs text-slate-400">
              <Link href="#" className="hover:text-slate-600 transition-colors duration-200">Privacy Policy</Link>
              <span>•</span>
              <Link href="#" className="hover:text-slate-600 transition-colors duration-200">Terms of Service</Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
