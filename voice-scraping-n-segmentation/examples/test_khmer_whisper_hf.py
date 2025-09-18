"""
Example: Using Specialized Khmer Whisper Model from Hugging Face

This example demonstrates how to use the ksoky/whisper-large-khmer-asr model
for improved Khmer speech recognition accuracy.

The model achieves 29.5% WER on Khmer speech, significantly better than 
the base Whisper model for Khmer language.
"""

import asyncio
import json
import requests
from pathlib import Path
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from service.transcription_service import TranscriptionService
from config.settings import get_config


async def test_khmer_whisper_models():
    """
    Test both the original Whisper and the specialized Khmer model.
    """
    print("🇰🇭 Khmer Whisper Model Comparison Test")
    print("=" * 60)
    
    # Test configurations
    configs = [
        {
            'name': 'Original Whisper (base)',
            'config_updates': {
                'use_khmer_whisper_hf': False,
                'whisper_model': 'base'
            }
        },
        {
            'name': 'Specialized Khmer Whisper (ksoky)',
            'config_updates': {
                'use_khmer_whisper_hf': True,
                'khmer_whisper_model_id': 'ksoky/whisper-large-khmer-asr'
            }
        }
    ]
    
    # Base configuration
    base_config = get_config()
    
    for test_config in configs:
        print(f"\n📊 Testing: {test_config['name']}")
        print("-" * 40)
        
        # Create modified config
        config = base_config.copy()
        config.update(test_config['config_updates'])
        
        # Initialize transcription service
        try:
            transcription_service = TranscriptionService(config)
            
            # Check if service is available
            if not transcription_service.is_available():
                print(f"❌ {test_config['name']} not available")
                continue
            
            # Get model info
            model_info = transcription_service.get_model_info()
            print(f"✅ Model loaded successfully")
            print(f"   Primary method: {model_info['transcription_method']}")
            print(f"   Device: {model_info['device']}")
            
            if model_info.get('hf_khmer_enabled'):
                print(f"   HF Khmer model: {model_info['hf_khmer_model_id']}")
                print(f"   HF model available: {model_info['hf_khmer_available']}")
            
            print(f"   Original Whisper available: {model_info['whisper_available']}")
            
        except Exception as e:
            print(f"❌ Failed to load {test_config['name']}: {e}")


async def test_api_with_khmer_model():
    """
    Test the API endpoints with the Khmer model enabled.
    """
    print("\n🌐 API Test with Khmer Model")
    print("=" * 40)
    
    # Test configuration for API
    test_config = {
        "s3_key": "audio_for_training/voice1.wav",
        "use_mfa": True,
        "save_chunks": False,
        "vad_aggressiveness": 3,
        "min_chunk_duration": 1,
        "max_chunk_duration": 5,
        "transcription_model": "hf_khmer",  # Use HF Khmer model
        "use_external_transcription": False,
        "upload_chunks_to_s3": False,
        "upload_csv_to_s3": False
    }
    
    print("Configuration for API test:")
    print(json.dumps(test_config, indent=2))
    print()
    
    print("To test with API, use:")
    print("curl -X POST 'http://localhost:8000/api/voice/process-s3' \\")
    print("  -H 'Content-Type: application/json' \\")
    print(f"  -d '{json.dumps(test_config)}'")


def show_environment_setup():
    """
    Show how to set up environment variables for the Khmer model.
    """
    print("\n⚙️  Environment Setup")
    print("=" * 30)
    
    env_vars = [
        "# Enable Hugging Face Khmer Whisper model",
        "USE_KHMER_WHISPER_HF=true",
        "",
        "# Specify the model (default is ksoky/whisper-large-khmer-asr)",
        "KHMER_WHISPER_MODEL_ID=ksoky/whisper-large-khmer-asr",
        "",
        "# Device configuration (auto, cuda, cpu)",
        "WHISPER_DEVICE=auto",
        "",
        "# Keep original Whisper as fallback",
        "WHISPER_MODEL=base"
    ]
    
    print("Add these to your .env file:")
    print()
    for line in env_vars:
        print(line)


def show_model_comparison():
    """
    Show comparison between different Whisper models for Khmer.
    """
    print("\n📈 Model Comparison for Khmer")
    print("=" * 40)
    
    models = [
        {
            "name": "OpenAI Whisper Base",
            "accuracy": "~40-50% WER",
            "pros": ["Fast", "General purpose", "Built-in"],
            "cons": ["Not optimized for Khmer", "Lower accuracy"]
        },
        {
            "name": "ksoky/whisper-large-khmer-asr",
            "accuracy": "29.5% WER",
            "pros": ["Specialized for Khmer", "Higher accuracy", "Fine-tuned on SLR42"],
            "cons": ["Larger model size", "Requires HuggingFace"]
        }
    ]
    
    for model in models:
        print(f"\n{model['name']}:")
        print(f"  Accuracy: {model['accuracy']}")
        print(f"  Pros: {', '.join(model['pros'])}")
        print(f"  Cons: {', '.join(model['cons'])}")


async def main():
    """
    Main function to run all tests.
    """
    print("🚀 Starting Khmer Whisper Model Tests...")
    
    try:
        # Test model loading
        await test_khmer_whisper_models()
        
        # Show API usage
        await test_api_with_khmer_model()
        
        # Show setup instructions
        show_environment_setup()
        
        # Show model comparison
        show_model_comparison()
        
        print("\n" + "=" * 60)
        print("✅ Khmer Whisper Model Test Complete!")
        print()
        print("💡 Next Steps:")
        print("1. Set USE_KHMER_WHISPER_HF=true in your .env file")
        print("2. Install: pip install transformers datasets accelerate")
        print("3. Restart your server to load the new model")
        print("4. Test with your Khmer audio files")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
