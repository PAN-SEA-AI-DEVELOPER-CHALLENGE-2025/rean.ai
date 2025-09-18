import React from 'react';
import Link from 'next/link';
import Logo from './Logo';
import SearchInput from './SearchInput';
import ThemeToggle from './ThemeToggle';

export interface NavItemType {
  label: string;
  href?: string;
  children?: { label: string; desc?: string; href: string; emoji?: string }[];
}

interface MobileDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  navItems: NavItemType[];
  isActive: (href?: string) => boolean;
  onSearch?: (query: string) => void;
  className?: string;
}

function cx(...classes: (string | false | undefined)[]) {
  return classes.filter(Boolean).join(' ');
}

export default function MobileDrawer({ 
  isOpen, 
  onClose, 
  navItems, 
  isActive,
  onSearch,
  className = ''
}: MobileDrawerProps) {
  return (
    <div className={cx('fixed inset-0 z-50 md:hidden', isOpen ? 'pointer-events-auto' : 'pointer-events-none', className)}>
      {/* Backdrop */}
      <div
        onClick={onClose}
        className={cx('absolute inset-0 bg-black/40 backdrop-blur-sm transition-opacity', isOpen ? 'opacity-100' : 'opacity-0')}
      />

      {/* Sheet */}
      <div
        className={cx(
          'absolute right-0 top-0 h-full w-[85%] max-w-sm border-l border-zinc-200/60 bg-white/85 backdrop-blur-2xl shadow-2xl dark:border-zinc-800 dark:bg-zinc-950/70',
          'transition-transform duration-300',
          isOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        {/* Header */}
        <DrawerHeader onClose={onClose} />

        {/* Content */}
        <div className="px-3 pb-6">
          {/* Search */}
          <div className="mb-3">
            <SearchInput 
              placeholder="Search…" 
              isMobile={true}
              onSearch={onSearch}
            />
          </div>

          {/* Navigation */}
          <div className="grid gap-1">
            {navItems.map((item) => 
              item.children ? (
                <CollapsibleNavItem key={item.label} item={item} />
              ) : (
                <NavLink 
                  key={item.label}
                  label={item.label}
                  href={item.href!}
                  isActive={isActive(item.href)}
                />
              )
            )}
          </div>

          {/* Actions */}
          <div className="mt-4 flex items-center gap-2">
            <ThemeToggle isMobile={true} />
            <Link
              href="/get-started"
              className="flex-1 rounded-xl bg-indigo-600 px-3 py-2 text-center text-sm font-semibold text-white"
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function DrawerHeader({ onClose }: { onClose: () => void }) {
  return (
    <div className="flex items-center justify-between p-4">
      <Logo size="sm" showBadge={false} href="/" />
      <button
        onClick={onClose}
        className="rounded-lg border border-zinc-200/70 bg-white/70 px-2 py-1 text-sm dark:border-zinc-800 dark:bg-zinc-900/70"
        aria-label="Close menu"
      >
        ✕
      </button>
    </div>
  );
}

function CollapsibleNavItem({ item }: { item: NavItemType }) {
  return (
    <details className="group rounded-xl">
      <summary className="flex cursor-pointer list-none items-center justify-between rounded-xl px-3 py-2 text-zinc-800 hover:bg-zinc-100 dark:text-zinc-200 dark:hover:bg-zinc-800/60">
        <span className="text-sm font-medium">{item.label}</span>
        <span className="transition group-open:rotate-180">⌄</span>
      </summary>
      <div className="ml-2 mt-1 grid gap-1 border-l border-zinc-200/60 pl-3 dark:border-zinc-800">
        {item.children?.map((child) => (
          <Link
            key={child.href}
            href={child.href}
            className="rounded-lg px-3 py-2 text-sm text-zinc-700 transition hover:bg-zinc-100 dark:text-zinc-300 dark:hover:bg-zinc-800/60"
          >
            {child.emoji && <span className="mr-2">{child.emoji}</span>}
            {child.label}
            {child.desc && (
              <span className="ml-2 text-xs text-zinc-500 dark:text-zinc-400">— {child.desc}</span>
            )}
          </Link>
        ))}
      </div>
    </details>
  );
}

function NavLink({ label, href, isActive }: { label: string; href: string; isActive: boolean }) {
  return (
    <Link
      href={href}
      className={cx(
        'rounded-xl px-3 py-2 text-sm font-medium transition hover:bg-zinc-100 dark:hover:bg-zinc-800/60',
        isActive && 'bg-indigo-500/10 ring-1 ring-indigo-500/30'
      )}
    >
      {label}
    </Link>
  );
}
