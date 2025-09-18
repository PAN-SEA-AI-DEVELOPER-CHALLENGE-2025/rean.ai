'use client';

import ClassDashboard from "@/components/dashboard/ClassDashboard";
import Header from "@/components/Header";
import { useAuth } from "@/hooks/useAuth";

export default function DashboardPage() {
  const { user, logout, isLoading } = useAuth();

  if (isLoading) {
    return (
      <main className="min-h-screen bg-white text-slate-800 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600 mx-auto"></div>
          <p className="mt-2 text-slate-600">Loading...</p>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-white text-slate-800">
      <Header />  
      <ClassDashboard />
    </main>
  );
}
