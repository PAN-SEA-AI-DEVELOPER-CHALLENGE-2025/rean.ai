import React from 'react';
import { IconType } from 'react-icons';

interface SocialLink {
  icon: IconType;
  href: string;
  label: string;
  color?: string;
}

interface SocialLinksProps {
  links: SocialLink[];
  title?: string;
  className?: string;
}

export default function SocialLinks({ links, title = "Follow Us", className = "" }: SocialLinksProps) {
  return (
    <div className={`bg-white p-6 rounded-2xl shadow-lg ${className}`}>
      <h4 className="font-semibold text-slate-900 mb-4">{title}</h4>
      <div className="flex space-x-4">
        {links.map((link, index) => {
          const Icon = link.icon;
          const colorClass = link.color || 'blue';
          
          return (
            <a 
              key={index}
              href={link.href} 
              aria-label={link.label}
              className={`w-10 h-10 bg-${colorClass}-100 rounded-full flex items-center justify-center hover:bg-${colorClass}-200 transition-colors`}
            >
              <Icon className={`text-${colorClass}-600`} />
            </a>
          );
        })}
      </div>
    </div>
  );
}

export type { SocialLink, SocialLinksProps };
