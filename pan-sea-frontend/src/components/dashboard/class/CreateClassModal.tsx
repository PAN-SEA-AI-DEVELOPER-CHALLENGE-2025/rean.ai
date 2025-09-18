"use client";

import { useState } from "react";
import { CreateClassRequest } from "@/services/classes";
import { SUBJECT_OPTIONS } from "@/lib/subjects";

interface CreateClassModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreate: (classData: CreateClassRequest) => void;
}

export default function CreateClassModal({ isOpen, onClose, onCreate }: CreateClassModalProps) {
  const [form, setForm] = useState({
    class_code: "",
    subject: "",
    grade: "",
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const clearForm = () => {
    setForm({
      class_code: "",
      subject: "",
      grade: "",
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isSubmitting) return;
    
    // Validation
    const required = ["class_code", "subject", "grade"] as const;
    for (const key of required) {
      if (!form[key]?.trim()) {
        alert(`Please fill in ${key.replace('_', ' ')}.`);
        return;
      }
    }

    setIsSubmitting(true);

    try {
      const newClassData: CreateClassRequest = {
        class_code: form.class_code.trim(),
        subject: form.subject.trim(),
        grade: form.grade.trim(),
        teacher_id: "auto", // Will be set by the parent component
        student_ids: [],
      };

      await onCreate(newClassData);
      clearForm();
      onClose();
    } catch (error) {
      console.error('Error creating class:', error);
      alert('Failed to create class. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    clearForm();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in-up"
    >
      {/* Enhanced backdrop with blur effect */}
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={handleClose}
        aria-hidden="true"
      />
      
      {/* Modal container with enhanced styling */}
      <div className="relative w-full max-w-xl rounded-3xl bg-white shadow-2xl border border-slate-200/50 animate-bounce-in">
        {/* Header with gradient background */}
        <div className="relative p-8 border-b border-slate-200/50 bg-gradient-to-r from-sky-50 to-emerald-50 rounded-t-3xl">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-blue-500 flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.746 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <div>
                <h2 className="text-2xl font-bold text-slate-800">Create New Class</h2>
                <p className="text-slate-600 text-sm mt-1">Enter class code, subject and grade</p>
              </div>
            </div>
            <button
              aria-label="Close"
              onClick={handleClose}
              className="rounded-xl p-2 hover:bg-white/50 transition-all duration-200 group"
            >
              <svg className="w-5 h-5 text-slate-500 group-hover:text-slate-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Form content */}
        <form onSubmit={handleSubmit} className="p-8 space-y-6">
          {/* Class Code and Subject */}
          <div className="grid sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label htmlFor="class_code" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                Class Code
                <span className="text-red-500">*</span>
              </label>
              <input
                id="class_code"
                value={form.class_code}
                onChange={(e) => setForm((f) => ({ ...f, class_code: e.target.value }))}
                placeholder="e.g., BIG HUG COOK"
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 transition-all duration-200 bg-slate-50/50 hover:bg-white"
                required
                disabled={isSubmitting}
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="subject" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                Subject
                <span className="text-red-500">*</span>
              </label>
              <select
                id="subject"
                value={form.subject}
                onChange={(e) => setForm((f) => ({ ...f, subject: e.target.value }))}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all duration-200 bg-slate-50/50 hover:bg-white"
                required
                disabled={isSubmitting}
              >
                <option value="" disabled>Select a subject</option>
                {SUBJECT_OPTIONS.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Grade */}
          <div className="grid sm:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label htmlFor="grade" className="text-sm font-semibold text-slate-700 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-orange-500"></span>
                Grade
                <span className="text-red-500">*</span>
              </label>
              <select
                id="grade"
                value={form.grade}
                onChange={(e) => setForm((f) => ({ ...f, grade: e.target.value }))}
                className="w-full rounded-xl border border-slate-300 px-4 py-3 outline-none focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all duration-200 bg-slate-50/50 hover:bg-white"
                required
                disabled={isSubmitting}
              >
                <option value="" disabled>Select grade</option>
                <option value="7">7</option>
                <option value="8">8</option>
                <option value="9">9</option>
                <option value="10">10</option>
                <option value="11">11</option>
                <option value="12">12</option>
              </select>
            </div>
          </div>

          {/* Action buttons */}
          <div className="flex items-center justify-end gap-4 pt-6 border-t border-slate-200">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-xl border border-slate-300 px-6 py-3 font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition-all duration-200"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="rounded-xl bg-blue-500  hover:bg-blue-600 text-white px-8 py-3 font-semibold shadow-lg hover:shadow-xl disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Creating Class...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  Create Class
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
