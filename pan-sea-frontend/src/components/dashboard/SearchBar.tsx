"use client";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export default function SearchBar({ value, onChange, placeholder = "Search classes" }: SearchBarProps) {
  return (
    <label className="flex items-center gap-2 rounded-full border border-slate-300 px-3 py-2 text-sm text-slate-600 shadow-sm">
      <svg width="16" height="16" viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M21 21l-4.35-4.35M10.5 18a7.5 7.5 0 1 1 0-15 7.5 7.5 0 0 1 0 15Z"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
        />
      </svg>
      <input
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="outline-none bg-transparent placeholder:text-slate-400 w-44 md:w-64"
        placeholder={placeholder}
        aria-label={placeholder}
      />
    </label>
  );
}
