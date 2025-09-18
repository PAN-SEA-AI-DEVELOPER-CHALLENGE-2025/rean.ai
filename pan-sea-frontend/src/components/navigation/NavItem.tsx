import React from 'react';
import Link from 'next/link';

interface NavItemProps {
  label: string;
  href?: string;
  isActive?: boolean;
  hasDropdown?: boolean;
  onClick?: () => void;
  onMouseEnter?: () => void;
  className?: string;
}

export default function NavItem({ 
  label, 
  href, 
  isActive = false, 
  hasDropdown = false,
  onClick,
  onMouseEnter,
  className = ''
}: NavItemProps) {
  const baseClasses = `
    group relative px-3 py-2 text-sm font-medium text-zinc-700 
    transition hover:text-zinc-900 dark:text-zinc-300 dark:hover:text-white
    ${className}
  `.trim();

  const underlineClasses = `
    pointer-events-none absolute inset-x-2 -bottom-[2px] h-[2px] origin-left 
    scale-x-0 bg-gradient-to-r from-indigo-500 via-violet-500 to-indigo-500 
    transition-transform duration-300 group-hover:scale-x-100
  `;

  const activeIndicator = isActive && (
    <span className="absolute left-1/2 top-[calc(100%+3px)] h-1.5 w-1.5 -translate-x-1/2 rotate-45 rounded-[3px] bg-indigo-500"></span>
  );

  if (hasDropdown || !href) {
    return (
      <button
        onClick={onClick}
        onMouseEnter={onMouseEnter}
        className={baseClasses}
      >
        {label}
        <span className={underlineClasses} />
        {activeIndicator}
      </button>
    );
  }

  return (
    <Link href={href} className={baseClasses}>
      {label}
      <span className={underlineClasses} />
      {activeIndicator}
    </Link>
  );
}
