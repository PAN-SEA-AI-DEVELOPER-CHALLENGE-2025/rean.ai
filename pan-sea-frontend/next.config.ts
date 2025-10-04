import type { NextConfig } from "next";

const isProd = process.env.NODE_ENV === 'production';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  images: {
    formats: ['image/avif', 'image/webp'],
    remotePatterns: [
      {
        protocol: 'https',
        // Replace with your actual image domains in production
        hostname: isProd ? 'YOUR-PROD-IMAGE-DOMAIN.example.com' : '**',
      },
    ],
  },
  compress: true,
  reactStrictMode: true,
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
  eslint: {
    // Allow production builds to succeed even if there are ESLint errors
    ignoreDuringBuilds: true,
  },
  experimental: {
    optimizePackageImports: [
      'lucide-react',
      'react-icons',
    ],
  },
  // Increase body size limit for file uploads
  serverExternalPackages: [],
  // Custom webpack config for larger file handling
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        ...config.resolve.fallback,
        fs: false,
      };
    }
    return config;
  },
  async headers() {
    // Global security headers; you can tailor by path later if needed
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'X-Content-Type-Options', value: 'nosniff' },
          { key: 'X-Frame-Options', value: 'DENY' },
          { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
          { key: 'Permissions-Policy', value: 'camera=(), microphone=(), geolocation=(), interest-cohort=()' },
          { key: 'Content-Security-Policy', value: [
            "default-src 'self'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
            "img-src 'self' data: blob: https:",
            "media-src 'self' data: blob: https:",
            isProd ? "script-src 'self' https:" : "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:",
            "style-src 'self' 'unsafe-inline' https:",
            "font-src 'self' data: https:",
            isProd ? "connect-src 'self' https:" : "connect-src 'self' https: http://localhost:8000 http://127.0.0.1:8000",
          ].join('; ') },
          { key: 'Strict-Transport-Security', value: 'max-age=63072000; includeSubDomains; preload' },
        ],
      },
    ];
  },
};

export default nextConfig;

