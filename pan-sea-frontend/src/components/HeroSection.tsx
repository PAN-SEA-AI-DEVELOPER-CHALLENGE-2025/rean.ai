import HeroContent from './HeroContent';
import HeroImage from './HeroImage';
import WaveDecoration from './WaveDecoration';

export default function HeroSection() {
  return (
    <section className="relative overflow-hidden">
      <div className="mx-auto max-w-7xl px-6 py-14 md:py-20 grid md:grid-cols-2 items-center gap-12 mb-[150px]">
        <HeroContent />
        <HeroImage />
      </div>
      <WaveDecoration />
    </section>
  );
}
