#!/bin/bash

# RAG API Testing Examples
# Make sure the server is running: python -m uvicorn app.main:app --reload

BASE_URL="http://localhost:8000/api/v1/rag"
CLASS_ID="d7e7d890-202f-4af6-accc-4b1fcff4306b"  # Replace with actual class_id

echo "🧪 RAG API Testing Examples"
echo "=========================="

# Test 1: Audio Transcription Search
echo -e "\n1️⃣ Testing Audio Transcription Search"
echo "Query: biology cells DNA"
curl -X POST "${BASE_URL}/search/audio" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"biology cells DNA\",
    \"class_id\": \"${CLASS_ID}\",
    \"limit\": 5,
    \"similarity_threshold\": 0.7
  }" | jq '.'

# Test 2: Lecture Summary Search
echo -e "\n2️⃣ Testing Lecture Summary Search"
echo "Query: mathematics algebra"
curl -X POST "${BASE_URL}/search/summaries" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"mathematics algebra\",
    \"class_id\": \"${CLASS_ID}\",
    \"limit\": 5
  }" | jq '.'

# Test 3: Combined Search
echo -e "\n3️⃣ Testing Combined Search"
echo "Query: physics energy"
curl -X POST "${BASE_URL}/search/combined" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"physics energy\",
    \"class_id\": \"${CLASS_ID}\",
    \"subject\": \"physics\",
    \"limit\": 10,
    \"include_transcriptions\": true,
    \"include_summaries\": true
  }" | jq '.'

# Test 4: Get Audio by Class
echo -e "\n4️⃣ Testing Get Audio by Class"
curl -X POST "${BASE_URL}/audio/by-class" \
  -H "Content-Type: application/json" \
  -d "{
    \"class_id\": \"${CLASS_ID}\",
    \"limit\": 10
  }" | jq '.'

# Test 5: Test with different subjects
echo -e "\n5️⃣ Testing Different Subjects"

subjects=("biology" "chemistry" "physics" "mathematics" "history" "literature")

for subject in "${subjects[@]}"; do
  echo -e "\n🔬 Testing subject: $subject"
  curl -X POST "${BASE_URL}/search/audio" \
    -H "Content-Type: application/json" \
    -d "{
      \"query\": \"$subject concepts\",
      \"class_id\": \"${CLASS_ID}\",
      \"limit\": 3
    }" | jq '. | length'
done

# Test 6: Edge Cases
echo -e "\n6️⃣ Testing Edge Cases"

echo -e "\n📝 Empty query test:"
curl -X POST "${BASE_URL}/search/audio" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"\",
    \"class_id\": \"${CLASS_ID}\",
    \"limit\": 5
  }" | jq '.'

echo -e "\n📝 Invalid class_id test:"
curl -X POST "${BASE_URL}/search/audio" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"biology\",
    \"class_id\": \"invalid-class-id\",
    \"limit\": 5
  }" | jq '.'

echo -e "\n📝 Very specific query test:"
curl -X POST "${BASE_URL}/search/audio" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"mitochondria cellular respiration ATP energy production\",
    \"class_id\": \"${CLASS_ID}\",
    \"limit\": 5
  }" | jq '.'

echo -e "\n✅ API testing completed!"

