#!/usr/bin/env python3
"""
Test script to verify RAG search functionality
"""
import asyncio
import json
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import rag_service

async def test_rag_search():
    try:
        # Test search for audio transcriptions
        print("=== Testing Audio Transcription Search ===")
        audio_results = await rag_service.search_audio_transcriptions(
            query="biology cells DNA",
            class_id="d7e7d890-202f-4af6-accc-4b1fcff4306b",
            limit=5
        )
        print(f"Found {len(audio_results)} audio transcription results")
        for i, result in enumerate(audio_results[:2]):  # Show first 2
            print(f"  {i+1}. Similarity: {result.get('similarity_score', 0):.3f}")
            print(f"     Lecture: {result.get('lecture_title', 'N/A')}")
            print(f"     Excerpt: {result.get('transcription', '')[:100]}...")
            print()
        
        # Test search for lecture summaries
        print("=== Testing Lecture Summary Search ===")
        summary_results = await rag_service.search_lecture_summaries(
            query="biology cells DNA",
            class_id="d7e7d890-202f-4af6-accc-4b1fcff4306b",
            limit=5
        )
        print(f"Found {len(summary_results)} lecture summary results")
        for i, result in enumerate(summary_results[:2]):  # Show first 2
            print(f"  {i+1}. Similarity: {result.get('similarity_score', 0):.3f}")
            print(f"     Class: {result.get('class_title', 'N/A')}")
            print(f"     Summary: {result.get('summary', '')[:100]}...")
            print()
        
        # Test combined search
        print("=== Testing Combined Search ===")
        combined_results = await rag_service.search_combined(
            query="biology cells DNA",
            class_id="d7e7d890-202f-4af6-accc-4b1fcff4306b",
            limit=6
        )
        print(f"Combined results: {len(combined_results['combined'])} total")
        print(f"  - Transcriptions: {len(combined_results['transcriptions'])}")
        print(f"  - Summaries: {len(combined_results['summaries'])}")
        
        for i, result in enumerate(combined_results['combined'][:3]):  # Show first 3
            print(f"  {i+1}. Type: {result.get('type', 'unknown')}")
            print(f"     Similarity: {result.get('similarity_score', 0):.3f}")
            if result.get('type') == 'transcription':
                print(f"     Content: {result.get('transcription', '')[:80]}...")
            else:
                print(f"     Content: {result.get('summary', '')[:80]}...")
            print()
        
    except Exception as e:
        print(f'Error: {str(e)}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_search())
