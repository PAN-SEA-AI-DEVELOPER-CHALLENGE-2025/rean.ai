#!/usr/bin/env python3
"""
Example Usage of Khmer Speech Dataset
====================================

This script demonstrates how to use the built speech dataset with different frameworks.
"""

import json
import pandas as pd
from pathlib import Path

def basic_data_exploration():
    """Basic exploration of the dataset"""
    print("=== KHMER SPEECH DATASET EXPLORATION ===\n")
    
    # Load dataset info
    with open('dataset/dataset_info.json', 'r') as f:
        info = json.load(f)
    
    print("Dataset Overview:")
    print(f"- Name: {info['dataset_name']}")
    print(f"- Language: {info['language']}")
    print(f"- Total Sessions: {info['statistics']['total_sessions']}")
    print(f"- Total Chunks: {info['statistics']['total_chunks']}")
    print(f"- Total Duration: {info['statistics']['total_duration_hours']:.2f} hours")
    print(f"- Sample Rate: {info['sample_rate']} Hz")
    print()
    
    # Load training manifest
    train_df = pd.read_csv('dataset/train/train_manifest.csv')
    print("Training Split:")
    print(f"- Training samples: {len(train_df)}")
    print(f"- Duration range: {train_df['duration'].min():.2f}s - {train_df['duration'].max():.2f}s")
    print(f"- Average duration: {train_df['duration'].mean():.2f}s")
    print(f"- Unique speakers: {train_df['speaker'].nunique()}")
    print()
    
    # Sample transcriptions
    print("Sample Transcriptions:")
    for i, row in train_df.head(3).iterrows():
        print(f"- {row['text']}")
    print()

def pytorch_example():
    """Example using PyTorch"""
    print("=== PYTORCH EXAMPLE ===")
    try:
        from data_loader import load_pytorch_dataset
        
        # Load training dataset
        train_dataset = load_pytorch_dataset('dataset', 'train')
        print(f"Loaded PyTorch dataset with {len(train_dataset)} samples")
        
        # Get a sample
        sample = train_dataset[0]
        print(f"Sample audio shape: {sample['audio'].shape}")
        print(f"Sample text: {sample['text']}")
        print(f"Sample duration: {sample['duration']:.2f}s")
        print(f"Sample language: {sample['language']}")
        print()
        
    except ImportError as e:
        print(f"PyTorch not available: {e}")
        print("Install with: pip install torch torchaudio")
        print()

def huggingface_example():
    """Example using Hugging Face Datasets"""
    print("=== HUGGING FACE EXAMPLE ===")
    try:
        from data_loader import load_huggingface_dataset
        
        # Load training dataset
        hf_dataset = load_huggingface_dataset('dataset', 'train')
        print(f"Loaded HF dataset with {len(hf_dataset)} samples")
        
        # Get a sample
        sample = hf_dataset[0]
        print(f"Sample audio: {sample['audio']['array'][:10]}...")  # First 10 samples
        print(f"Sample transcription: {sample['transcription']}")
        print(f"Sample duration: {sample['duration']:.2f}s")
        print()
        
    except ImportError as e:
        print(f"Hugging Face datasets not available: {e}")
        print("Install with: pip install datasets")
        print()

def manual_loading_example():
    """Example of manual data loading"""
    print("=== MANUAL LOADING EXAMPLE ===")
    
    # Load manifest manually
    with open('dataset/train/train_manifest.jsonl', 'r') as f:
        samples = [json.loads(line) for line in f.readlines()[:5]]
    
    print("First 5 training samples:")
    for i, sample in enumerate(samples):
        print(f"{i+1}. {sample['audio_filepath']}")
        print(f"   Text: {sample['text']}")
        print(f"   Duration: {sample['duration']:.2f}s")
        print(f"   Speaker: {sample['speaker']}")
        print()

def training_framework_examples():
    """Show how to use with different training frameworks"""
    print("=== TRAINING FRAMEWORK EXAMPLES ===")
    
    print("1. ESPnet Training:")
    print("   espnet2-train --config config.yaml --train_data_path_and_name_and_type dataset/train/train_manifest.jsonl,speech,kaldi_ark")
    print()
    
    print("2. Wav2Vec2 with Hugging Face:")
    print("   from transformers import Wav2Vec2ForCTC, Wav2Vec2Tokenizer")
    print("   # Load model and tokenizer, then use HF dataset for training")
    print()
    
    print("3. Whisper Fine-tuning:")
    print("   from transformers import WhisperForConditionalGeneration")
    print("   # Use HF dataset format for fine-tuning Whisper on Khmer")
    print()

def data_statistics():
    """Show detailed data statistics"""
    print("=== DATA STATISTICS ===")
    
    # Load all splits
    train_df = pd.read_csv('dataset/train/train_manifest.csv')
    val_df = pd.read_csv('dataset/validation/validation_manifest.csv')
    test_df = pd.read_csv('dataset/test/test_manifest.csv')
    
    print("Split Statistics:")
    print(f"- Train: {len(train_df)} samples ({train_df['duration'].sum()/3600:.2f} hours)")
    print(f"- Validation: {len(val_df)} samples ({val_df['duration'].sum()/3600:.2f} hours)")
    print(f"- Test: {len(test_df)} samples ({test_df['duration'].sum()/3600:.2f} hours)")
    print()
    
    # Duration distribution
    all_durations = pd.concat([train_df['duration'], val_df['duration'], test_df['duration']])
    print("Duration Distribution:")
    print(f"- Min: {all_durations.min():.2f}s")
    print(f"- Max: {all_durations.max():.2f}s")
    print(f"- Mean: {all_durations.mean():.2f}s")
    print(f"- Median: {all_durations.median():.2f}s")
    print()
    
    # Speaker distribution
    all_speakers = pd.concat([train_df['speaker'], val_df['speaker'], test_df['speaker']])
    speaker_counts = all_speakers.value_counts()
    print(f"Speaker Distribution ({len(speaker_counts)} unique speakers):")
    print(speaker_counts.head().to_string())
    print()

if __name__ == "__main__":
    basic_data_exploration()
    data_statistics()
    pytorch_example()
    huggingface_example()
    manual_loading_example()
    training_framework_examples()
