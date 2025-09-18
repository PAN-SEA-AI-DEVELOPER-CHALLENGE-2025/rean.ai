"use client";

import { useRouter } from "next/navigation";
import { useState, type MouseEvent } from "react";
import { fetchClassById, fetchClassStudents } from "@/services/classes";
import { fetchSummaries } from "@/services/summaries";
import { useAuth } from "@/hooks/useAuth";

export type ClassItem = {
  id: string;
  code: string;         
  name: string;        
  faculty?: string;    
  grade?: string;      
  schedule?: string;    
  color?: string;      
  students?: string[];
};

interface ClassCardProps {
  classItem: ClassItem;
  onDelete: (id: string) => void;
}

export default function ClassCard({ classItem, onDelete }: ClassCardProps) {
  const router = useRouter();
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isStudentsOpen, setIsStudentsOpen] = useState(false);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [students, setStudents] = useState<string[] | null>(null);
  const [studentsError, setStudentsError] = useState<string | null>(null);
  const { user } = useAuth();
  const role = user?.role?.toLowerCase?.();
  const canManage = role !== undefined && role !== 'student';

  const handleEdit = () => {
    alert("Edit coming soon");
  };

  const handleDelete = () => {
    setIsConfirmOpen(true);
  };

  const openStudents = async (e: MouseEvent) => {
    e.stopPropagation();
    setIsStudentsOpen(true);
    if (!students) {
      try {
        setStudentsError(null);
        setStudentsLoading(true);
        const ids = await fetchClassStudents(classItem.id);
        setStudents(ids);
      } catch (err) {
        setStudentsError("Failed to load students");
      } finally {
        setStudentsLoading(false);
      }
    }
  };

  const confirmDelete = async () => {
    try {
      setIsDeleting(true);
      await Promise.resolve(onDelete(classItem.id));
      setIsConfirmOpen(false);
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <article
      role="button"
      tabIndex={0}
      onClick={() => router.push(`/dashboard/class_detail/${classItem.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          router.push(`/dashboard/class_detail/${classItem.id}`);
        }
      }}
      onMouseEnter={() => {
        // Warm caches: class details and summaries for the target class
        fetchClassById(classItem.id).catch(() => {});
        fetchSummaries(classItem.id).catch(() => {});
      }}
      className="rounded-2xl border border-slate-200 bg-white shadow-sm cursor-pointer transition-all duration-200 hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg hover:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2"
    >
      <div className="p-5">
        <div className="flex items-start justify-between">
          <div className={`inline-flex items-center gap-2 rounded-md px-2 py-1 text-xs font-semibold ${classItem.color}`}>
            <span>{classItem.code}</span>
          </div>
          <span className="text-xs text-slate-500">{classItem.grade || "—"}</span>
        </div>

        <h3 className="mt-3 text-lg font-bold leading-snug">{classItem.name}</h3>

        <dl className="mt-3 text-sm text-slate-600 grid gap-1">
          <div className="flex justify-between">
            <dt className="text-slate-500">Teacher</dt>
            <dd className="font-medium">{classItem.faculty || "—"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Grade</dt>
            <dd className="font-medium">{classItem.grade || "—"}</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-slate-500">Schedule</dt>
            <dd className="font-medium">{classItem.schedule || "TBA"}</dd>
          </div>
        </dl>

        <div className="mt-5 flex items-center justify-between">
          <button
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
            onClick={openStudents}
          >
            Students{Array.isArray(classItem.students) ? ` (${classItem.students.length})` : ''}
          </button>
          <div className="flex items-center gap-2">
            {canManage && (
              <>
                <button
                  className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleEdit();
                  }}
                >
                  Edit
                </button>
                <button
                  className="rounded-md border border-rose-200 text-rose-700 px-3 py-1.5 text-sm hover:bg-rose-50"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete();
                  }}
                >
                  Delete
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {isStudentsOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm opacity-0 animate-[fadeInUp_0.2s_ease-out_forwards]"
            onClick={() => setIsStudentsOpen(false)}
            aria-hidden="true"
          />
          <div className="relative w-full max-w-md rounded-2xl bg-white shadow-xl border border-slate-200 transform opacity-0 scale-95 animate-[bounceIn_0.35s_ease-out_forwards]">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between">
              <h3 className="text-base font-semibold text-slate-800">Students</h3>
              <button
                className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
                onClick={() => setIsStudentsOpen(false)}
              >
                Close
              </button>
            </div>
            <div className="p-5 max-h-72 overflow-auto">
              {studentsLoading ? (
                <div className="flex items-center gap-2 text-slate-600">
                  <div className="w-4 h-4 border-2 border-slate-300 border-t-slate-600 rounded-full animate-spin" />
                  Loading students...
                </div>
              ) : studentsError ? (
                <div className="text-rose-600 text-sm">{studentsError}</div>
              ) : !students || students.length === 0 ? (
                <div className="text-slate-600 text-sm">No students enrolled.</div>
              ) : (
                <ul className="space-y-2">
                  {students.map((sid) => (
                    <li key={sid} className="text-sm text-slate-800 break-all">{sid}</li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      )}

      {isConfirmOpen && (
        <div
          role="dialog"
          aria-modal="true"
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
        >
          <div
            className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm opacity-0 animate-[fadeInUp_0.2s_ease-out_forwards]"
            onClick={() => setIsConfirmOpen(false)}
            aria-hidden="true"
          />
          <div className="relative w-full max-w-md rounded-2xl bg-white shadow-xl border border-slate-200 transform opacity-0 scale-95 animate-[bounceIn_0.35s_ease-out_forwards]">
            <div className="p-5 border-b border-slate-200 flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-rose-100 text-rose-700 flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M4.93 4.93l14.14 14.14M9.17 4h5.66a2 2 0 011.789 1.106l.894 1.789A2 2 0 0019.553 8H4.447a2 2 0 01-1.789-3.105l.894-1.789A2 2 0 014.83 4z" />
                </svg>
              </div>
              <h3 className="text-base font-semibold text-slate-800">Delete class</h3>
            </div>
            <div className="p-5">
              <p className="text-sm text-slate-600">
                Are you sure you want to delete “<span className="font-semibold">{classItem.name}</span>”? This action is permanent and cannot be undone.
              </p>
            </div>
            <div className="p-5 pt-0 flex items-center justify-end gap-3">
              <button
                disabled={isDeleting}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                onClick={() => setIsConfirmOpen(false)}
              >
                Cancel
              </button>
              <button
                disabled={isDeleting}
                className="rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700 shadow-sm active:scale-95 disabled:opacity-60 flex items-center gap-2"
                onClick={confirmDelete}
              >
                {isDeleting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Deleting...
                  </>
                ) : (
                  'Delete'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </article>
  );
}
