// app/page.tsx (Server Component)
import Header from '@/components/Header';
import HeroSection from '@/components/HeroSection';
import FeaturesSection from '@/components/FeaturesSection';
import Footer from '@/components/Footer';

export default function Page() {
  return (
    <main className="min-h-screen bg-white text-slate-800">
      <Header />
      <HeroSection />
      <FeaturesSection />
      <Footer />
    </main>
  );
}
