"use client";

import SearchBar from "./SearchBar";

interface DashboardHeaderProps {
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onCreateClass: () => void;
  canCreate?: boolean;
}

export default function DashboardHeader({ 
  searchQuery, 
  onSearchChange, 
  onCreateClass,
  canCreate = true,
}: DashboardHeaderProps) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
      <div>
        <h1 className="text-3xl md:text-4xl font-extrabold tracking-tight">Your Classes</h1>
        <p className="text-slate-600 mt-1">{canCreate ? "Browse, search, and create new classes." : "Browse and search your classes."}</p>
      </div>

      <div className="flex items-center gap-3">
        <SearchBar 
          value={searchQuery}
          onChange={onSearchChange}
          placeholder="Search classes"
        />
        {canCreate && (
          <button
            onClick={onCreateClass}
            className="rounded-lg bg-sky-600 hover:bg-sky-700 text-white px-4 py-2.5 font-semibold shadow-sm"
          >
            + New Class
          </button>
        )}
      </div>
    </div>
  );
}
