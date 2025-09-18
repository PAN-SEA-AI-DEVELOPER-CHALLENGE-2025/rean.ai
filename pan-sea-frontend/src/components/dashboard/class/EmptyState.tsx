"use client";

interface EmptyStateProps {
  onCreateClass: () => void;
  canCreate?: boolean;
}

export default function EmptyState({ onCreateClass, canCreate = true }: EmptyStateProps) {
  return (
    <div className="mt-10 rounded-xl border border-dashed border-slate-300 p-10 text-center">
      <p className="text-slate-600">
        {canCreate ? (
          <>
            No classes found{" "}
            <button 
              className="text-sky-700 font-semibold hover:underline" 
              onClick={onCreateClass}
            >
              Create one
            </button>
            .
          </>
        ) : (
          "No classes found."
        )}
      </p>
    </div>
  );
}
