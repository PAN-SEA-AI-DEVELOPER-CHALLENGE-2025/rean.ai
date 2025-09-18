# RAG Chat Implementation

## Overview
This implementation adds a new lesson-specific RAG (Retrieval-Augmented Generation) chat functionality that allows users to ask questions about specific lessons and get contextually relevant answers.

## Key Features

### 1. Dynamic top_k Calculation
The system automatically calculates the optimal `top_k` parameter based on:
- **Lesson Duration**: Longer lessons get more retrieved chunks
- **Topic Complexity**: More topics discussed = higher top_k
- **Question Complexity**: Complex questions get more context

```typescript
private calculateTopK(
  lessonDuration: number = 60, 
  topicsCount: number = 5, 
  questionComplexity: 'simple' | 'complex' = 'simple'
): number
```

### 2. Question Complexity Analysis
The system analyzes questions to determine if they need more context:

**Complex Question Indicators:**
- explain, analyze, compare, contrast, evaluate, discuss
- relationship, connection, why, how does, what if
- implications, consequences, detailed, comprehensive

### 3. New API Endpoints

#### `/api/rag/lessons/[lessonId]/ask`
- **Method**: POST
- **Body**: 
  ```json
  {
    "question": "string",
    "top_k": "number (calculated dynamically)"
  }
  ```
- **Response**:
  ```json
  {
    "answer": "string",
    "sources": [
      {
        "id": "string",
        "content": "string",
        "score": "number"
      }
    ],
    "confidence": "number"
  }
  ```

## Usage

### Frontend Integration

1. **In Chat Service** (`services/chat.ts`):
```typescript
const ragResponse = await chatService.getLessonAnswer(
  lessonId, 
  query, 
  {
    duration: lesson.duration,
    topicsCount: lesson.topicsDiscussed.length
  }
);
```

2. **In Chat Page** (`/lesson/[lessonId]/chat`):
The chat automatically uses the new RAG system for all user questions.

## Example Dynamic top_k Calculation

### Scenario 1: Short, Simple Lesson
- Duration: 30 minutes
- Topics: 3
- Question: "What is the main topic?"
- **Result**: top_k = 4

### Scenario 2: Long, Complex Lesson  
- Duration: 120 minutes
- Topics: 12
- Question: "Explain the relationship between concepts A and B"
- **Result**: top_k = 10

### Scenario 3: Standard Lesson
- Duration: 60 minutes
- Topics: 6
- Question: "How does this apply to real-world scenarios?"
- **Result**: top_k = 8

## UI Improvements

### Enhanced Chat Messages
- **Confidence Scores**: Shows RAG confidence percentage
- **Source Display**: Shows relevant chunks that informed the answer
- **Better Loading**: Indicates RAG analysis is happening

### Performance Optimizations
- Dynamic top_k reduces unnecessary processing for simple questions
- Context-aware chunk retrieval improves answer quality
- Source attribution helps users understand answer origin

## Configuration

The system can be tuned by adjusting the constants in `calculateTopK()`:

```typescript
// Base values
let topK = 5; // Starting point

// Duration adjustments
if (lessonDuration > 90) topK += 3;
else if (lessonDuration > 60) topK += 2;
else if (lessonDuration > 30) topK += 1;

// Topic complexity
if (topicsCount > 10) topK += 2;
else if (topicsCount > 6) topK += 1;

// Question complexity
if (questionComplexity === 'complex') topK += 2;

// Bounds: min=3, max=12
return Math.min(Math.max(topK, 3), 12);
```

## Testing

To test the implementation:

1. Navigate to any lesson chat page
2. Ask various types of questions:
   - Simple: "What is the main topic?"
   - Complex: "Explain the relationship between the concepts discussed"
3. Observe the dynamic top_k values in browser console
4. Check answer quality and source attribution

## Backend API Compatibility

The frontend proxies requests to the backend API:
```
Frontend: /api/rag/lessons/[lessonId]/ask
Backend: http://localhost:8000/api/v1/rag/lessons/[lessonId]/ask
```

Ensure the backend API is running and accessible for full functionality.
