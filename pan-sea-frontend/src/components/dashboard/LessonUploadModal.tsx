"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { uploadService } from '@/services/upload';
import { SUBJECT_OPTIONS } from '@/lib/subjects';

const AUDIO_TYPES = [
  'audio/mpeg',
  'audio/mp3',
  'audio/wav',
  'audio/ogg',
  'audio/webm',
  'audio/m4a',
  'audio/aac',
  'audio/flac'
];

const AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.webm', '.m4a', '.aac', '.flac'];
const MATERIAL_INDEXES = [0, 1, 2];

type LessonUploadModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onUpload: (lessonData: {
    title: string;
    description: string;
    file: File | null;
    dateTime: string;
    summaryId?: string;
    isAudioTranscribed?: boolean;
  }) => void;
  classCode: string;
  classId: string;
};

export default function LessonUploadModal({ 
  isOpen, 
  onClose, 
  onUpload, 
  classCode,
  classId
}: LessonUploadModalProps) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [dateTime, setDateTime] = useState('');
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'processing' | 'completed' | 'error'>('idle');
  const [summaryId, setSummaryId] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [language, setLanguage] = useState<string>('khmer');
  const [lessonSubject, setLessonSubject] = useState<string>('');
  const [materials, setMaterials] = useState<File[]>([]);
  const materialInputsRef = useRef<Array<HTMLInputElement | null>>([null, null, null]);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const lastProgressRef = useRef(0);
  const rafIdRef = useRef<number | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !file || isUploading) return;

    setIsUploading(true);
    setUploadStatus('uploading');
    setUploadProgress(0);
    setErrorMessage(null);
    
    try {
      // Require audio file (API expects audio + optional materials)
      if (!file || !isAudioFile(file)) {
        throw new Error('Please select an audio file (MP3, WAV, OGG, WEBM, M4A, AAC, FLAC).');
      }
      // If it's an audio file, use the upload service for transcription
      if (file && isAudioFile(file)) {
        // Validate file size before upload
        const maxSize = 50 * 1024 * 1024; // 50MB
        if (file.size > maxSize) {
          throw new Error(`File too large. Maximum size is 50MB. Current file size: ${Math.round(file.size / (1024 * 1024))}MB. Please compress your audio file.`);
        }
        // Validate required fields for audio processing API
        if (!language.trim() || !lessonSubject.trim()) {
          throw new Error('Please fill in Language and Subject for audio uploads.');
        }
        // Validate materials (max 3, allowed types)
        const allowedMaterialExt = ['.pdf', '.ppt', '.pptx', '.docx', '.txt'];
        if (materials.length > 3) {
          throw new Error('You can attach up to 3 materials (PDF, PPT/PPTX, DOCX, TXT).');
        }
        for (const m of materials) {
          const lower = (m?.name || '').toLowerCase();
          if (!allowedMaterialExt.some(ext => lower.endsWith(ext))) {
            throw new Error('Invalid material type. Allowed: PDF, PPT, PPTX, DOCX, TXT.');
          }
        }
        const response = await uploadService.uploadAudio(
          file,
          classId,
          (progress) => {
            const pct = progress.percentage;
            if (pct === lastProgressRef.current) return;
            if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
            rafIdRef.current = requestAnimationFrame(() => {
              lastProgressRef.current = pct;
              setUploadProgress(pct);
              if (pct === 100) {
                setUploadStatus('processing');
              }
            });
          },
          {
            lecture_title: title.trim() || `${classCode} • ${file.name}`,
            language: language.trim(),
            subject: lessonSubject.trim(),
            materials: materials
          }
        );

        if (response.success) {
          setSummaryId(response.summary_id || null);
          setUploadStatus('completed');
          
          // Call the original onUpload with enhanced data (for UI state update only)
          try {
            await onUpload({
              title: title.trim(),
              description: description.trim(),
              file,
              dateTime: dateTime || new Date().toISOString(),
              summaryId: response.summary_id,
              isAudioTranscribed: true
            });
          } catch (uiError) {
            console.log('UI update completed, ignoring any UI errors:', uiError);
          }
        } else {
          throw new Error(response.error || 'Upload failed');
        }
      }
      
      // Reset form after short delay to show success
      setTimeout(() => {
        setTitle('');
        setDescription('');
        setFile(null);
        setDateTime('');
        setUploadProgress(0);
        setUploadStatus('idle');
        setSummaryId(null);
        setErrorMessage(null);
        setLanguage('khmer');
        setLessonSubject('');
        setMaterials([]);
        materialInputsRef.current.forEach((el) => { if (el) el.value = ''; });
        onClose();
      }, 2000);
      
    } catch (error) {
      console.error('Upload failed:', error);
      setUploadStatus('error');
      
      // Store the error message for display
      const errorMessage = error instanceof Error ? error.message : 'Upload failed. Please try again.';
      console.error('Upload error details:', errorMessage);
      setErrorMessage(errorMessage);
    } finally {
      setIsUploading(false);
    }
  };

  const isAudioFile = useCallback((file: File): boolean => {
    return AUDIO_TYPES.includes(file.type) || AUDIO_EXTENSIONS.some(ext => 
      file.name.toLowerCase().endsWith(ext)
    );
  }, []);

  const formattedFileSize = useMemo(() => {
    return file ? uploadService.formatFileSize(file.size) : '';
  }, [file]);

  useEffect(() => {
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, []);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    setFile(selectedFile);
    
    // Auto-generate title from filename if title is empty
    if (selectedFile && !title.trim()) {
      const filename = selectedFile.name;
      const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.')) || filename;
      setTitle(`${classCode} • ${nameWithoutExt}`);
    }
  }, [classCode, title]);

  // Drag and drop handlers
  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
    
    const droppedFiles = e.dataTransfer.files;
    if (droppedFiles.length > 0) {
      const selectedFile = droppedFiles[0];
      setFile(selectedFile);
      
      // Auto-generate title from filename if title is empty
      if (!title.trim()) {
        const filename = selectedFile.name;
        const nameWithoutExt = filename.substring(0, filename.lastIndexOf('.')) || filename;
        setTitle(`${classCode} • ${nameWithoutExt}`);
      }
    }
  }, [classCode, title]);

  const handleClose = useCallback(() => {
    // Reset all states
    setTitle('');
    setDescription('');
    setFile(null);
    setDateTime('');
    setUploadProgress(0);
    setUploadStatus('idle');
    setSummaryId(null);
    setIsDragOver(false);
    setErrorMessage(null);
    setMaterials([]);
    if (materialInputsRef && materialInputsRef.current) {
      materialInputsRef.current.forEach((el) => { if (el) el.value = ''; });
    }
    
    onClose();
  }, [onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex" role="dialog" aria-modal="true" aria-labelledby="lesson-upload-title">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm" onClick={!isUploading ? handleClose : undefined} />
      {/* Sheet */}
      <div className="relative ml-auto h-full w-full bg-white shadow-xl flex flex-col">
        {/* Header */}
        <div className="sticky top-0 z-10 border-b border-slate-200 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
          <div className="mx-auto max-w-6xl px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-sky-600 text-white">
                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 5 17 10"/><line x1="12" y1="5" x2="12" y2="20"/></svg>
              </div>
              <div>
                <h2 id="lesson-upload-title" className="text-lg font-semibold text-slate-900">Add New Lesson</h2>
                <p className="text-xs text-slate-500">{classCode} • Audio will be auto-transcribed for summary</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="inline-flex h-8 w-8 items-center justify-center rounded-md text-slate-500 hover:text-slate-700 hover:bg-slate-100"
              aria-label="Close modal"
              disabled={isUploading}
            >
              <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="mx-auto w-full max-w-6xl flex-1 overflow-y-auto px-6">
          {errorMessage && (
            <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
              <div className="flex items-start gap-2">
                <svg className="mt-0.5 h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                <span>{errorMessage}</span>
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 py-6">
            {/* Left: Dropzone and helper */}
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Audio File *
                </label>
                <div 
                  className={`border-2 border-dashed rounded-xl p-6 text-center transition-all duration-200 cursor-pointer ${
                    isDragOver
                      ? 'border-sky-400 bg-sky-50'
                      : 'border-slate-300 hover:border-slate-400'
                  } ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}
                  onDragEnter={handleDragEnter}
                  onDragLeave={handleDragLeave}
                  onDragOver={handleDragOver}
                  onDrop={handleDrop}
                >
                  <input
                    type="file"
                    onChange={handleFileChange}
                    accept=".mp3,.wav,.ogg,.webm,.m4a,.aac,.flac,audio/*"
                    className="hidden"
                    id="file-upload"
                    ref={fileInputRef}
                    disabled={isUploading}
                  />
                  <label htmlFor="file-upload" className="cursor-pointer block" aria-label="Upload lesson file">
                    <div className="text-slate-600">
                      {file ? (
                        <div>
                          <div className="flex items-center justify-center mb-2">
                            {isAudioFile(file) ? (
                              <div className="w-12 h-12 bg-sky-100 rounded-full flex items-center justify-center">
                                <svg className="h-6 w-6 text-sky-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>
                              </div>
                            ) : (
                              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center">
                                <svg className="h-6 w-6 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                              </div>
                            )}
                          </div>
                          <div className="text-slate-900 font-medium text-sm">{file.name}</div>
                          <div className="text-xs text-slate-500 mt-1">
                            {formattedFileSize}
                            {isAudioFile(file) && (
                              <span className="ml-2 px-2 py-1 bg-sky-100 text-sky-700 rounded-full text-xs">
                                Audio - Will be transcribed
                              </span>
                            )}
                          </div>

                          {uploadStatus === 'uploading' && (
                            <div className="mt-3">
                              <div className="w-full bg-slate-200 rounded-full h-2">
                                <div 
                                  className="bg-sky-600 h-2 rounded-full transition-all duration-300"
                                  style={{ width: `${uploadProgress}%` }}
                                />
                              </div>
                              <div className="text-xs text-slate-500 mt-1">
                                Uploading... {uploadProgress}%
                              </div>
                            </div>
                          )}

                          {uploadStatus === 'processing' && (
                            <div className="mt-3">
                              <div className="flex items-center justify-center space-x-2">
                                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-sky-600"></div>
                                <span className="text-xs text-sky-600">
                                  Processing transcription... This may take several minutes for longer audio files.
                                </span>
                              </div>
                            </div>
                          )}

                          {uploadStatus === 'completed' && summaryId && (
                            <div className="mt-3 p-2 bg-sky-50 border border-sky-200 rounded">
                              <div className="flex items-center gap-2 text-xs text-sky-700">
                                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
                                <span>Transcription completed! Summary ID: {summaryId}</span>
                              </div>
                            </div>
                          )}

                          {uploadStatus === 'error' && (
                            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded">
                              <div className="flex items-center gap-2 text-xs text-red-700">
                                <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                                <span>Upload failed. Please try again.</span>
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="py-2">
                          <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-slate-100">
                            <svg className="h-6 w-6 text-slate-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 5 17 10"/><line x1="12" y1="5" x2="12" y2="20"/></svg>
                          </div>
                          <div className="text-base font-medium">Click to upload or drag and drop</div>
                          <div className="text-sm text-slate-600 mt-2">
                            <strong>Audio:</strong> MP3, WAV, OGG, WEBM, M4A, AAC, FLAC (auto-transcribed)
                          </div>
                          <div className="text-xs text-slate-500 mt-2">
                            Max size: 50MB
                          </div>
                        </div>
                      )}
                    </div>
                  </label>
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">Materials (optional, max 3)</label>
                  <div className="space-y-2">
                    {MATERIAL_INDEXES.map((idx) => (
                      <div key={idx} className="flex items-center gap-2">
                        {!materials[idx] ? (
                          <input
                            type="file"
                            accept=".pdf,.ppt,.pptx,.docx,.txt"
                            className="block w-full text-sm text-slate-700 file:mr-3 file:rounded-md file:border file:border-slate-300 file:bg-white file:px-3 file:py-1.5 hover:file:bg-slate-50"
                            ref={(el) => { materialInputsRef.current[idx] = el; }}
                            onChange={(e) => {
                              const f = e.target.files?.[0];
                              setMaterials((prev) => {
                                const next = [...prev];
                                if (f) {
                                  next[idx] = f;
                                } else {
                                  next.splice(idx, 1);
                                }
                                return next.filter(Boolean).slice(0,3);
                              });
                            }}
                            disabled={isUploading}
                          />
                        ) : (
                          <div className="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs text-slate-700 shadow-sm">
                            <svg className="h-3.5 w-3.5 text-slate-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                            <span className="truncate max-w-[160px]" title={materials[idx].name}>{materials[idx].name}</span>
                            <button
                              type="button"
                              className="inline-flex h-5 w-5 items-center justify-center rounded hover:bg-rose-50 text-slate-400 hover:text-rose-600"
                              aria-label="Remove material"
                              onClick={() => {
                                setMaterials((prev) => {
                                  const next = [...prev];
                                  next.splice(idx, 1);
                                  return next;
                                });
                                const el = materialInputsRef.current[idx];
                                if (el) el.value = '';
                              }}
                              disabled={isUploading}
                            >
                              <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                    <p className="text-xs text-slate-500">PDF, PPT/PPTX, DOCX, TXT</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 mt-4">
                  <div className="mt-0.5 inline-flex h-6 w-6 items-center justify-center rounded-full bg-sky-100 text-sky-700">
                    <svg className="h-3.5 w-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4 12.5-12.5z"/></svg>
                  </div>
                  <div className="text-sm text-slate-600">
                    <div className="font-medium text-slate-800">Tips</div>
                    Clear titles and subjects help generate better summaries.
                  </div>
                </div>
              </div>
            </div>

            {/* Right: Form */}
            <div>
              <form id="lesson-upload-form" onSubmit={handleSubmit} className="space-y-4">
                {/* Title */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Lesson Title *
                  </label>
                  <input
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder={`${classCode} • Lesson Title`}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-600 focus:border-sky-600"
                    required
                    disabled={isUploading}
                  />
                </div>

                {/* Language and Subject (for audio processing) */}
                <div className="grid sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Language {file && isAudioFile(file) && <span className="text-red-500">*</span>}
                    </label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-600 focus:border-sky-600"
                      disabled={isUploading}
                    >
                      <option value="khmer">Khmer</option>
                      <option value="english">English</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-2">
                      Subject {file && isAudioFile(file) && <span className="text-red-500">*</span>}
                    </label>
                    <select
                      value={lessonSubject}
                      onChange={(e) => setLessonSubject(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-600 focus:border-sky-600"
                      disabled={isUploading}
                    >
                      <option value="">Select subject</option>
                      {SUBJECT_OPTIONS.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Description
                  </label>
                  <textarea
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of the lesson content..."
                    rows={3}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-600 focus:border-sky-600"
                    disabled={isUploading}
                  />
                </div>

                {/* Date Time */}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-2">
                    Lesson Date & Time
                  </label>
                  <input
                    type="datetime-local"
                    value={dateTime}
                    onChange={(e) => setDateTime(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-sky-600 focus:border-sky-600"
                    disabled={isUploading}
                  />
                  {!dateTime && (
                    <p className="text-xs text-slate-500 mt-1">Leave blank to use current date/time</p>
                  )}
                </div>
              </form>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 border-t border-slate-200 bg-white/80 backdrop-blur supports-[backdrop-filter]:bg-white/60">
          <div className="mx-auto max-w-6xl px-6 py-4 flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
            <div className="text-xs text-slate-500">
              Make sure your file complies with class policy before uploading.
            </div>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleClose}
                className="px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium"
                disabled={isUploading}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => {
                  fileInputRef.current?.click();
                }}
                className="hidden sm:inline-flex px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 font-medium"
                disabled={isUploading}
              >
                Choose file
              </button>
              <button
                type="submit"
                form="lesson-upload-form"
                disabled={!title.trim() || !file || isUploading || uploadStatus === 'completed'}
                className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 font-medium disabled:bg-slate-300 disabled:cursor-not-allowed"
              >
                {uploadStatus === 'uploading' ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Uploading... {uploadProgress}%
                  </div>
                ) : uploadStatus === 'processing' ? (
                  <div className="flex items-center justify-center gap-2">
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Processing transcription...
                  </div>
                ) : uploadStatus === 'completed' ? (
                  <div className="flex items-center justify-center gap-2">
                    <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6L9 17l-5-5"/></svg>
                    Upload Complete
                  </div>
                ) : uploadStatus === 'error' ? (
                  'Retry Upload'
                ) : (
                  'Upload Lesson'
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
