import { apiFetch } from '@/lib/http';
import { ApiClass, ClassItem, ApiStudent, StudentItem } from '@/types/api';

// Convert API class to frontend ClassItem format
export function transformApiClassToClassItem(apiClass: any): ClassItem {
  // Support flexible API shapes: prefer title, fallback to class_code/name
  const title: string = apiClass?.title ?? apiClass?.class_code ?? apiClass?.name ?? 'Untitled Class';
  const subject: string = apiClass?.subject ?? '';
  const classroom: string = apiClass?.classroom ?? apiClass?.room ?? '';
  const teacherName: string = apiClass?.teacher_name ?? apiClass?.teacherName ?? apiClass?.teacher?.name ?? '';
  const grade: string | undefined = apiClass?.grade ?? undefined;

  // Schedule if start/end provided; otherwise omit
  let schedule: string | undefined = undefined;
  const startRaw = apiClass?.start_time ?? apiClass?.startTime ?? null;
  const endRaw = apiClass?.end_time ?? apiClass?.endTime ?? null;
  if (startRaw && endRaw) {
    const startTime = new Date(startRaw);
    const endTime = new Date(endRaw);
    const formatTime = (date: Date) => date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    schedule = `${startTime.toLocaleDateString('en-US', { weekday: 'short' })} • ${formatTime(startTime)}–${formatTime(endTime)}`;
  }

  return {
    id: apiClass.id,
    code: (apiClass?.class_code ?? subject ?? 'CLS').toString().toUpperCase(),
    name: title,
    faculty: teacherName || classroom || undefined,
    grade,
    schedule,
    color: getRandomColor(),
    students: Array.isArray(apiClass?.students) ? apiClass.students : undefined,
  };
}

// Helper function to get random colors for classes
function getRandomColor(): string {
  const colors = [
    'bg-blue-100 text-blue-800',
    'bg-green-100 text-green-800', 
    'bg-purple-100 text-purple-800',
    'bg-pink-100 text-pink-800',
    'bg-indigo-100 text-indigo-800',
    'bg-yellow-100 text-yellow-800',
    'bg-red-100 text-red-800',
    'bg-teal-100 text-teal-800'
  ];
  return colors[Math.floor(Math.random() * colors.length)];
}

// Define possible response formats
type ClassesResponse = 
  | ApiClass[] 
  | { data: ApiClass[] } 
  | { items: ApiClass[] };

export async function fetchClasses(teacherId: string, limit = 50): Promise<ClassItem[]> {
  try {
    console.log(`Fetching classes for teacher: ${teacherId} with limit: ${limit}`);
    const response = await apiFetch<ClassesResponse>(
      `/classes/teacher/${teacherId}?limit=${limit}`,
      { ttlMs: 60000 }
    );
    
    console.log('Raw API response:', response);
    console.log('Response type:', typeof response);
    console.log('Is array:', Array.isArray(response));
    
    // Handle different possible response formats
    let apiClasses: ApiClass[];
    
    if (Array.isArray(response)) {
      // Direct array response
      apiClasses = response;
    } else if ('data' in response && Array.isArray(response.data)) {
      // Wrapped in data property
      apiClasses = response.data;
    } else if ('items' in response && Array.isArray(response.items)) {
      // Paginated response
      apiClasses = response.items;
    } else {
      console.error('Unexpected response format:', response);
      throw new Error('Unexpected response format from API');
    }
    
    console.log('Extracted classes array:', apiClasses);
    const transformedClasses = apiClasses.map(transformApiClassToClassItem);
    console.log('Transformed classes:', transformedClasses);
    
    return transformedClasses;
  } catch (error) {
    console.error('Error fetching classes:', error);
    throw error;
  }
}

// Fetch classes a student is enrolled in
type StudentClassesResponse = ClassesResponse;

export async function fetchStudentClasses(limit = 50, offset = 0): Promise<ClassItem[]> {
  try {
    const response = await apiFetch<StudentClassesResponse>(
      `/student/classes?limit=${limit}&offset=${offset}`,
      { ttlMs: 60000 }
    );

    let apiClasses: ApiClass[];
    if (Array.isArray(response)) {
      apiClasses = response;
    } else if ('data' in response && Array.isArray(response.data)) {
      apiClasses = response.data;
    } else if ('items' in response && Array.isArray(response.items)) {
      apiClasses = response.items;
    } else {
      throw new Error('Unexpected response format from API');
    }

    return apiClasses.map(transformApiClassToClassItem);
  } catch (error) {
    console.error('Error fetching student classes:', error);
    throw error;
  }
}

export async function fetchClassById(classId: string): Promise<ClassItem | null> {
  try {
    const apiClass = await apiFetch<ApiClass>(`/classes/${classId}`, { ttlMs: 60000 });
    return transformApiClassToClassItem(apiClass);
  } catch (error) {
    console.error('Error fetching class:', error);
    return null;
  }
}

export async function fetchClassStudents(classId: string): Promise<string[]> {
  try {
    const apiClass = await apiFetch<ApiClass>(`/classes/${classId}`, { ttlMs: 30000 });
    return Array.isArray(apiClass?.students) ? apiClass.students : [];
  } catch (error) {
    console.error('Error fetching class students:', error);
    return [];
  }
}

export async function fetchClassStudentProfiles(classId: string): Promise<StudentItem[]> {
  try {
    // Prefer dedicated students endpoint if available
    try {
      const students = await apiFetch<ApiStudent[] | { data: ApiStudent[] } | { items: ApiStudent[] }>(
        `/classes/${classId}/students`,
        { ttlMs: 30000 }
      );
      const array = Array.isArray(students)
        ? students
        : 'data' in (students as any) && Array.isArray((students as any).data)
        ? (students as any).data
        : 'items' in (students as any) && Array.isArray((students as any).items)
        ? (students as any).items
        : [];
      return array.map(transformApiStudentToStudentItem);
    } catch {
      // Fallback: fetch class and resolve IDs only
      const ids = await fetchClassStudents(classId);
      return ids.map((id) => ({ id, name: id }));
    }
  } catch (error) {
    console.error('Error fetching class student profiles:', error);
    return [];
  }
}

function transformApiStudentToStudentItem(apiStudent: ApiStudent): StudentItem {
  const name = apiStudent.name || apiStudent.full_name || apiStudent.username || apiStudent.email || 'Unknown';
  return { id: apiStudent.id, name };
}

export interface CreateClassRequest {
  class_code: string;
  subject: string;
  grade: string;
  teacher_id: string;
  student_ids?: string[];
}

export async function createClass(classData: CreateClassRequest): Promise<ClassItem> {
  try {
    console.log('Creating class:', classData);
    const apiClass = await apiFetch<any>('/classes/', {
      method: 'POST',
      body: classData
    });
    
    console.log('Class created:', apiClass);
    return transformApiClassToClassItem(apiClass);
  } catch (error) {
    console.error('Error creating class:', error);
    throw error;
  }
}

export async function deleteClass(classId: string): Promise<void> {
  try {
    await apiFetch<void>(`/classes/${classId}`, {
      method: 'DELETE',
    });
  } catch (error) {
    console.error('Error deleting class:', error);
    throw error;
  }
}