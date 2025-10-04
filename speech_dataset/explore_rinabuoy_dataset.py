#!/usr/bin/env python3
"""
Explore Rinabuoy Khmer ASR Dataset
==================================

Script to explore the rinabuoy/khm-asr-open dataset before merging.
"""

from datasets import load_dataset
import pandas as pd
import json
from pathlib import Path

def explore_rinabuoy_dataset():
    """Explore the rinabuoy dataset structure and content"""
    print("🔍 Exploring rinabuoy/khm-asr-open dataset...")
    
    try:
        # Load the dataset
        print("📦 Downloading dataset...")
        ds = load_dataset("rinabuoy/khm-asr-open")
        
        print(f"✅ Dataset loaded successfully!")
        print(f"📊 Dataset info: {ds}")
        print()
        
        # Explore each split
        for split_name, split_data in ds.items():
            print(f"📁 Split: {split_name}")
            print(f"   Samples: {len(split_data):,}")
            
            # Check columns
            print(f"   Columns: {split_data.column_names}")
            
            # Sample some data
            sample = split_data[0]
            print(f"   Sample keys: {sample.keys()}")
            
            if 'transcription' in sample:
                print(f"   Sample transcription: {sample['transcription'][:100]}...")
            elif 'text' in sample:
                print(f"   Sample text: {sample['text'][:100]}...")
            
            if 'audio' in sample:
                audio_info = sample['audio']
                if isinstance(audio_info, dict):
                    print(f"   Audio info: {list(audio_info.keys())}")
                    if 'array' in audio_info:
                        print(f"   Audio array shape: {len(audio_info['array'])}")
                    if 'sampling_rate' in audio_info:
                        print(f"   Sampling rate: {audio_info['sampling_rate']}")
            
            # Check for speaker info
            if 'speaker_id' in sample:
                speakers = set(split_data['speaker_id'])
                print(f"   Unique speakers: {len(speakers)}")
                print(f"   Speaker sample: {list(speakers)[:5]}")
            
            print()
        
        # Calculate total statistics
        total_samples = sum(len(split) for split in ds.values())
        print(f"📈 Total Statistics:")
        print(f"   Total samples: {total_samples:,}")
        
        # Estimate duration if possible
        try:
            if 'train' in ds:
                train_sample = ds['train'][0]
                if 'audio' in train_sample:
                    sample_duration = len(train_sample['audio']['array']) / train_sample['audio']['sampling_rate']
                    estimated_duration = (total_samples * sample_duration) / 3600
                    print(f"   Estimated duration: {estimated_duration:.2f} hours")
        except:
            print("   Duration: Could not estimate")
        
        print("\n✅ Dataset exploration complete!")
        return ds
        
    except Exception as e:
        print(f"❌ Error loading dataset: {e}")
        print("💡 Make sure you have internet connection and datasets library installed:")
        print("   pip install datasets")
        return None

if __name__ == "__main__":
    explore_rinabuoy_dataset()
