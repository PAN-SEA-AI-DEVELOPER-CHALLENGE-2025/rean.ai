import React, { useEffect, useState } from 'react';

interface ThemeToggleProps {
  className?: string;
  showLabel?: boolean;
  isMobile?: boolean;
}

export default function ThemeToggle({ 
  className = '', 
  showLabel = false,
  isMobile = false 
}: ThemeToggleProps) {
  const [dark, setDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const prefers =
      localStorage.getItem('prefers-dark') === 'true' ||
      (!localStorage.getItem('prefers-dark') &&
        window.matchMedia('(prefers-color-scheme: dark)').matches);
    setDark(prefers);
  }, []);

  useEffect(() => {
    if (mounted) {
      document.documentElement.classList.toggle('dark', dark);
      localStorage.setItem('prefers-dark', String(dark));
    }
  }, [dark, mounted]);

  const toggleTheme = () => {
    setDark(prev => !prev);
  };

  // Prevent hydration mismatch
  if (!mounted) {
    return (
      <button
        className={`
          rounded-xl border border-zinc-200/70 bg-white/70 px-3 py-2 text-sm text-zinc-700 
          shadow-sm transition hover:bg-white dark:border-zinc-800 dark:bg-zinc-900/70 
          dark:text-zinc-200 ${isMobile ? 'flex-1' : ''} ${className}
        `.trim()}
        disabled
      >
        {showLabel ? 'Toggle theme ' : ''}☀️
      </button>
    );
  }

  if (isMobile) {
    return (
      <button
        onClick={toggleTheme}
        className={`
          flex-1 rounded-xl border border-zinc-200/70 bg-white/70 px-3 py-2 text-sm 
          dark:border-zinc-800 dark:bg-zinc-900/70 ${className}
        `.trim()}
      >
        Toggle theme {dark ? '🌙' : '☀️'}
      </button>
    );
  }

  return (
    <button
      onClick={toggleTheme}
      title="Toggle theme"
      className={`
        rounded-xl border border-zinc-200/70 bg-white/70 px-3 py-2 text-sm text-zinc-700 
        shadow-sm transition hover:bg-white dark:border-zinc-800 dark:bg-zinc-900/70 
        dark:text-zinc-200 ${className}
      `.trim()}
    >
      {showLabel && `Toggle theme `}
      {dark ? '🌙' : '☀️'}
    </button>
  );
}
