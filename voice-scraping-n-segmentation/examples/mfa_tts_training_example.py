"""
Example: Training MFA Models with TTS Dataset

This example demonstrates how to use your existing Khmer TTS dataset 
(km_kh_male) to train custom MFA acoustic models and dictionaries.
"""

import asyncio
import json
from pathlib import Path
import sys

# Add the parent directory to the path so we can import our modules
sys.path.append(str(Path(__file__).parent.parent))

from service.mfa_training_service import MFATTSTrainingService
from service.mfa_service import MFAService
from config.settings import get_config


async def main():
    """
    Main example demonstrating TTS dataset training for MFA.
    """
    print("🇰🇭 Khmer MFA Training with TTS Dataset Example")
    print("=" * 60)
    
    # Initialize services
    config = get_config()
    training_service = MFATTSTrainingService(config)
    mfa_service = MFAService(config)
    
    print("📊 Step 1: Checking current MFA model status...")
    model_status = mfa_service.get_model_status()
    print(f"Current model status:")
    print(f"  - Custom acoustic model: {model_status['acoustic_model']['is_custom']}")
    print(f"  - Custom dictionary: {model_status['dictionary']['is_custom']}")
    print(f"  - Recommendations: {len(model_status['recommendations'])}")
    
    for rec in model_status['recommendations']:
        print(f"    • {rec}")
    print()
    
    print("🔍 Step 2: Validating TTS dataset...")
    validation_result = training_service.validate_tts_dataset()
    
    if validation_result['success']:
        print("✅ TTS dataset validation passed!")
        stats = validation_result['statistics']
        print(f"  - Total transcriptions: {stats['total_transcriptions']}")
        print(f"  - Valid audio-text pairs: {stats['valid_pairs']}")
        print(f"  - Unique words: {stats['unique_words']}")
        print(f"  - Average words per utterance: {stats['avg_words_per_utterance']:.1f}")
        
        if validation_result['recommendations']:
            print("  Recommendations:")
            for rec in validation_result['recommendations']:
                print(f"    • {rec}")
    else:
        print("❌ TTS dataset validation failed!")
        for issue in validation_result['issues']:
            print(f"  - {issue}")
        return
    print()
    
    print("📁 Step 3: Checking training status...")
    training_status = training_service.get_training_status()
    print(f"Training status:")
    print(f"  - Dataset prepared: {training_status['dataset_prepared']}")
    print(f"  - Dictionary generated: {training_status['dictionary_generated']}")
    print(f"  - Acoustic model trained: {training_status['acoustic_model_trained']}")
    print()
    
    # Prepare dataset if not already done
    if not training_status['dataset_prepared']:
        print("🔧 Step 4: Preparing dataset for MFA training...")
        prepare_result = training_service.prepare_tts_dataset_for_mfa()
        
        if prepare_result['success']:
            print(f"✅ Dataset prepared! Processed {prepare_result['processed_files']} files")
        else:
            print(f"❌ Dataset preparation failed: {prepare_result['error']}")
            return
    else:
        print("✅ Step 4: Dataset already prepared")
    print()
    
    # Generate dictionary if not already done
    if not training_status['dictionary_generated']:
        print("📝 Step 5: Generating Khmer pronunciation dictionary...")
        dict_result = training_service.generate_khmer_pronunciation_dictionary()
        
        if dict_result['success']:
            print(f"✅ Dictionary generated! Created {dict_result['word_count']} entries")
            print(f"   Dictionary saved to: {dict_result['dictionary_file']}")
            
            # Show sample entries
            if 'sample_entries' in dict_result:
                print("   Sample entries:")
                for word, phonemes in list(dict_result['sample_entries'].items())[:5]:
                    print(f"     {word} → {phonemes}")
        else:
            print(f"❌ Dictionary generation failed: {dict_result['error']}")
            return
    else:
        print("✅ Step 5: Dictionary already generated")
    print()
    
    # Train acoustic model if not already done
    if not training_status['acoustic_model_trained']:
        print("🎯 Step 6: Training MFA acoustic model...")
        print("⚠️  Warning: This can take 30-60 minutes depending on your hardware!")
        
        response = input("Continue with training? (y/N): ")
        if response.lower() != 'y':
            print("Training skipped.")
            return
        
        print("🚀 Starting acoustic model training...")
        train_result = training_service.train_acoustic_model()
        
        if train_result['success']:
            print(f"✅ Acoustic model training completed!")
            print(f"   Model saved to: {train_result['model_path']}")
        else:
            print(f"❌ Acoustic model training failed: {train_result['error']}")
            if 'stdout' in train_result:
                print("Training output:")
                print(train_result['stdout'])
            return
    else:
        print("✅ Step 6: Acoustic model already trained")
    print()
    
    print("🔄 Step 7: Checking final MFA model status...")
    final_status = mfa_service.get_model_status()
    print(f"Final model status:")
    print(f"  - Custom acoustic model: {final_status['acoustic_model']['is_custom']}")
    print(f"  - Custom dictionary: {final_status['dictionary']['is_custom']}")
    print(f"  - All models available: {final_status['custom_models_available']}")
    print()
    
    if final_status['custom_models_available']:
        print("🎉 Success! Custom MFA models are now available.")
        print("You can now use these models for high-quality Khmer forced alignment.")
        print()
        print("📊 Usage example:")
        print("Your voice processing requests will now automatically use")
        print("the custom TTS-trained models for better Khmer alignment.")
    else:
        print("⚠️  Custom models not fully available yet.")
        print("Some training steps may still be needed.")
    
    print()
    print("=" * 60)
    print("🇰🇭 MFA TTS Training Example Complete!")


def show_api_usage():
    """
    Show how to use the API endpoints for MFA training.
    """
    print("\n📡 API Usage Examples:")
    print("=" * 40)
    
    api_examples = [
        {
            "title": "Check Training Status",
            "method": "GET",
            "endpoint": "/api/mfa-training/status",
            "description": "Get current status of training data and models"
        },
        {
            "title": "Validate TTS Dataset",
            "method": "GET", 
            "endpoint": "/api/mfa-training/validate-dataset",
            "description": "Validate TTS dataset for MFA compatibility"
        },
        {
            "title": "Run Full Training Pipeline",
            "method": "POST",
            "endpoint": "/api/mfa-training/full-training-pipeline",
            "body": {"force_rebuild": False, "num_jobs": 4},
            "description": "Run complete training pipeline"
        },
        {
            "title": "Get Model Information",
            "method": "GET",
            "endpoint": "/api/mfa-training/model-info", 
            "description": "Get detailed model status and recommendations"
        }
    ]
    
    for example in api_examples:
        print(f"\n{example['title']}:")
        print(f"  {example['method']} {example['endpoint']}")
        if 'body' in example:
            print(f"  Body: {json.dumps(example['body'], indent=2)}")
        print(f"  {example['description']}")


if __name__ == "__main__":
    print("Running MFA TTS Training Example...")
    try:
        asyncio.run(main())
        show_api_usage()
    except KeyboardInterrupt:
        print("\n\nTraining interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
