# RAG Chat Usage Examples

## How to Test the Dynamic top_k Feature

### Step 1: Navigate to a Lesson Chat
1. Go to http://localhost:3001
2. Navigate to any class dashboard
3. Click on a lesson to enter the chat interface

### Step 2: Test Different Question Types

#### Simple Questions (Expected top_k: 3-6)
```
- "What is this lesson about?"
- "Give me a summary"
- "What are the main topics?"
```

#### Complex Questions (Expected top_k: 7-12)
```
- "Explain the relationship between concept A and concept B"
- "How do these topics connect to real-world applications?"
- "Analyze the implications of what we learned"
- "Compare and contrast the different approaches discussed"
```

### Step 3: Monitor Console Output
Open browser developer tools and check the console for logs like:
```
RAG Query: "Explain the relationship between..." | Complexity: complex | top_k: 10
```

### Step 4: Observe Response Quality
- **Higher top_k**: More comprehensive answers with more sources
- **Lower top_k**: Focused, concise answers
- **Source Attribution**: See which parts of the lesson informed each answer
- **Confidence Scores**: Understand how certain the AI is about its response

## Example API Calls

### Simple Question
```bash
curl -X 'POST' \
  'http://localhost:3001/api/rag/lessons/YOUR_LESSON_ID/ask' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "What is the main topic?"
  }'
```

### Complex Question
```bash
curl -X 'POST' \
  'http://localhost:3001/api/rag/lessons/YOUR_LESSON_ID/ask' \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "Explain the relationship between the concepts discussed and their practical applications"
  }'
```

## Expected Behavior

### For a 30-minute lesson with 3 topics:
- Simple question: top_k = 4
- Complex question: top_k = 6

### For a 90-minute lesson with 8 topics:
- Simple question: top_k = 8  
- Complex question: top_k = 10

### For a 120-minute lesson with 12 topics:
- Simple question: top_k = 10
- Complex question: top_k = 12 (max cap)

The system automatically optimizes retrieval based on lesson characteristics and question complexity!
