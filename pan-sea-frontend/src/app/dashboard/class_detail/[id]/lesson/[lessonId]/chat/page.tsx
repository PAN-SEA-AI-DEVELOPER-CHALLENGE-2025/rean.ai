"use client";

import { useEffect, useRef, useState, use } from "react";
import { 
  FaArrowLeft, 
  FaBook, 
  FaBullseye, 
  FaClipboardList, 
  FaQuestionCircle, 
  FaListAlt, 
  FaLightbulb, 
  FaChevronDown 
} from "react-icons/fa";
import Link from "next/link";
import ChatMessage from "@/components/dashboard/chat/ChatMessage";
import ChatInput from "@/components/dashboard/chat/ChatInput";
import { fetchSummaryById } from "@/services/summaries";
import { SummaryItem } from "@/types/api";
import { chatService } from "@/services/chat";

type UiChatMessage = {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isLoading?: boolean;
  confidence?: number;
  sources?: string[];
};

function toUiMessage(msg: { id: string; type: 'user' | 'assistant'; content: string; timestamp: Date; isLoading?: boolean }): UiChatMessage {
  return {
    id: msg.id,
    type: msg.type,
    content: msg.content,
    timestamp: msg.timestamp,
    isLoading: msg.isLoading,
  };
}

export default function LessonChatPage({ 
  params 
}: { 
  params: Promise<{ id: string; lessonId: string }> 
}) {
  const { id: classId, lessonId } = use(params);
  const [summary, setSummary] = useState<SummaryItem | null>(null);
  const [messages, setMessages] = useState<UiChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingSummary, setIsLoadingSummary] = useState(true);
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);
  const [shownSections, setShownSections] = useState<Record<string, boolean>>({});

  const listContainerRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    async function loadSummary() {
      try {
        setIsLoadingSummary(true);
        const summaryData = await fetchSummaryById(classId, lessonId);
        setSummary(summaryData);
        
        if (summaryData) {
          // Create initial AI message with lesson context
          const initialMessage = chatService.createMessage(
            'assistant',
            `Hi! I'm here to help you with "${summaryData.lectureTitle}". 

I have all the details about this lecture including:
📚 Topics discussed: ${summaryData.topicsDiscussed.join(', ')}
🎯 Learning objectives: ${summaryData.learningObjectives.join(', ')}
${summaryData.homework.length > 0 ? `📝 Homework: ${summaryData.homework.join(', ')}` : ''}

Click the buttons below to view specific sections, or ask me anything about this lecture!`
          );
          setMessages([toUiMessage(initialMessage)]);
        }
      } catch (error) {
        console.error('Error loading summary:', error);
      } finally {
        setIsLoadingSummary(false);
      }
    }

    loadSummary();
  }, [classId, lessonId]);

  const addSectionMessage = (sectionType: string) => {
    if (!summary) return;

    // Prevent duplicate section messages
    if (shownSections[sectionType]) return;

    let content = '';
    switch (sectionType) {
      case 'summary':
        content = `📋 **Full Lecture Summary**

${summary.summary}

Duration: ${Math.round(summary.duration / 60) || 'N/A'} minutes
Date: ${new Date(summary.createdAt).toLocaleDateString()}`;
        break;
        
      case 'topics':
        content = `📚 **Topics Discussed**

${summary.topicsDiscussed.map((topic, index) => `${index + 1}. ${topic}`).join('\n')}

${summary.topicsDiscussed.length} topics covered in this lecture.`;
        break;
        
      case 'objectives':
        content = `🎯 **Learning Objectives**

${summary.learningObjectives.map((obj) => `✓ ${obj}`).join('\n')}

Focus on mastering these ${summary.learningObjectives.length} key objectives.`;
        break;
        
      case 'keypoints':
        if (summary.keyPoints.length > 0) {
          content = `💡 **Key Points**

${summary.keyPoints.map((point) => `• ${point}`).join('\n')}

These are the most important takeaways from the lecture.`;
        } else {
          content = `💡 **Key Points**

No specific key points were highlighted for this lecture. The main focus areas are covered in the topics discussed above.`;
        }
        break;
        
      case 'homework':
        if (summary.homework.length > 0) {
          content = `📝 **Homework Assignments**

${summary.homework.map((hw, index) => `${index + 1}. ${hw}`).join('\n')}

${summary.homework.length} assignment(s) to complete.`;
        } else {
          content = `📝 **Homework Assignments**

No homework has been assigned for this lecture. Focus on reviewing the key concepts and topics discussed.`;
        }
        break;
        
      case 'questions':
        if (summary.studyQuestions.length > 0) {
          content = `❓ **Study Questions**

${summary.studyQuestions.map((q, index) => `Q${index + 1}: ${q}`).join('\n')}

Use these questions to test your understanding of the material.`;
        } else {
          content = `❓ **Study Questions**

Here are some questions to help you review:
Q1: What are the main concepts covered in "${summary.lectureTitle}"?
Q2: How do the topics discussed relate to each other?
Q3: What are the practical applications of what we learned?`;
        }
        break;
        
      default:
        return;
    }

    const newMessage = chatService.createMessage('assistant', content);

    setMessages(prev => [...prev, toUiMessage(newMessage)]);
    setShownSections(prev => ({ ...prev, [sectionType]: true }));
  };

  // Keyboard shortcuts for quick navigation to sections
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const active = document.activeElement as HTMLElement | null;
      const isTyping = active && (active.tagName === 'INPUT' || active.tagName === 'TEXTAREA' || active.getAttribute('contenteditable') === 'true');
      if (isTyping) return;
      if (!summary) return;

      const key = e.key.toLowerCase();
      if (key === 's') { e.preventDefault(); addSectionMessage('summary'); }
      if (key === 't') { e.preventDefault(); addSectionMessage('topics'); }
      if (key === 'o') { e.preventDefault(); addSectionMessage('objectives'); }
      if (key === 'h') { e.preventDefault(); addSectionMessage('homework'); }
      if (key === 'q') { e.preventDefault(); addSectionMessage('questions'); }
      if (key === 'k') { e.preventDefault(); addSectionMessage('keypoints'); }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [summary]);

  // Auto scroll to bottom behavior
  useEffect(() => {
    if (!autoScrollEnabled) return;
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }
  }, [messages, autoScrollEnabled]);

  // Track scroll to toggle the floating button
  useEffect(() => {
    const container = listContainerRef.current;
    if (!container) return;

    const onScroll = () => {
      const nearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 48;
      setShowScrollToBottom(!nearBottom);
      setAutoScrollEnabled(nearBottom);
    };

    container.addEventListener('scroll', onScroll, { passive: true });
    // Run once to initialize
    onScroll();
    return () => container.removeEventListener('scroll', onScroll);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = chatService.createMessage('user', inputValue);
    const currentQuery = inputValue;
    
    setMessages(prev => [...prev, toUiMessage(userMessage)]);
    setInputValue("");
    setIsLoading(true);

    // Add loading message
    const loadingMessage = chatService.createLoadingMessage();
    setMessages(prev => [...prev, toUiMessage(loadingMessage)]);

    try {
      // Check if user wants to see pre-defined summary sections
      const query = currentQuery.toLowerCase();
      if ((query.includes('summary') || query.includes('overview')) && summary) {
        // Remove loading message and add summary
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
        addSectionMessage('summary');
        setIsLoading(false);
        return;
      }

      if (query.includes('topic') && query.includes('what') && summary) {
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
        addSectionMessage('topics');
        setIsLoading(false);
        return;
      }

      if (query.includes('objective') && summary) {
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
        addSectionMessage('objectives');
        setIsLoading(false);
        return;
      }

      if (query.includes('homework') && summary) {
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
        addSectionMessage('homework');
        setIsLoading(false);
        return;
      }

      // Use lesson-based RAG API for direct questions
      const lessonMetadata = {
        duration: summary?.duration || 60,
        topicsCount: summary?.topicsDiscussed.length || 5
      };

      try {
        const chatResponse = await chatService.getLessonAnswer(
          lessonId, 
          currentQuery, 
          lessonMetadata
        );

        // Remove loading message
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
        
        // Create AI response with RAG data
        const aiMessage: UiChatMessage = {
          ...toUiMessage(chatService.createMessage('assistant', chatResponse.answer)),
          sources: chatResponse.sources.map(source => source.transcription)
        };
        
        setMessages(prev => [...prev, aiMessage]);
      } catch (ragError) {
        console.error('RAG API Error:', ragError);
        
        // Remove loading message
        setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
        
        // Fallback to old class-based RAG or generic response
        try {
          const fallbackResponse = await chatService.getAnswer(currentQuery, classId);
          const aiMessage: UiChatMessage = {
            ...toUiMessage(chatService.createMessage('assistant', fallbackResponse.answer)),
            sources: fallbackResponse.sources.map(source => source.transcription)
          };
          setMessages(prev => [...prev, aiMessage]);
        } catch (fallbackError) {
          console.error('Fallback API Error:', fallbackError);
          
          // Final fallback to offline response
          const offlineMessage = chatService.createMessage(
            'assistant', 
            `I'm having trouble connecting to the lesson content right now. This might be because:

1. **Backend API not running**: Make sure the RAG API server is running on http://localhost:8000
2. **Network connectivity**: Check your internet connection
3. **API configuration**: Verify the RAG_API_URL_BASED environment variable

**Meanwhile, here's what I can tell you about "${summary?.lectureTitle}":**

📚 **Topics**: ${summary?.topicsDiscussed.join(', ') || 'No topics available'}
🎯 **Objectives**: ${summary?.learningObjectives.join(', ') || 'No objectives available'}
⏱️ **Duration**: ${Math.round((summary?.duration || 0) / 60) || 'N/A'} minutes

Try asking again in a moment, or use the quick navigation buttons above to explore specific sections.`
          );
          setMessages(prev => [...prev, toUiMessage(offlineMessage)]);
        }
      }
      
    } catch (error) {
      console.error('Error getting AI response:', error);
      
      // Remove loading message
      setMessages(prev => prev.filter(msg => msg.id !== loadingMessage.id));
      
      // Fallback to mock response
      const fallbackMessage = chatService.createMessage(
        'assistant', 
        "I'm sorry, I'm having trouble accessing the lecture content right now. Please try again in a moment, or use the quick action buttons above to access specific sections."
      );
      setMessages(prev => [...prev, toUiMessage(fallbackMessage)]);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoadingSummary) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sky-600 mx-auto"></div>
          <p className="mt-3 text-slate-600">Loading lesson...</p>
        </div>
      </div>
    );
  }

  if (!summary) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <h1 className="text-2xl font-bold text-slate-900 mb-2">Lesson not found</h1>
          <p className="text-slate-600 mb-4">We couldn't find this lesson. It may have been removed or the link is incorrect.</p>
          <Link
            href={`/dashboard/class_detail/${classId}`}
            className="inline-flex items-center px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 transition-colors"
          >
            ← Back to Class
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white flex flex-col">
      {/* Header */}
      <div className="bg-white/80 border-b border-slate-200/70 px-6 py-4 sticky top-0 z-30 backdrop-blur supports-[backdrop-filter]:bg-white/70">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-3">
              <Link
                href={`/dashboard/class_detail/${classId}`}
                className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-800 transition-colors"
              >
                <FaArrowLeft className="w-5 h-5" />
                <span className="text-sm">Back to Class</span>
              </Link>
              <div className="h-4 w-px bg-slate-200" />
              <div>
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">{summary.lectureTitle}</h1>
                <p className="text-sm text-slate-500">
                  Duration: {Math.round(summary.duration / 60) || 'N/A'} min • {new Date(summary.createdAt).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
          <button
            onClick={() => addSectionMessage('summary')}
            className="px-4 py-2 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-lg hover:from-sky-100 hover:to-blue-100 transition-colors text-sm font-medium inline-flex items-center gap-2 ring-1 ring-blue-100"
          >
            <FaListAlt className="w-4 h-4" />
            View Summary
          </button>
        </div>
      </div>

      {/* Sticky Navigator */}
      {summary && (
        <div className="bg-white/80 border-b border-slate-200/70 sticky top-[64px] z-20 backdrop-blur supports-[backdrop-filter]:bg-white/70">
          <div className="max-w-4xl mx-auto px-6 py-2">
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-xs text-slate-500 mr-1">Jump to:</span>
              <button
                onClick={() => addSectionMessage('topics')}
                className="px-3 py-1.5 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-md hover:from-sky-100 hover:to-blue-100 transition-colors text-xs font-medium inline-flex items-center gap-1.5 ring-1 ring-blue-100"
                title="Shortcut: T"
              >
                <FaBook className="w-3.5 h-3.5" />
                Topics
              </button>
              <button
                onClick={() => addSectionMessage('objectives')}
                className="px-3 py-1.5 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-md hover:from-sky-100 hover:to-blue-100 transition-colors text-xs font-medium inline-flex items-center gap-1.5 ring-1 ring-blue-100"
                title="Shortcut: O"
              >
                <FaBullseye className="w-3.5 h-3.5" />
                Objectives
              </button>
              {summary.homework.length > 0 && (
                <button
                  onClick={() => addSectionMessage('homework')}
                  className="px-3 py-1.5 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-md hover:from-sky-100 hover:to-blue-100 transition-colors text-xs font-medium inline-flex items-center gap-1.5 ring-1 ring-blue-100"
                  title="Shortcut: H"
                >
                  <FaClipboardList className="w-3.5 h-3.5" />
                  Homework
                </button>
              )}
              <button
                onClick={() => addSectionMessage('questions')}
                className="px-3 py-1.5 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-md hover:from-sky-100 hover:to-blue-100 transition-colors text-xs font-medium inline-flex items-center gap-1.5 ring-1 ring-blue-100"
                title="Shortcut: Q"
              >
                <FaQuestionCircle className="w-3.5 h-3.5" />
                Questions
              </button>
              <button
                onClick={() => addSectionMessage('summary')}
                className="px-3 py-1.5 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-md hover:from-sky-100 hover:to-blue-100 transition-colors text-xs font-medium inline-flex items-center gap-1.5 ring-1 ring-blue-100"
                title="Shortcut: S"
              >
                <FaListAlt className="w-3.5 h-3.5" />
                Summary
              </button>
              {summary.keyPoints.length > 0 && (
                <button
                  onClick={() => addSectionMessage('keypoints')}
                  className="px-3 py-1.5 bg-gradient-to-br from-sky-50 to-blue-50 text-blue-700 rounded-md hover:from-sky-100 hover:to-blue-100 transition-colors text-xs font-medium inline-flex items-center gap-1.5 ring-1 ring-blue-100"
                  title="Shortcut: K"
                >
                  <FaLightbulb className="w-3.5 h-3.5" />
                  Key Points
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      

      {/* Chat Messages */}
      <div ref={listContainerRef} className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
          {messages.map((message) => (
            <ChatMessage key={message.id} message={message} />
          ))}
          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Scroll to bottom button */}
      {showScrollToBottom && (
        <div className="fixed bottom-28 right-6 z-30">
          <button
            onClick={() => {
              setAutoScrollEnabled(true);
              if (messagesEndRef.current) messagesEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'end' });
            }}
            className="shadow-lg px-3 py-2 rounded-full bg-gradient-to-br from-blue-600 to-indigo-600 text-white text-xs hover:from-blue-700 hover:to-indigo-700"
            aria-label="Scroll to bottom"
          >
            <span className="inline-flex items-center gap-2">
              <FaChevronDown className="w-4 h-4" />
              New messages
            </span>
          </button>
        </div>
      )}

      {/* Chat Input */}
      <ChatInput
        inputValue={inputValue}
        onInputChange={setInputValue}
        onSubmit={handleSubmit}
        isLoading={isLoading}
        placeholder={`Ask me anything about "${summary.lectureTitle}"...`}
      />
    </div>
  );
}

