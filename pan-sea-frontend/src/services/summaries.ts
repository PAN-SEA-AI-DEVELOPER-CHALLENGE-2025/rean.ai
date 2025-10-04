import { apiFetch, ApiError } from '@/lib/http';
import { ApiSummary, SummaryItem } from '@/types/api';

// Define possible response formats
type SummariesResponse = 
  | ApiSummary[] 
  | { data: ApiSummary[] } 
  | { items: ApiSummary[] };

// Convert API summary to frontend SummaryItem format
function safeParseStringArray(value: unknown): string[] {
  // Already an array
  if (Array.isArray(value)) {
    return value.map((v) => String(v)).filter(Boolean);
  }

  // Try JSON parsing when value is a string
  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return [];
    try {
      const parsed = JSON.parse(trimmed);
      if (Array.isArray(parsed)) {
        return parsed.map((v) => String(v)).filter(Boolean);
      }
    } catch {
      // Not JSON – fall back to splitting heuristics (newline, bullets, commas, semicolons, dashes)
      return trimmed
        .split(/\r?\n|\u2022|•|,|;| - | -| -|^-|\s-\s|\s*\d+\.|\s*\*\s*/)
        .map((s) => s.trim())
        .filter(Boolean);
    }
  }

  // Default
  return [];
}

export function transformApiSummaryToSummaryItem(apiSummary: ApiSummary): SummaryItem {
  const topicsDiscussed = Array.isArray(apiSummary.topics_discussed)
    ? apiSummary.topics_discussed
    : safeParseStringArray((apiSummary as unknown as Record<string, unknown>).topics_discussed);

  const learningObjectives = Array.isArray(apiSummary.learning_objectives)
    ? apiSummary.learning_objectives
    : safeParseStringArray((apiSummary as unknown as Record<string, unknown>).learning_objectives);

  const homework = Array.isArray(apiSummary.homework)
    ? apiSummary.homework
    : safeParseStringArray((apiSummary as unknown as Record<string, unknown>).homework);

  const announcements = Array.isArray(apiSummary.announcements)
    ? apiSummary.announcements
    : safeParseStringArray((apiSummary as unknown as Record<string, unknown>).announcements);

  const keyPoints = safeParseStringArray(apiSummary.key_points);
  const studyQuestions = safeParseStringArray(apiSummary.study_questions);

  return {
    id: apiSummary.id,
    classId: apiSummary.class_id,
    lessonId: (apiSummary as any).lesson_id || apiSummary.id,
    summary: apiSummary.summary,
    topicsDiscussed,
    learningObjectives,
    homework,
    announcements,
    duration: apiSummary.duration,
    nextClassPreview: apiSummary.next_class_preview,
    createdAt: apiSummary.created_at,
    updatedAt: apiSummary.updated_at,
    keyPoints,
    studyQuestions,
    lectureTitle: apiSummary.lecture_title || `Untitled Lecture - ${new Date(apiSummary.created_at).toLocaleDateString()}`,
  };
}

export async function fetchSummaries(classId: string, skip = 0, limit = 100): Promise<SummaryItem[]> {
  try {
    console.log(`Fetching summaries for class: ${classId} with skip: ${skip}, limit: ${limit}`);
    const response = await apiFetch<SummariesResponse>(
      `/summaries/class/${classId}?skip=${skip}&limit=${limit}`,
      { ttlMs: 60000 }
    );
    
    console.log('Raw summaries API response:', response);
    console.log('Response type:', typeof response);
    console.log('Is array:', Array.isArray(response));
    
    // Handle different possible response formats
    let apiSummaries: ApiSummary[];
    
    if (Array.isArray(response)) {
      // Direct array response
      apiSummaries = response as ApiSummary[];
    } else if ('data' in response && Array.isArray(response.data)) {
      // Wrapped in data property
      apiSummaries = response.data;
    } else if ('items' in response && Array.isArray(response.items)) {
      // Paginated response
      apiSummaries = response.items;
    } else {
      console.error('Unexpected response format:', response);
      throw new Error('Unexpected response format from API');
    }
    
    console.log('Extracted summaries array:', apiSummaries);
    const transformedSummaries = apiSummaries.map(transformApiSummaryToSummaryItem);
    console.log('Transformed summaries:', transformedSummaries);
    
    return transformedSummaries;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      // No summaries yet for this class
      return [];
    }
    console.error('Error fetching summaries:', error);
    throw error;
  }
}

export async function fetchSummaryById(classId: string, summaryId: string): Promise<SummaryItem | null> {
  try {
    // Prefer a direct lesson endpoint if available
    const response = await apiFetch<SummariesResponse>(
      `/summaries/lesson/${summaryId}?skip=0&limit=1`,
      { ttlMs: 60000 }
    );

    let apiSummaries: ApiSummary[] = [];
    if (Array.isArray(response)) {
      apiSummaries = response as ApiSummary[];
    } else if ('data' in response && Array.isArray(response.data)) {
      apiSummaries = response.data;
    } else if ('items' in response && Array.isArray(response.items)) {
      apiSummaries = response.items;
    }

    const found = apiSummaries[0];
    if (found) {
      return transformApiSummaryToSummaryItem(found);
    }

    // Fallback to fetching by class and filtering by lessonId or id
    const summaries = await fetchSummaries(classId);
    return summaries.find(summary => summary.lessonId === summaryId || summary.id === summaryId) || null;
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      console.warn('No summary found for lesson. Falling back to class summaries.');
    } else {
      console.error('Error fetching summary:', error);
    }
    // Fallback in case of lesson endpoint failure
    try {
      const summaries = await fetchSummaries(classId);
      return summaries.find(summary => summary.lessonId === summaryId || summary.id === summaryId) || null;
    } catch {
      return null;
    }
  }
}
