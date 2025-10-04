# Lesson Deletion Guide

This guide explains how to delete lessons by class in the Pan Sea Backend API.

## Overview

The system provides functionality to delete all lessons associated with a specific class. This includes:
- Deleting lesson records from the database
- Removing audio files from S3 storage
- Cleaning up associated embeddings for semantic search
- Proper validation to ensure only class owners can delete lessons

## API Endpoints

### 1. Get Lessons Count by Class

**Endpoint:** `GET /api/v1/audio/lessons/class/{class_id}/count`

**Description:** Get the count of lessons for a specific class before deletion.

**Authentication:** Requires teacher authentication token.

**Parameters:**
- `class_id` (path): The ID of the class

**Response:**
```json
{
  "message": "Lessons count retrieved successfully",
  "data": {
    "class_id": "class-123",
    "lessons_count": 5
  }
}
```

### 2. Delete Individual Lesson

**Endpoint:** `DELETE /api/v1/audio/lessons/{lesson_id}`

**Description:** Delete a specific lesson by its ID.

**Authentication:** Requires teacher authentication token.

**Parameters:**
- `lesson_id` (path): The ID of the lesson to delete

**Response (Success):**
```json
{
  "message": "Lesson deleted successfully",
  "data": {
    "lesson_id": "lesson-123",
    "class_id": "class-456",
    "lecture_title": "Introduction to Physics",
    "deleted": true
  }
}
```

**Response (Not Found):**
```json
{
  "detail": "Lesson lesson-123 not found"
}
```

**Response (Access Denied):**
```json
{
  "detail": "You can only access classes you created"
}
```

## Usage Examples

### Using curl

1. **Get lessons count:**
```bash
curl -X GET "https://your-api-domain.com/api/v1/audio/lessons/class/class-123/count" \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN"
```

2. **Delete a specific lesson:**
```bash
curl -X DELETE "https://your-api-domain.com/api/v1/audio/lessons/lesson-123" \
  -H "Authorization: Bearer YOUR_TEACHER_TOKEN"
```

### Using Python requests

```python
import requests

# Configuration
API_BASE_URL = "https://your-api-domain.com/api/v1"
TEACHER_TOKEN = "your_teacher_token"
CLASS_ID = "class-123"

headers = {
    "Authorization": f"Bearer {TEACHER_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Get lessons count
count_response = requests.get(
    f"{API_BASE_URL}/audio/lessons/class/{CLASS_ID}/count",
    headers=headers
)
print("Lessons count:", count_response.json())

# 2. Delete a specific lesson
LESSON_ID = "lesson-123"
delete_response = requests.delete(
    f"{API_BASE_URL}/audio/lessons/{LESSON_ID}",
    headers=headers
)
print("Delete result:", delete_response.json())
```

### Using JavaScript/Fetch

```javascript
const API_BASE_URL = 'https://your-api-domain.com/api/v1';
const TEACHER_TOKEN = 'your_teacher_token';
const CLASS_ID = 'class-123';

const headers = {
  'Authorization': `Bearer ${TEACHER_TOKEN}`,
  'Content-Type': 'application/json'
};

// 1. Get lessons count
async function getLessonsCount() {
  const response = await fetch(
    `${API_BASE_URL}/audio/lessons/class/${CLASS_ID}/count`,
    { headers }
  );
  const data = await response.json();
  console.log('Lessons count:', data);
  return data;
}

// 2. Delete a specific lesson
const LESSON_ID = 'lesson-123';
async function deleteLesson() {
  const response = await fetch(
    `${API_BASE_URL}/audio/lessons/${LESSON_ID}`,
    { 
      method: 'DELETE',
      headers 
    }
  );
  const data = await response.json();
  console.log('Delete result:', data);
  return data;
}

// Usage
getLessonsCount().then(() => deleteLesson());
```

## What Gets Deleted

When you delete a lesson, the following are removed (in order):

1. **Lesson Summaries:**
   - Associated lesson summaries from the `lesson_summaries` table
   - This is deleted first to avoid foreign key constraint violations

2. **Embeddings:**
   - Vector embeddings used for semantic search
   - RAG (Retrieval-Augmented Generation) data for that lesson

3. **S3 Storage:**
   - The audio file stored in S3
   - Associated metadata

4. **Database Records:**
   - The specific lesson record from the `lessons` table
   - This is deleted last to maintain referential integrity

## Security & Validation

- **Teacher Authentication:** Only authenticated teachers can delete lessons
- **Class Ownership:** Teachers can only delete lessons from classes they own
- **Lesson Validation:** The system validates that the lesson exists before attempting deletion

## Error Handling

The API handles various error scenarios:

- **Lesson Not Found:** Returns 404 if the lesson doesn't exist
- **Access Denied:** Returns 403 if the teacher doesn't own the class
- **Class Not Found:** Returns 400 if the lesson has no associated class
- **Server Errors:** Returns 500 for unexpected errors

## Best Practices

1. **Verify Lesson ID:** Ensure you have the correct lesson ID before deletion
2. **Backup Important Data:** Consider backing up important lessons before deletion
3. **Handle Errors:** Check the response for any errors and handle them appropriately
4. **Use Proper Authentication:** Ensure you're using a valid teacher token

## Related Endpoints

- `GET /api/v1/audio/lessons/{class_id}` - Get all lessons for a class
- `DELETE /api/v1/audio/lessons/{lesson_id}` - Delete individual lesson (new endpoint)
- `DELETE /api/v1/audio/recordings/{audio_id}` - Delete individual lesson (legacy endpoint)
- `GET /api/v1/classes/{class_id}` - Get class information
