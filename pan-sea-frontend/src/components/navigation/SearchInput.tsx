import React, { useState } from 'react';

interface SearchInputProps {
  placeholder?: string;
  shortcut?: string;
  expandOnFocus?: boolean;
  onSearch?: (query: string) => void;
  className?: string;
  isMobile?: boolean;
}

export default function SearchInput({ 
  placeholder = "Search docs…",
  shortcut = "/",
  expandOnFocus = true,
  onSearch,
  className = '',
  isMobile = false
}: SearchInputProps) {
  const [query, setQuery] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (onSearch && query.trim()) {
      onSearch(query.trim());
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setQuery(e.target.value);
  };

  if (isMobile) {
    return (
      <form onSubmit={handleSubmit} className={`w-full ${className}`}>
        <input
          type="search"
          placeholder={placeholder}
          value={query}
          onChange={handleChange}
          className="w-full rounded-xl border border-zinc-200/70 bg-white/70 px-3 py-2 text-sm dark:border-zinc-800 dark:bg-zinc-900/70"
        />
      </form>
    );
  }

  return (
    <form onSubmit={handleSubmit} className={`group relative ${className}`}>
      <input
        type="search"
        placeholder={placeholder}
        value={query}
        onChange={handleChange}
        onFocus={() => setIsFocused(true)}
        onBlur={() => setIsFocused(false)}
        className={`
          rounded-xl border border-zinc-200/70 bg-white/60 px-3 py-2 text-sm text-zinc-700 
          outline-none transition-all placeholder:text-zinc-400 dark:border-zinc-800 
          dark:bg-zinc-900/60 dark:text-zinc-200 dark:focus:bg-zinc-900
          ${expandOnFocus ? (isFocused ? 'w-56 bg-white' : 'w-36') : 'w-full'}
        `.trim()}
      />
      {shortcut && (
        <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 rounded-md border border-zinc-200 bg-white px-1.5 text-[10px] text-zinc-500 shadow-sm dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-400">
          {shortcut}
        </kbd>
      )}
    </form>
  );
}
