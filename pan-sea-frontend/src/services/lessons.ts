import { apiFetch, ApiError } from '@/lib/http';
import { ApiLesson, LessonItem } from '@/types/api';

// Define possible response formats
type LessonsResponse = 
  | ApiLesson[] 
  | { data: ApiLesson[] } 
  | { items: ApiLesson[] };

// Convert API lesson to frontend LessonItem format
export function transformApiLessonToLessonItem(apiLesson: ApiLesson, index: number): LessonItem {
  return {
    id: apiLesson.id || `lesson-${index}`,
    title: apiLesson.lecture_title || `Untitled Lesson ${index + 1}`,
    content: apiLesson.lecture_title ? `Lecture content for ${apiLesson.lecture_title}` : 'No content available',
    datetime: apiLesson.created_at || new Date().toISOString(),
    duration: apiLesson.duration || 0,
    status: apiLesson.status || 'completed'
  };
}

export async function fetchLessons(classId: string, limit: number = 100, offset: number = 0): Promise<LessonItem[]> {
  async function requestAndTransform(endpoint: string): Promise<LessonItem[]> {
    const response = await apiFetch<LessonsResponse>(endpoint, { ttlMs: 60000 });
    let apiLessons: ApiLesson[];
    if (Array.isArray(response)) {
      apiLessons = response as ApiLesson[];
    } else if ('data' in (response as any) && Array.isArray((response as any).data)) {
      apiLessons = (response as any).data as ApiLesson[];
    } else if ('items' in (response as any) && Array.isArray((response as any).items)) {
      apiLessons = (response as any).items as ApiLesson[];
    } else {
      console.error('Unexpected lessons response format:', response);
      throw new Error('Unexpected response format from API');
    }
    return apiLessons.map((lesson, index) => transformApiLessonToLessonItem(lesson, index));
  }

  try {
    console.log(`Fetching lessons (classes endpoint) for class: ${classId}`);
    // Primary endpoint
    return await requestAndTransform(`/classes/${encodeURIComponent(classId)}/lessons/list?limit=${encodeURIComponent(String(limit))}&offset=${encodeURIComponent(String(offset))}`);
  } catch (err) {
    // Fallback to older audio endpoint on 404/400 or generic errors
    const isApiErr = err instanceof ApiError;
    if (isApiErr && (err.status === 404 || err.status === 400)) {
      try {
        console.warn('Primary lessons endpoint not found; falling back to /audio/lessons');
        return await requestAndTransform(`/audio/lessons/${encodeURIComponent(classId)}?skip=${encodeURIComponent(String(offset))}&limit=${encodeURIComponent(String(limit))}`);
      } catch (fallbackErr) {
        console.error('Fallback lessons endpoint failed:', fallbackErr);
        throw fallbackErr;
      }
    }
    console.error('Error fetching lessons:', err);
    throw err;
  }
}

export async function fetchLessonById(classId: string, lessonId: string): Promise<LessonItem | null> {
  try {
    // For now, get all lessons and find the specific one
    const lessons = await fetchLessons(classId);
    return lessons.find(lesson => lesson.id === lessonId) || null;
  } catch (error) {
    console.error('Error fetching lesson:', error);
    return null;
  }
}

export async function deleteLesson(classId: string, lessonId: string): Promise<void> {
  try {
    // Try DELETE /audio/lessons/{lessonId}
    await apiFetch<void>(`/audio/lessons/${encodeURIComponent(lessonId)}`, {
      method: 'DELETE',
    });
    return;
  } catch (error) {
    // Fall back to DELETE /audio/lessons/{classId}?lesson_id={lessonId}
    const shouldFallback =
      (error instanceof ApiError && (error.status === 400 || error.status === 422)) ||
      (error as any)?.message?.toString()?.toLowerCase()?.includes('lesson_id');
    if (shouldFallback) {
      await apiFetch<void>(`/audio/lessons/${encodeURIComponent(classId)}?lesson_id=${encodeURIComponent(lessonId)}`, {
        method: 'DELETE',
      });
      return;
    }
    console.error('Error deleting lesson:', error);
    throw error;
  }
}
