#!/usr/bin/env python3
"""
Test script for Enhanced Transcription Service
"""

import os
import sys
import logging
from pathlib import Path

# Add service directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from service.enhanced_transcription_service import EnhancedTranscriptionService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_transcription():
    """Test Enhanced Transcription with sample audio file"""
    
    # Look for sample audio file
    test_audio_path = "/Users/thun/Desktop/pan-sea/voice-scraping-n-segmentation/data/temp/temp_audio_20250912_232823.wav"
    
    if not os.path.exists(test_audio_path):
        logger.error(f"Test audio file not found: {test_audio_path}")
        logger.info("Please ensure you have a sample audio file to test with")
        return False
    
    try:
        # Use the same config as your system (Khmer transcription service)
        config = {
            'TRANSCRIPTION_SERVICE_URL': 'http://3.234.216.146:8000/transcribe/khmer',
            'TRANSCRIPTION_SERVICE_TIMEOUT': 300,
            'use_openai_transcription': False  # Use external Khmer service
        }
        
        logger.info("Initializing Enhanced Transcription service...")
        service = EnhancedTranscriptionService(config)
        
        # Check if service is available (skip for testing)
        logger.info("Service will use fallback transcription if external service is not available")
        
        logger.info(f"Processing audio file: {test_audio_path}")
        
        # Create output directory
        output_dir = "/Users/thun/Desktop/pan-sea/voice-scraping-n-segmentation/data/temp/enhanced_transcription_test"
        os.makedirs(output_dir, exist_ok=True)
        
        # Run enhanced transcription with alignment
        result = service.align_audio_chunk(
            audio_path=test_audio_path,
            output_dir=output_dir,
            chunk_id="test_chunk"
        )
        
        if result.get('success') and result.get('words'):
            logger.info(f"SUCCESS! Found {len(result['words'])} word segments with timestamps")
            
            # Show transcription text
            transcription_data = result.get('transcription', {}).get('data', {})
            transcription_text = transcription_data.get('text', '')
            if transcription_text:
                logger.info(f"Transcription: {transcription_text}")
            
            # Show confidence
            confidence = transcription_data.get('confidence', 0.0)
            logger.info(f"Transcription confidence: {confidence:.3f}")
            
            # Show first few word segments
            for i, word_info in enumerate(result['words'][:5]):
                logger.info(f"  Word {i+1}: '{word_info['word']}' [{word_info['start']:.2f}s - {word_info['end']:.2f}s] (score: {word_info.get('score', 0):.3f})")
                
            logger.info(f"Full results saved to: {result.get('output_file', 'Unknown')}")
            logger.info(f"Method used: {result.get('method', 'unknown')}")
        else:
            logger.warning(f"Enhanced transcription failed: {result.get('error', 'Unknown error')}")
            return False
            
        logger.info("Enhanced Transcription test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Enhanced Transcription test failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("Testing Enhanced Transcription Service (MFA Replacement)")
    print("=" * 70)
    
    success = test_enhanced_transcription()
    
    if success:
        print("\n✅ Enhanced Transcription integration test PASSED!")
        print("You can now use Enhanced Transcription instead of MFA for word-level timestamps.")
        print("This service uses your existing Khmer transcription API and creates word timestamps.")
    else:
        print("\n❌ Enhanced Transcription integration test FAILED!")
        print("Check the logs above for error details.")
    
    print("=" * 70)
