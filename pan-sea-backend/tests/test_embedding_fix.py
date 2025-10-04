#!/usr/bin/env python3
"""
Test script to verify the embedding fix works correctly.
This tests the token counting and chunking functionality without requiring a full API call.
"""

import asyncio
import logging
import sys
import os

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.rag_service import rag_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_long_text(target_tokens: int = 12000) -> str:
    """Create a test text that's approximately the target token count"""
    # Create a realistic transcription-like text
    base_text = """
    This is a sample audio transcription that contains detailed information about a computer science lecture.
    The professor discussed various topics including machine learning algorithms, artificial intelligence methodologies,
    deep learning neural networks, natural language processing techniques, computer vision applications,
    data science frameworks, statistical analysis methods, mathematical foundations of computing, linear algebra concepts,
    calculus applications in optimization, probability theory and statistics, database management systems,
    software engineering principles, object-oriented programming paradigms, functional programming concepts,
    distributed systems architecture, cloud computing platforms, cybersecurity protocols, network security measures,
    encryption algorithms, digital privacy protection, blockchain technology, cryptocurrency mechanisms,
    web development frameworks, mobile application development, user interface design principles, user experience optimization,
    agile development methodologies, version control systems, continuous integration and deployment,
    software testing strategies, debugging techniques, performance optimization methods, scalability considerations,
    microservices architecture, API design principles, REST and GraphQL protocols, database optimization,
    big data processing frameworks, data mining techniques, predictive analytics models, machine learning pipelines,
    supervised and unsupervised learning algorithms, reinforcement learning applications, computer graphics rendering,
    virtual reality technologies, augmented reality implementations, game development engines, physics simulations.
    Students actively participated in discussions about practical implementations, real-world applications,
    industry best practices, research methodologies, academic paper reviews, emerging technology trends,
    career development opportunities, internship experiences, graduate school preparation, job market analysis,
    technical interview preparation, coding challenges, algorithm complexity analysis, system design principles,
    and professional development strategies for success in the technology industry.
    """
    
    # Repeat the text multiple times to ensure we exceed the token limit
    current_text = ""
    repetitions = max(1, (target_tokens * 4) // len(base_text) + 1)
    
    for i in range(repetitions):
        current_text += f"\n\nSection {i+1}:\n{base_text}"
    
    return current_text.strip()

async def test_token_counting():
    """Test the token counting functionality"""
    logger.info("Testing token counting...")
    
    short_text = "This is a short test."
    long_text = create_long_text(12000)
    
    short_tokens = rag_service._count_tokens(short_text)
    long_tokens = rag_service._count_tokens(long_text)
    
    logger.info(f"Short text: {len(short_text)} chars, {short_tokens} tokens")
    logger.info(f"Long text: {len(long_text)} chars, {long_tokens} tokens")
    
    return short_tokens, long_tokens

async def test_chunking():
    """Test the token-based chunking functionality"""
    logger.info("Testing token-based chunking...")
    
    long_text = create_long_text(12000)
    chunks = rag_service._chunk_text_by_tokens(
        long_text, 
        max_tokens=7000, 
        overlap_tokens=100
    )
    
    logger.info(f"Created {len(chunks)} chunks from text")
    
    # Verify each chunk is within limits
    for i, chunk in enumerate(chunks):
        tokens = rag_service._count_tokens(chunk)
        logger.info(f"Chunk {i+1}: {len(chunk)} chars, {tokens} tokens")
        assert tokens <= 7000, f"Chunk {i+1} exceeds token limit: {tokens} tokens"
    
    return chunks

async def test_embedding_preparation():
    """Test the embedding preparation without actually calling the API"""
    logger.info("Testing embedding preparation...")
    
    # Test with long text that would previously fail
    long_text = create_long_text(12000)
    
    # Clean the text
    cleaned_text = rag_service._clean_text(long_text)
    actual_tokens = rag_service._count_tokens(cleaned_text)
    
    logger.info(f"Original text tokens: {actual_tokens}")
    
    if actual_tokens <= rag_service.max_tokens_per_chunk:
        logger.info("Text fits within token limit - would embed directly")
        return True
    else:
        logger.info("Text too long - would use chunking")
        chunks = rag_service._chunk_text_by_tokens(
            cleaned_text, 
            max_tokens=rag_service.max_tokens_per_chunk, 
            overlap_tokens=rag_service.chunk_overlap_tokens
        )
        
        # Verify all chunks are valid
        all_valid = True
        for i, chunk in enumerate(chunks):
            chunk_tokens = rag_service._count_tokens(chunk)
            if chunk_tokens > rag_service.max_tokens_per_chunk:
                logger.error(f"Chunk {i+1} still too large: {chunk_tokens} tokens")
                all_valid = False
            else:
                logger.info(f"Chunk {i+1}: {chunk_tokens} tokens (valid)")
        
        return all_valid

async def main():
    """Run all tests"""
    logger.info("Starting embedding fix tests...")
    
    try:
        # Test 1: Token counting
        short_tokens, long_tokens = await test_token_counting()
        assert short_tokens > 0, "Token counting failed for short text"
        assert long_tokens > 7000, "Token counting seems inaccurate for long text"
        logger.info("✅ Token counting test passed")
        
        # Test 2: Chunking
        chunks = await test_chunking()
        assert len(chunks) > 1, "Chunking should create multiple chunks for long text"
        logger.info("✅ Chunking test passed")
        
        # Test 3: Embedding preparation
        is_valid = await test_embedding_preparation()
        assert is_valid, "Embedding preparation failed"
        logger.info("✅ Embedding preparation test passed")
        
        logger.info("🎉 All tests passed! The embedding fix should work correctly.")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
