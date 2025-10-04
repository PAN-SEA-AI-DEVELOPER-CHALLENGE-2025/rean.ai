import React from 'react';
import Link from 'next/link';

export interface DropdownItem {
  label: string;
  desc?: string;
  href: string;
  emoji?: string;
}

interface DropdownMenuProps {
  items: DropdownItem[];
  isVisible: boolean;
  onMouseLeave?: () => void;
  className?: string;
}

export default function DropdownMenu({ 
  items, 
  isVisible, 
  onMouseLeave,
  className = ''
}: DropdownMenuProps) {
  if (!isVisible) return null;

  return (
    <div 
      onMouseLeave={onMouseLeave} 
      className={`absolute left-0 right-0 top-full z-30 ${className}`}
    >
      <div className="mx-auto max-w-6xl px-4">
        <div className="mt-3 rounded-2xl border border-zinc-200/60 bg-white/70 p-4 backdrop-blur-xl shadow-lg ring-1 ring-black/5 dark:bg-zinc-900/70 dark:border-zinc-800">
          <div className="grid gap-2 sm:grid-cols-2 md:grid-cols-4">
            {items.map((item) => (
              <DropdownItem key={item.href} {...item} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function DropdownItem({ label, desc, href, emoji }: DropdownItem) {
  return (
    <Link
      href={href}
      className="group rounded-xl p-3 transition hover:bg-zinc-100/70 dark:hover:bg-zinc-800/60"
    >
      <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-zinc-100">
        {emoji && <span className="text-base">{emoji}</span>}
        <span className="group-hover:translate-x-0.5 transition">{label}</span>
      </div>
      {desc && (
        <div className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">{desc}</div>
      )}
    </Link>
  );
}
