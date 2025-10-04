#!/usr/bin/env python3
"""
Improved RAG testing script with better error handling and database setup
"""
import asyncio
import json
import sys
import os
import logging
from typing import List, Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import rag_service
from app.database.database import db_manager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_database_connection():
    """Check if database is accessible and tables exist"""
    try:
        # Test basic connection
        result = await db_manager.execute_query("SELECT 1 as test")
        logger.info("✅ Database connection successful")
        
        # Check if required tables exist
        tables_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('lessons', 'lesson_summaries', 'classes')
        """
        tables = await db_manager.execute_query(tables_query)
        existing_tables = [row['table_name'] for row in tables] if tables else []
        
        logger.info(f"📊 Found tables: {existing_tables}")
        
        if 'lessons' not in existing_tables:
            logger.warning("⚠️  'lessons' table not found - RAG search will not work")
        if 'lesson_summaries' not in existing_tables:
            logger.warning("⚠️  'lesson_summaries' table not found - summary search will not work")
        if 'classes' not in existing_tables:
            logger.warning("⚠️  'classes' table not found - class info will not be available")
            
        return existing_tables
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return []

async def check_sample_data():
    """Check if there's sample data to test with"""
    try:
        # Check lessons with transcriptions
        lessons_query = """
            SELECT COUNT(*) as count 
            FROM lessons 
            WHERE transcription IS NOT NULL AND transcription != ''
        """
        lessons_result = await db_manager.execute_query(lessons_query)
        lessons_count = lessons_result[0]['count'] if lessons_result else 0
        
        # Check lessons with embeddings
        embeddings_query = """
            SELECT COUNT(*) as count 
            FROM lessons 
            WHERE embedding IS NOT NULL
        """
        embeddings_result = await db_manager.execute_query(embeddings_query)
        embeddings_count = embeddings_result[0]['count'] if embeddings_result else 0
        
        # Check lesson summaries
        summaries_query = """
            SELECT COUNT(*) as count 
            FROM lesson_summaries 
            WHERE summary IS NOT NULL AND summary != ''
        """
        summaries_result = await db_manager.execute_query(summaries_query)
        summaries_count = summaries_result[0]['count'] if summaries_result else 0
        
        logger.info(f"📈 Data availability:")
        logger.info(f"   - Lessons with transcriptions: {lessons_count}")
        logger.info(f"   - Lessons with embeddings: {embeddings_count}")
        logger.info(f"   - Lesson summaries: {summaries_count}")
        
        return {
            'lessons_with_transcriptions': lessons_count,
            'lessons_with_embeddings': embeddings_count,
            'lesson_summaries': summaries_count
        }
    except Exception as e:
        logger.error(f"❌ Error checking sample data: {e}")
        return {}

async def get_sample_class_id():
    """Get a sample class_id for testing"""
    try:
        query = "SELECT id FROM classes LIMIT 1"
        result = await db_manager.execute_query(query)
        if result:
            class_id = result[0]['id']
            logger.info(f"🎯 Using class_id for testing: {class_id}")
            return class_id
        else:
            logger.warning("⚠️  No classes found in database")
            return None
    except Exception as e:
        logger.error(f"❌ Error getting sample class_id: {e}")
        return None

async def test_embedding_generation():
    """Test if embedding generation works"""
    try:
        logger.info("🧪 Testing embedding generation...")
        test_text = "This is a test for biology and DNA concepts"
        embedding = await rag_service.generate_embedding(test_text)
        
        if embedding and len(embedding) > 0:
            logger.info(f"✅ Embedding generated successfully (dimensions: {len(embedding)})")
            return True
        else:
            logger.warning("⚠️  Embedding generation returned empty result")
            return False
    except Exception as e:
        logger.error(f"❌ Embedding generation failed: {e}")
        return False

async def test_audio_transcription_search(class_id: str = None):
    """Test audio transcription search"""
    try:
        logger.info("🔍 Testing audio transcription search...")
        
        queries = [
            "biology cells DNA",
            "mathematics algebra",
            "physics energy",
            "chemistry reaction"
        ]
        
        for query in queries:
            logger.info(f"   Query: '{query}'")
            results = await rag_service.search_audio_transcriptions(
                query=query,
                class_id=class_id,
                limit=3
            )
            
            logger.info(f"   Results: {len(results)} found")
            for i, result in enumerate(results[:2]):  # Show first 2
                score = result.get('similarity_score', 0)
                title = result.get('lecture_title', 'N/A')
                logger.info(f"     {i+1}. Score: {score:.3f} - {title}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Audio transcription search failed: {e}")
        return False

async def test_lecture_summary_search(class_id: str = None):
    """Test lecture summary search"""
    try:
        logger.info("📝 Testing lecture summary search...")
        
        queries = [
            "biology cells DNA",
            "mathematics algebra",
            "physics energy"
        ]
        
        for query in queries:
            logger.info(f"   Query: '{query}'")
            results = await rag_service.search_lecture_summaries(
                query=query,
                class_id=class_id,
                limit=3
            )
            
            logger.info(f"   Results: {len(results)} found")
            for i, result in enumerate(results[:2]):  # Show first 2
                score = result.get('similarity_score', 0)
                title = result.get('lecture_title', 'N/A')
                logger.info(f"     {i+1}. Score: {score:.3f} - {title}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Lecture summary search failed: {e}")
        return False

async def test_combined_search(class_id: str = None):
    """Test combined search functionality"""
    try:
        logger.info("🔄 Testing combined search...")
        
        results = await rag_service.search_combined(
            query="biology cells DNA",
            class_id=class_id,
            subject="biology",
            limit=5,
            include_transcriptions=True,
            include_summaries=True
        )
        
        logger.info(f"Combined results:")
        logger.info(f"   - Transcriptions: {len(results.get('transcriptions', []))}")
        logger.info(f"   - Summaries: {len(results.get('summaries', []))}")
        logger.info(f"   - Total combined: {len(results.get('combined', []))}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Combined search failed: {e}")
        return False

async def create_sample_data_if_needed():
    """Create sample data if none exists"""
    try:
        # Check if we have any data
        data_check = await check_sample_data()
        
        if data_check.get('lessons_with_transcriptions', 0) == 0:
            logger.info("📝 Creating sample lesson data...")
            
            # Create a sample class first
            class_query = """
                INSERT INTO classes (id, class_code, subject, teacher_id, created_at)
                VALUES (gen_random_uuid(), 'TEST101', 'Biology', gen_random_uuid(), NOW())
                RETURNING id
            """
            class_result = await db_manager.execute_query(class_query)
            class_id = class_result[0]['id'] if class_result else None
            
            if class_id:
                # Create sample lesson
                lesson_query = """
                    INSERT INTO lessons (id, class_id, lecture_title, transcription, created_at)
                    VALUES (gen_random_uuid(), $1, 'Introduction to Biology', 
                            'Today we will discuss the fundamental concepts of biology including cells, DNA, and genetics. Cells are the basic units of life and contain genetic material.', 
                            NOW())
                """
                await db_manager.execute_query(lesson_query, class_id)
                
                # Create sample summary
                summary_query = """
                    INSERT INTO lesson_summaries (id, class_id, lecture_title, summary, topics_discussed, learning_objectives, key_points, duration, created_at)
                    VALUES (gen_random_uuid(), $1, 'Introduction to Biology',
                            'This lesson covered the basic concepts of biology including cell structure, DNA composition, and genetic inheritance patterns.',
                            '["cells", "DNA", "genetics", "biology"]',
                            '["Understand cell structure", "Explain DNA function", "Describe genetic patterns"]',
                            '["Cells are basic units of life", "DNA contains genetic information", "Genetics determines traits"]',
                            45, NOW())
                """
                await db_manager.execute_query(summary_query, class_id)
                
                logger.info(f"✅ Sample data created with class_id: {class_id}")
                return class_id
        
        return None
    except Exception as e:
        logger.error(f"❌ Error creating sample data: {e}")
        return None

async def main():
    """Main test function"""
    logger.info("🚀 Starting RAG Testing Suite")
    logger.info("=" * 50)
    
    # Step 1: Check database connection
    tables = await check_database_connection()
    if not tables:
        logger.error("❌ Cannot proceed without database connection")
        return
    
    # Step 2: Check sample data
    data_stats = await check_sample_data()
    
    # Step 3: Get or create sample class_id
    class_id = await get_sample_class_id()
    if not class_id:
        class_id = await create_sample_data_if_needed()
    
    if not class_id:
        logger.error("❌ No class_id available for testing")
        return
    
    # Step 4: Test embedding generation
    embedding_works = await test_embedding_generation()
    
    # Step 5: Test search functionalities
    logger.info("\n" + "=" * 50)
    logger.info("🧪 Running Search Tests")
    logger.info("=" * 50)
    
    audio_search_works = await test_audio_transcription_search(class_id)
    summary_search_works = await test_lecture_summary_search(class_id)
    combined_search_works = await test_combined_search(class_id)
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Results Summary")
    logger.info("=" * 50)
    logger.info(f"Database Connection: {'✅' if tables else '❌'}")
    logger.info(f"Embedding Generation: {'✅' if embedding_works else '❌'}")
    logger.info(f"Audio Search: {'✅' if audio_search_works else '❌'}")
    logger.info(f"Summary Search: {'✅' if summary_search_works else '❌'}")
    logger.info(f"Combined Search: {'✅' if combined_search_works else '❌'}")
    
    if all([tables, embedding_works, audio_search_works, summary_search_works, combined_search_works]):
        logger.info("\n🎉 All tests passed! RAG system is working correctly.")
    else:
        logger.warning("\n⚠️  Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    asyncio.run(main())

