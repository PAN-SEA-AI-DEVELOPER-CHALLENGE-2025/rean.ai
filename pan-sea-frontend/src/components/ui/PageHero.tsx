import React from 'react';
import { IconType } from 'react-icons';

interface PageHeroProps {
  icon: IconType;
  title: string;
  description: string;
  className?: string;
}

export default function PageHero({ icon: Icon, title, description, className = "" }: PageHeroProps) {
  return (
    <section className={`relative overflow-hidden bg-white ${className}`}>
      <div className="absolute inset-0 bg-gradient-to-r from-sky-600 to-blue-700 opacity-90"></div>
      <div className="relative max-w-7xl mx-auto px-6 py-24 text-center">
        <div className="flex justify-center mb-6">
          <div className="w-20 h-20 bg-white/20 rounded-full flex items-center justify-center">
            <Icon className="text-4xl text-white" />
          </div>
        </div>
        <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
          {title}
        </h1>
        <p className="text-xl md:text-2xl text-sky-100 max-w-3xl mx-auto leading-relaxed">
          {description}
        </p>
      </div>
    </section>
  );
}
