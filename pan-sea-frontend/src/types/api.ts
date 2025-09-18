export interface ApiClass {
  id: string;
  title: string;
  subject: string;
  start_time: string;
  end_time: string;
  classroom: string;
  grade: string;
  teacher_id: string;
  teacher_name?: string;
  status: 'scheduled' | 'ongoing' | 'completed' | 'cancelled';
  duration: number;
  created_at: string;
  updated_at: string;
  students: string[];
}

export interface ClassItem {
  id: string;
  code: string;
  name: string;
  faculty?: string;
  grade?: string;
  schedule?: string;
  color?: string;
  students?: string[];
}

export interface ApiStudent {
  id: string;
  name?: string;
  full_name?: string;
  username?: string;
  email?: string;
}

export interface StudentItem {
  id: string;
  name: string;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiLesson {
  lecture_title: string | null;
  id?: string;
  created_at?: string;
  duration?: number;
  status?: string;
}

export interface LessonItem {
  id: string;
  title: string;
  content?: string;
  datetime: string;
  duration?: number;
  status?: string;
}

export interface ApiSummary {
  id: string;
  class_id: string;
  summary: string;
  lesson_id?: string;
  topics_discussed: string[];
  learning_objectives: string[];
  homework: string[];
  announcements: string[];
  duration: number;
  next_class_preview: string | null;
  created_at: string;
  updated_at: string;
  key_points: string;
  study_questions: string;
  lecture_title: string | null;
}

export interface SummaryItem {
  id: string;
  classId: string;
  lessonId: string;
  summary: string;
  topicsDiscussed: string[];
  learningObjectives: string[];
  homework: string[];
  announcements: string[];
  duration: number;
  nextClassPreview: string | null;
  createdAt: string;
  updatedAt: string;
  keyPoints: string[];
  studyQuestions: string[];
  lectureTitle: string;
}

// Profile payload
export interface ProfileUser {
  id: string;
  full_name: string;
  email: string;
  role: string;
}

export interface ProfileClassItem {
  id: string;
  subject: string;
  teacher_id: string;
  duration: number | null;
  grade: string | null;
  created_at: string;
  updated_at: string;
  class_code: string;
  teacher_name: string;
  teacher_email: string;
  students: string[];
}

export interface ProfileResponse {
  user: ProfileUser;
  classes: ProfileClassItem[];
}