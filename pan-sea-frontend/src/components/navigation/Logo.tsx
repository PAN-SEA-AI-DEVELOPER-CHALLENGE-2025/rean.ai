import React from 'react';
import Link from 'next/link';
import Image from 'next/image';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showBadge?: boolean;
  badgeText?: string;
  className?: string;
  href?: string;
}

const sizeConfig = {
  sm: {
    container: 'h-7 w-7',
    image: { width: 28, height: 28 },
    text: 'text-sm',
    badge: 'text-[9px] px-1.5 py-0.5'
  },
  md: {
    container: 'h-8 w-8',
    image: { width: 32, height: 32 },
    text: 'text-[17px]',
    badge: 'text-[10px] px-2 py-0.5'
  },
  lg: {
    container: 'h-10 w-10',
    image: { width: 40, height: 40 },
    text: 'text-xl',
    badge: 'text-xs px-2.5 py-1'
  }
};

export default function Logo({ 
  size = 'md', 
  showBadge = true, 
  badgeText = 'New',
  className = '',
  href = '/'
}: LogoProps) {
  const config = sizeConfig[size];
  
  const logoContent = (
    <div className={`group flex items-center gap-2 ${className}`}>
      <span className={`relative inline-flex ${config.container} items-center justify-center overflow-hidden rounded-xl ring-1 ring-slate-200 bg-white`}>
        <Image 
          src="/logo.png" 
          alt="Rean.ai logo" 
          width={config.image.width} 
          height={config.image.height} 
          className="relative"
          priority
        />
      </span>
      <span className={`${config.text} font-bold tracking-tight text-slate-900`}>
        <span className="text-blue-700">Rean</span>
        <span className="text-slate-800">.ai</span>
      </span>
      {showBadge && (
        <span className={`ml-2 hidden rounded-full bg-blue-600/10 ${config.badge} font-semibold text-blue-700 ring-1 ring-inset ring-blue-600/20 md:inline`}>
          {badgeText}
        </span>
      )}
    </div>
  );

  if (href) {
    return <Link href={href}>{logoContent}</Link>;
  }

  return logoContent;
}
