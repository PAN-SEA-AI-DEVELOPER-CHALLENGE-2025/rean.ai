interface RAGSearchRequest {
  query: string;
  class_id: string;
  limit?: number;
  similarity_threshold?: number;
}

interface RAGSearchResponse {
  id: string;
  similarity_score: number;
  transcription: string;
  full_transcription: string;
  class_id: string;
  created_at: string;
  class_title: string;
  subject: string;
  class_start_time: string;
}

interface LessonRAGResponse {
  answer: string;
  sources: Array<{
    id: string;
    content: string;
    metadata?: Record<string, unknown>;
    score?: number;
  }>;
  confidence?: number;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  confidence?: number;
  sources?: RAGSearchResponse[];
}

interface ChatResponse {
  answer: string;
  sources: RAGSearchResponse[];
  confidence: number;
}

class ChatService {
  private baseUrl = (process.env.NEXT_PUBLIC_API_URL_BASED || '').replace(/\/$/, '');

  /**
   * Calculate dynamic top_k based on lesson characteristics
   * @param lessonDuration - Duration in minutes
   * @param topicsCount - Number of topics in the lesson
   * @param questionComplexity - Simple analysis of question complexity
   */
  private calculateTopK(
    lessonDuration: number = 60, 
    topicsCount: number = 5, 
    questionComplexity: 'simple' | 'complex' = 'simple'
  ): number {
    let topK = 5; // Base value

    // Adjust based on lesson duration
    if (lessonDuration > 90) topK += 3;
    else if (lessonDuration > 60) topK += 2;
    else if (lessonDuration > 30) topK += 1;

    // Adjust based on topic complexity
    if (topicsCount > 10) topK += 2;
    else if (topicsCount > 6) topK += 1;

    // Adjust based on question complexity
    if (questionComplexity === 'complex') topK += 2;

    // Keep within reasonable bounds
    return Math.min(Math.max(topK, 3), 12);
  }

  /**
   * Analyze question complexity
   */
  private analyzeQuestionComplexity(question: string): 'simple' | 'complex' {
    const complexIndicators = [
      'explain', 'analyze', 'compare', 'contrast', 'evaluate', 'discuss',
      'relationship', 'connection', 'why', 'how does', 'what if',
      'implications', 'consequences', 'detailed', 'comprehensive'
    ];

    const lowercaseQuestion = question.toLowerCase();
    const hasComplexIndicators = complexIndicators.some(indicator => 
      lowercaseQuestion.includes(indicator)
    );

    return hasComplexIndicators ? 'complex' : 'simple';
  }

  async searchAudio(params: RAGSearchRequest): Promise<RAGSearchResponse[]> {
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const response = await fetch(`/api/rag/search/audio`, {
        method: 'POST',
        headers: {
          'accept': 'application/json',
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          query: params.query,
          class_id: params.class_id,
          limit: params.limit || 10,
          similarity_threshold: params.similarity_threshold || 0.7
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: RAGSearchResponse[] = await response.json();
      return data;
    } catch (error) {
      console.error('Error searching audio:', error);
      throw error;
    }
  }

  /**
   * Ask question about a specific lesson using the new RAG API
   */
  async askLessonQuestion(
    lessonId: string, 
    question: string, 
    lessonMetadata?: {
      duration?: number;
      topicsCount?: number;
    }
  ): Promise<LessonRAGResponse> {
    try {
      // Calculate dynamic top_k
      const questionComplexity = this.analyzeQuestionComplexity(question);
      const topK = this.calculateTopK(
        lessonMetadata?.duration || 60,
        lessonMetadata?.topicsCount || 5,
        questionComplexity
      );

      console.log(`RAG Query: "${question}" | Complexity: ${questionComplexity} | top_k: ${topK}`);

      const apiUrl = `/api/rag/lessons/${lessonId}/ask`;
      console.log(`Making request to: ${apiUrl}`);

      const token2 = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
          ...(token2 ? { Authorization: `Bearer ${token2}` } : {}),
        },
        body: JSON.stringify({
          question,
          top_k: topK
        })
      });

      console.log(`Response status: ${response.status}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('API Error Response:', errorData);
        throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
      }

      const data: LessonRAGResponse = await response.json();
      console.log('RAG Response:', data);
      return data;
    } catch (error) {
      console.error('Error asking lesson question:', error);
      if (error instanceof TypeError && error.message.includes('fetch failed')) {
        throw new Error('Unable to connect to the RAG API. Please check if the backend server is running.');
      }
      throw error;
    }
  }

  async getAnswer(query: string, classId: string): Promise<ChatResponse> {
    try {
      const searchResults = await this.searchAudio({
        query,
        class_id: classId,
        limit: 5,
        similarity_threshold: 0.7
      });

      if (searchResults.length === 0) {
        return {
          answer: "I couldn't find any relevant information about that topic in this class. Could you try rephrasing your question or asking about something else?",
          sources: [],
          confidence: 0
        };
      }

      // Get the best matching result
      const bestMatch = searchResults[0];
      const confidence = bestMatch.similarity_score;

      // Generate a contextual answer based on the transcription
      const answer = this.generateAnswer(query, bestMatch.transcription, confidence);

      return {
        answer,
        sources: searchResults,
        confidence
      };
    } catch (error) {
      console.error('Error getting answer:', error);
      throw new Error('Failed to get answer from the class content');
    }
  }

  /**
   * Get answer for a specific lesson using the new RAG API
   */
  async getLessonAnswer(
    lessonId: string, 
    query: string, 
    lessonMetadata?: {
      duration?: number;
      topicsCount?: number;
    }
  ): Promise<ChatResponse> {
    try {
      const ragResponse = await this.askLessonQuestion(lessonId, query, lessonMetadata);
      const rawSources = Array.isArray(ragResponse?.sources) ? ragResponse.sources : [];

      return {
        answer: ragResponse.answer,
        sources: rawSources.map(source => ({
          id: source.id,
          similarity_score: source.score || 0,
          transcription: source.content,
          full_transcription: source.content,
          class_id: '',
          created_at: '',
          class_title: '',
          subject: '',
          class_start_time: ''
        })),
        confidence: ragResponse?.confidence || 0
      };
    } catch (error) {
      console.error('Error getting lesson answer:', error);
      throw new Error('Failed to get answer from the lesson content');
    }
  }

  private generateAnswer(query: string, transcription: string, confidence: number): string {
    // Simple answer extraction logic
    // In a real implementation, you might want to use AI to generate better answers
    
    if (confidence < 0.6) {
      return `I found some information that might be related: "${transcription}" However, I'm not very confident this answers your question. Could you be more specific?`;
    }

    if (confidence < 0.8) {
      return `Based on the class content: "${transcription}"`;
    }

    // High confidence - provide a more direct answer
    return transcription;
  }

  // Create a new chat message
  createMessage(type: 'user' | 'assistant', content: string): ChatMessage {
    const id = (typeof crypto !== 'undefined' && 'randomUUID' in crypto)
      ? (crypto as any).randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    return {
      id,
      type,
      content,
      timestamp: new Date(),
      isLoading: false
    };
  }

  // Create a loading message
  createLoadingMessage(): ChatMessage {
    const id = (typeof crypto !== 'undefined' && 'randomUUID' in crypto)
      ? `loading-${(crypto as any).randomUUID()}`
      : `loading-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
    return {
      id,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      isLoading: true
    };
  }
}

export const chatService = new ChatService();
export type { ChatMessage, ChatResponse, RAGSearchResponse, LessonRAGResponse };
