"use client";

import { useEffect, useMemo, useState, use, useRef } from "react";
import Link from "next/link";
import LessonUploadModal from "@/components/dashboard/LessonUploadModal";
import { fetchClassById, fetchClassStudentProfiles } from "@/services/classes";
import { fetchSummaries, fetchSummaryById } from "@/services/summaries";
import { deleteLesson, fetchLessons } from "@/services/lessons";
import { toast } from "react-toastify";
import { SummaryItem } from "@/types/api";
import { useAuth } from "@/hooks/useAuth";

type ClassItem = {
  id: string;
  code: string;
  name: string;
  faculty?: string;
  grade?: string;
  schedule?: string;
  color?: string;
  students?: string[];
};

function uid() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export default function ClassDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const actionMenuRef = useRef<HTMLDivElement>(null);
  const emptyMenuRef = useRef<HTMLDivElement>(null);
  const [classItem, setClassItem] = useState<ClassItem | null>(null);
  const [summaries, setSummaries] = useState<SummaryItem[] | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [isActionMenuOpen, setIsActionMenuOpen] = useState(false);
  const [isEmptyMenuOpen, setIsEmptyMenuOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [confirmTarget, setConfirmTarget] = useState<{ id: string; title: string } | null>(null);
  const [isConfirmDeleting, setIsConfirmDeleting] = useState(false);
  const [query, setQuery] = useState("");
  const [tab, setTab] = useState<"all" | "homework" | "recent">("all");
  const [sortBy, setSortBy] = useState<"date_desc" | "date_asc" | "title_asc" | "title_desc">("date_desc");
  const [showStudents, setShowStudents] = useState(false);
  const [students, setStudents] = useState<{ id: string; name: string }[] | null>(null);
  const [studentsLoading, setStudentsLoading] = useState(false);
  const [studentsError, setStudentsError] = useState<string | null>(null);
  const { user } = useAuth();
  const role = user?.role?.toLowerCase?.();
  const canManage = role !== undefined && role !== 'student';

  useEffect(() => {
    async function loadClassData() {
      try {
        // Fetch class from API only
        const found: ClassItem | null = await fetchClassById(id);
        
        if (!found) {
          setNotFound(true);
          setIsLoading(false);
          return;
        }
        
        setClassItem(found);

        // Fetch lessons list and map to table rows
        try {
          console.log('Fetching lessons for class:', id);
          const lessons = await fetchLessons(id, 100, 0);
          console.log('Fetched lessons:', lessons);
          const rows = (lessons || []).map((l) => ({
            id: l.id,
            classId: id,
            lessonId: l.id,
            lectureTitle: l.title,
            summary: '',
            topicsDiscussed: [],
            learningObjectives: [],
            homework: [],
            announcements: [],
            duration: l.duration || 0,
            nextClassPreview: null,
            createdAt: l.datetime,
            updatedAt: l.datetime,
            keyPoints: [],
            studyQuestions: [],
          } as SummaryItem));
          setSummaries(rows);
        } catch (lessonsError) {
          console.error('Error fetching lessons:', lessonsError);
          setSummaries([]);
        }
      } catch (error) {
        console.error('Error loading class data:', error);
        setNotFound(true);
      } finally {
        setIsLoading(false);
      }
    }

    loadClassData();
  }, [id]);

  // header visuals removed; keep design minimal above table

  const handleUploadFile = () => {
    if (!canManage) return;
    setIsActionMenuOpen(false);
    setIsEmptyMenuOpen(false);
    setIsUploadModalOpen(true);
  };

  // live recording removed

  const openStudents = async () => {
    setShowStudents(true);
    if (students === null) {
      try {
        setStudentsError(null);
        setStudentsLoading(true);
        const list = await fetchClassStudentProfiles(id);
        setStudents(list);
      } catch (err) {
        setStudentsError("Failed to load students");
      } finally {
        setStudentsLoading(false);
      }
    }
  };

  const openDeleteConfirm = (lessonId: string, title: string) => {
    setConfirmTarget({ id: lessonId, title });
    setIsConfirmOpen(true);
  };

  const handleDeleteLesson = async () => {
    if (!confirmTarget) return;
    const lessonId = confirmTarget.id;
    setDeletingId(lessonId);
    setIsConfirmDeleting(true);
    try {
      await deleteLesson(id, lessonId);
      setSummaries((prev) => (prev ? prev.filter((s) => s.lessonId !== lessonId && s.id !== lessonId) : prev));
      toast.success("Lesson deleted");
      setIsConfirmOpen(false);
      setConfirmTarget(null);
    } catch (err) {
      console.error("Failed to delete lesson", err);
      toast.error("Failed to delete lesson");
    } finally {
      setIsConfirmDeleting(false);
      setDeletingId(null);
    }
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const targetNode = event.target as Node;
      const clickedOutsideAction = actionMenuRef.current && !actionMenuRef.current.contains(targetNode);
      const clickedOutsideEmpty = emptyMenuRef.current && !emptyMenuRef.current.contains(targetNode);

      if (clickedOutsideAction) setIsActionMenuOpen(false);
      if (clickedOutsideEmpty) setIsEmptyMenuOpen(false);
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleLessonUpload = async (lessonData: {
    title: string;
    description: string;
    file: File | null;
    dateTime: string;
    summaryId?: string;
    isAudioTranscribed?: boolean;
  }) => {
    if (!classItem || !summaries) return;

    // Create new summary from uploaded lesson
    const newSummary: SummaryItem = {
      id: lessonData.summaryId || uid(),
      classId: id,
      lessonId: lessonData.summaryId || uid(),
      lectureTitle: lessonData.title,
      summary: lessonData.isAudioTranscribed 
        ? "AI-generated summary from audio transcription is being processed. Check back soon for detailed content analysis."
        : (lessonData.description || "Summary will be generated from uploaded content."),
      topicsDiscussed: lessonData.isAudioTranscribed ? ["Audio content analysis in progress"] : [],
      learningObjectives: lessonData.isAudioTranscribed ? ["Content will be analyzed for learning objectives"] : [],
      homework: [],
      announcements: [],
      duration: 0,
      nextClassPreview: null,
      keyPoints: lessonData.isAudioTranscribed ? ["Audio transcription completed"] : [],
      studyQuestions: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    // Update summaries in state and localStorage
    const updatedSummaries = [...summaries, newSummary];
    setSummaries(updatedSummaries);

    // Log upload details
    if (lessonData.file) {
      console.log('File uploaded:', {
        filename: lessonData.file.name,
        isAudio: lessonData.isAudioTranscribed,
        summaryId: lessonData.summaryId,
        transcribed: lessonData.isAudioTranscribed
      });
    }
  };

  const filteredSummaries = useMemo(() => {
    const list = (summaries || []).filter((s) => {
      const matchesQuery = query.trim().length === 0 ||
        s.lectureTitle.toLowerCase().includes(query.trim().toLowerCase()) ||
        (s.summary || "").toLowerCase().includes(query.trim().toLowerCase());
      const matchesTab =
        tab === "all" ? true :
        tab === "homework" ? (Array.isArray(s.homework) && s.homework.some((h) => String(h).trim().length > 0)) :
        tab === "recent" ? true :
        true;
      return matchesQuery && matchesTab;
    });

    const recentCutoffMs = Date.now() - 1000 * 60 * 60 * 24 * 14; // 14 days
    const withRecent = tab === "recent" ? list.filter((s) => {
      const d = s.updatedAt || s.createdAt;
      return d ? new Date(d).getTime() >= recentCutoffMs : false;
    }) : list;

    const sorted = [...withRecent].sort((a, b) => {
      if (sortBy === "date_desc") {
        const da = new Date(a.updatedAt || a.createdAt || 0).getTime();
        const db = new Date(b.updatedAt || b.createdAt || 0).getTime();
        return db - da;
      }
      if (sortBy === "date_asc") {
        const da = new Date(a.updatedAt || a.createdAt || 0).getTime();
        const db = new Date(b.updatedAt || b.createdAt || 0).getTime();
        return da - db;
      }
      if (sortBy === "title_asc") {
        return a.lectureTitle.localeCompare(b.lectureTitle);
      }
      if (sortBy === "title_desc") {
        return b.lectureTitle.localeCompare(a.lectureTitle);
      }
      return 0;
    });

    return sorted;
  }, [summaries, query, tab, sortBy]);

  if (isLoading) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-10">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600"></div>
          <p className="ml-3 text-slate-600">Loading class details...</p>
        </div>
      </section>
    );
  }

  if (notFound) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-10">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h1 className="text-xl font-bold">Class not found</h1>
          <p className="text-slate-600 mt-2">We could not find this class. It may have been deleted.</p>
          <div className="mt-4">
            <Link href="/dashboard" className="text-sky-700 font-semibold hover:underline">Back to Dashboard</Link>
          </div>
        </div>
      </section>
    );
  }

  if (!classItem) {
    return (
      <section className="mx-auto max-w-3xl px-6 py-10">
        <p className="text-slate-600">Loading…</p>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-5xl px-6 py-10">
      <nav className="mb-6 text-sm text-slate-500">
        <Link href="/dashboard" className="inline-flex items-center gap-1 hover:text-slate-700">
          <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
          Back
        </Link>
        <span className="mx-2">/</span>
        <span className="text-slate-700">{classItem.name}</span>
      </nav>

      {/* Minimal layout: header/stats removed */}

      <div className="mt-8">
        {/* Toolbar + content view switch */}
        {canManage && showStudents ? (
          <div className="mt-4">
            <div className="flex items-center justify-between mb-3">
              <div className="text-sm text-slate-600">
                {studentsLoading ? 'Loading students…' : students ? `${students.length} student(s)` : ''}
              </div>
              <button
                type="button"
                onClick={() => setShowStudents(false)}
                className="inline-flex items-center gap-2 px-3 py-2 border border-slate-200 bg-white text-slate-700 rounded-lg hover:bg-slate-50 active:scale-[0.99] font-medium text-xs transition"
              >
                ← Back to Lessons
              </button>
            </div>
            <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
              {studentsError ? (
                <div className="p-4 text-rose-600 text-sm">{studentsError}</div>
              ) : studentsLoading ? (
                <div className="p-4 text-sm text-slate-600">Loading students…</div>
              ) : students && students.length > 0 ? (
                <table className="min-w-full divide-y divide-slate-200">
                  <thead className="bg-slate-50/50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">#</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Student</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">ID</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {(students || []).map((s, idx) => (
                      <tr key={s.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-2 align-top text-xs text-slate-600">{idx + 1}</td>
                        <td className="px-4 py-2 align-top text-sm text-slate-800">{s.name}</td>
                        <td className="px-4 py-2 align-top text-xs text-slate-600 break-all">{s.id}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <div className="p-4 text-sm text-slate-600">No students enrolled.</div>
              )}
            </div>
          </div>
        ) : !summaries || summaries.length === 0 ? (
          <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-10 text-center">
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-sky-50 text-sky-600 ring-1 ring-sky-100">
              <svg className="h-6 w-6" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            </div>
            <p className="text-base font-semibold mb-1 text-slate-900">No lessons yet</p>
            <p className="text-sm mb-6 text-slate-600">Start by uploading materials or recording a lecture to generate AI summaries.</p>
            {canManage && (
              <div className="relative inline-block" ref={emptyMenuRef}>
                <button
                  type="button"
                  onClick={() => setIsEmptyMenuOpen(!isEmptyMenuOpen)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-sky-600 text-white rounded-lg shadow-sm hover:bg-sky-700 active:scale-[0.99] font-medium text-sm transition"
                  aria-haspopup="menu"
                  aria-expanded={isEmptyMenuOpen}
                  aria-controls="empty-state-actions-menu"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add your first lesson
                  <svg className={`w-4 h-4 transition-transform ${isEmptyMenuOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {isEmptyMenuOpen && (
                  <div
                    id="empty-state-actions-menu"
                    role="menu"
                    aria-label="Add lesson actions"
                    className="absolute left-1/2 -translate-x-1/2 mt-2 w-64 bg-white rounded-xl shadow-lg border border-slate-200 z-10 overflow-hidden"
                  >
                    <button
                      role="menuitem"
                      onClick={handleUploadFile}
                      className="flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                    >
                      <svg className="h-5 w-5 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h5l2 3h11v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 7V5a2 2 0 0 1 2-2h3l2 2h3"/></svg>
                      <div>
                        <div className="font-medium text-slate-900">Upload files</div>
                        <div className="text-xs text-slate-500">Documents, videos, audio files</div>
                      </div>
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="mt-4">
            {/* Toolbar */}
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white p-1">
                <button
                  className={`px-3 py-1.5 text-xs font-medium rounded-md ${tab === 'all' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:text-slate-900'}`}
                  onClick={() => setTab('all')}
                >
                  All
                </button>
                <button
                  className={`px-3 py-1.5 text-xs font-medium rounded-md ${tab === 'homework' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:text-slate-900'}`}
                  onClick={() => setTab('homework')}
                >
                  With homework
                </button>
                <button
                  className={`px-3 py-1.5 text-xs font-medium rounded-md ${tab === 'recent' ? 'bg-slate-100 text-slate-900' : 'text-slate-600 hover:text-slate-900'}`}
                  onClick={() => setTab('recent')}
                >
                  Recent
                </button>
              </div>
              <div className="flex flex-1 md:flex-none items-center gap-2">
                <div className="relative w-full md:w-72">
                  <input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search lessons..."
                    className="w-full rounded-lg border border-slate-200 bg-white py-2 pl-9 pr-3 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
                  />
                  <svg className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                </div>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="rounded-lg border border-slate-200 bg-white py-2 px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
                >
                  <option value="date_desc">Newest first</option>
                  <option value="date_asc">Oldest first</option>
                  <option value="title_asc">Title A–Z</option>
                  <option value="title_desc">Title Z–A</option>
                </select>
                {canManage && (
                  <button
                    type="button"
                    onClick={openStudents}
                    className={`inline-flex items-center gap-2 px-3 py-2 border ${showStudents ? 'border-sky-300 bg-sky-50 text-sky-700' : 'border-slate-200 bg-white text-slate-700'} rounded-lg hover:bg-slate-50 active:scale-[0.99] font-medium text-xs transition`}
                  >
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                    Students{typeof (classItem?.students?.length) === 'number' ? ` (${classItem?.students?.length})` : ''}
                  </button>
                )}
                {canManage && (
                  <div className="relative" ref={actionMenuRef}>
                    <button
                      type="button"
                      onClick={() => setIsActionMenuOpen(!isActionMenuOpen)}
                      className="inline-flex items-center gap-2 px-3 py-2 bg-sky-600 text-white rounded-lg shadow-sm hover:bg-sky-700 active:scale-[0.99] font-medium text-xs transition"
                      aria-haspopup="menu"
                      aria-expanded={isActionMenuOpen}
                      aria-controls="lesson-actions-menu"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      New lesson
                      <svg className={`w-3.5 h-3.5 transition-transform ${isActionMenuOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    {isActionMenuOpen && (
                      <div
                        id="lesson-actions-menu"
                        role="menu"
                        aria-label="Lesson actions"
                        className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-lg border border-slate-200 z-10 overflow-hidden"
                      >
                        <button
                          role="menuitem"
                          onClick={handleUploadFile}
                          className="flex items-center gap-3 w-full px-4 py-3 text-left hover:bg-slate-50 transition-colors"
                        >
                          <svg className="h-5 w-5 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 7h5l2 3h11v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 7V5a2 2 0 0 1 2-2h3l2 2h3"/></svg>
                          <div>
                            <div className="font-medium text-slate-900">Upload files</div>
                            <div className="text-xs text-slate-500">Documents, videos, audio files</div>
                          </div>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>

            {/* Data Table */}
            <div className="mt-3 overflow-hidden rounded-2xl border border-slate-200 bg-white">
              <table className="min-w-full divide-y divide-slate-200">
                <thead className="bg-slate-50/50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Title</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-600">Created</th>
                    {canManage && (
                      <th className="px-4 py-3 text-right text-xs font-semibold text-slate-600">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredSummaries.length === 0 && (
                    <tr>
                      <td colSpan={canManage ? 3 : 2} className="px-4 py-10 text-center text-sm text-slate-500">No lessons match your filters.</td>
                    </tr>
                  )}
                  {filteredSummaries.map((summary) => (
                    <tr key={summary.lessonId} className="hover:bg-slate-50/60">
                      <td className="px-4 py-3 align-top">
                        <Link
                          href={`/dashboard/class_detail/${id}/lesson/${summary.lessonId}/chat`}
                          className="block w-full h-full"
                          prefetch
                          onMouseEnter={() => {
                            fetchSummaryById(id, summary.lessonId).catch(() => {});
                          }}
                        >
                          <div className="max-w-xs">
                            <span className="text-sm font-medium text-slate-900 hover:text-sky-700">
                              {summary.lectureTitle}
                            </span>
                            {summary.summary && (
                              <p className="mt-1 line-clamp-2 text-xs text-slate-500">{summary.summary}</p>
                            )}
                          </div>
                        </Link>
                      </td>
                      <td className="px-4 py-3 align-top text-xs text-slate-600">
                        {new Date(summary.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                      </td>
                      {canManage && (
                        <td className="px-4 py-3 align-top">
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => openDeleteConfirm(summary.lessonId, summary.lectureTitle)}
                              disabled={deletingId === summary.id}
                              className="inline-flex items-center gap-1 rounded-md border border-rose-200 bg-rose-50 px-2.5 py-1.5 text-xs font-medium text-rose-700 hover:bg-rose-100 disabled:opacity-60"
                              aria-label="Delete lesson"
                            >
                              {deletingId === summary.id ? (
                                <div className="w-3.5 h-3.5 border-2 border-rose-600 border-t-transparent rounded-full animate-spin"></div>
                              ) : (
                                <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/></svg>
                              )}
                              Delete
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Upload Modal */}
      {classItem && canManage && (
        <LessonUploadModal
          isOpen={isUploadModalOpen}
          onClose={() => setIsUploadModalOpen(false)}
          onUpload={handleLessonUpload}
          classCode={classItem.code}
          classId={id}
        />
      )}

      {/* Delete Confirmation Modal */}
      {canManage && isConfirmOpen && confirmTarget && (
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
              <h3 className="text-base font-semibold text-slate-800">Delete lesson</h3>
            </div>
            <div className="p-5">
              <p className="text-sm text-slate-600">
                Are you sure you want to delete “<span className="font-semibold">{confirmTarget.title}</span>”? This action is permanent and cannot be undone.
              </p>
            </div>
            <div className="p-5 pt-0 flex items-center justify-end gap-3">
              <button
                disabled={isConfirmDeleting}
                className="rounded-md border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                onClick={() => setIsConfirmOpen(false)}
              >
                Cancel
              </button>
              <button
                disabled={isConfirmDeleting}
                className="rounded-md bg-rose-600 px-4 py-2 text-sm font-semibold text-white hover:bg-rose-700 shadow-sm active:scale-95 disabled:opacity-60 flex items-center gap-2"
                onClick={handleDeleteLesson}
              >
                {isConfirmDeleting ? (
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

      {/* Students in-page view handled above */}
    </section>
  );
}
