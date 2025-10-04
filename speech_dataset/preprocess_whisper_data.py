#!/usr/bin/env python3
"""
Whisper Dataset Preprocessing ONLY
Converts your existing CSV datasets to input_features + labels format
NO DUMMY DATA - Fails on real errors
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import torch
import boto3
import soundfile as sf
import io
from pathlib import Path
from tqdm import tqdm
from datasets import Dataset, DatasetDict, load_from_disk
from transformers import WhisperFeatureExtractor, WhisperTokenizer
import warnings
warnings.filterwarnings("ignore")

def preprocess_whisper_datasets(input_dir, output_dir, 
                               model_name='openai/whisper-tiny',
                               language='km', task='transcribe'):
    """
    Apply preprocessing to convert raw datasets to training format
    
    Args:
        input_dir: Directory containing your raw datasets (with audio_filepath, text, etc.)
        output_dir: Where to save processed datasets (with input_features, labels)
    """
    
    print("🔄 WHISPER PREPROCESSING - RAW → TRAINING FORMAT")
    print("=" * 60)
    
    # Load your existing datasets
    print(f"📂 Loading raw datasets from: {input_dir}")
    
    try:
        raw_datasets = load_from_disk(input_dir)
        print(f"✅ Loaded {len(raw_datasets)} splits")
        
        for split_name, dataset in raw_datasets.items():
            print(f"   {split_name}: {len(dataset):,} samples")
            print(f"      Columns: {dataset.column_names}")
    except Exception as e:
        print(f"❌ FAILED to load datasets from {input_dir}")
        print(f"Error: {e}")
        sys.exit(1)
    
    # Initialize Whisper components
    print(f"\n🔧 Initializing Whisper components ({model_name})...")
    try:
        feature_extractor = WhisperFeatureExtractor.from_pretrained(model_name)
        tokenizer = WhisperTokenizer.from_pretrained(model_name, language=language, task=task)
        s3_client = boto3.client('s3', region_name='ap-southeast-1')
        print("✅ Components initialized successfully")
    except Exception as e:
        print(f"❌ FAILED to initialize Whisper components: {e}")
        sys.exit(1)
    
    def preprocess_sample(sample):
        """Convert one sample: audio_filepath → input_features, text → labels"""
        
        # Process audio
        audio_path = sample['audio_filepath']
        
        if isinstance(audio_path, str) and audio_path.startswith('s3://'):
            # Load real S3 audio
            try:
                # Parse S3 path
                parts = audio_path.replace('s3://', '').split('/', 1)
                bucket_name = parts[0]
                s3_key = parts[1]
                
                # Download from S3
                response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                audio_bytes = response['Body'].read()
                
                # Load audio
                audio_array, sampling_rate = sf.read(io.BytesIO(audio_bytes))
                
                # Ensure mono and float32
                if len(audio_array.shape) > 1:
                    audio_array = np.mean(audio_array, axis=1)
                audio_array = audio_array.astype(np.float32)
                
                # Resample if needed
                if sampling_rate != 16000:
                    import librosa
                    audio_array = librosa.resample(audio_array, orig_sr=sampling_rate, target_sr=16000)
                
            except Exception as e:
                raise RuntimeError(f"FAILED to load audio from {audio_path}: {e}")
        
        elif isinstance(audio_path, str) and os.path.exists(audio_path):
            # Load local file
            try:
                audio_array, sampling_rate = sf.read(audio_path)
                if len(audio_array.shape) > 1:
                    audio_array = np.mean(audio_array, axis=1)
                audio_array = audio_array.astype(np.float32)
                
                if sampling_rate != 16000:
                    import librosa
                    audio_array = librosa.resample(audio_array, orig_sr=sampling_rate, target_sr=16000)
                    
            except Exception as e:
                raise RuntimeError(f"FAILED to load local audio from {audio_path}: {e}")
        
        else:
            raise ValueError(f"Invalid audio path: {audio_path}")
        
        # Extract mel-spectrogram features
        try:
            input_features = feature_extractor(
                audio_array,
                sampling_rate=16000,
                return_tensors="np"
            ).input_features[0]
        except Exception as e:
            raise RuntimeError(f"FAILED to extract features from audio: {e}")
        
        # Tokenize text
        text = str(sample.get('text', '')).strip()
        if not text:
            raise ValueError("Empty or missing text field")
        
        try:
            with tokenizer.as_target_tokenizer():
                labels = tokenizer(text).input_ids
        except Exception as e:
            raise RuntimeError(f"FAILED to tokenize text '{text}': {e}")
        
        return {
            'input_features': input_features,
            'labels': labels
        }
    
    # Process each split
    processed_datasets = {}
    
    for split_name, dataset in raw_datasets.items():
        print(f"\n🔄 Processing {split_name} split ({len(dataset):,} samples)...")
        
        try:
            # Apply preprocessing - this will FAIL on any error
            processed_dataset = dataset.map(
                preprocess_sample,
                remove_columns=dataset.column_names,  # Remove ALL original columns
                desc=f"Converting {split_name}",
                num_proc=1  # Single process for clearer error messages
            )
            
            processed_datasets[split_name] = processed_dataset
            
            # Verify the result
            sample = processed_dataset[0]
            input_shape = sample['input_features'].shape
            labels_len = len(sample['labels'])
            
            print(f"✅ {split_name}: {len(processed_dataset):,} samples processed")
            print(f"   Input features shape: {input_shape}")
            print(f"   Labels length: {labels_len}")
            
        except Exception as e:
            print(f"❌ FAILED to process {split_name} split")
            print(f"Error: {e}")
            print("\n💡 Check your audio files and S3 paths!")
            sys.exit(1)
    
    # Save processed dataset
    print(f"\n💾 Saving processed dataset to: {output_dir}")
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    try:
        final_dataset = DatasetDict(processed_datasets)
        final_dataset.save_to_disk(str(output_path))
        
        # Save metadata
        metadata = {
            "processed_by": "preprocess_whisper_data.py",
            "model_name": model_name,
            "language": language,
            "task": task,
            "splits": {split: len(dataset) for split, dataset in processed_datasets.items()},
            "total_samples": sum(len(dataset) for dataset in processed_datasets.values()),
            "columns": ["input_features", "labels"],
            "input_features_shape": list(input_shape),
            "original_columns_removed": list(raw_datasets[list(raw_datasets.keys())[0]].column_names)
        }
        
        with open(output_path / "preprocessing_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print("✅ Preprocessing complete!")
        print(f"📊 Final dataset:")
        
        total_samples = 0
        for split, dataset in processed_datasets.items():
            total_samples += len(dataset)
            print(f"   {split}: {len(dataset):,} samples")
        
        print(f"   Total: {total_samples:,} samples")
        print(f"   Columns: {final_dataset[list(processed_datasets.keys())[0]].column_names}")
        print(f"\n🎉 Ready for training! Load with:")
        print(f"   datasets = load_from_disk('{output_path}')")
        
        return final_dataset
        
    except Exception as e:
        print(f"❌ FAILED to save processed dataset: {e}")
        sys.exit(1)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess datasets for Whisper training')
    parser.add_argument('input_dir', help='Directory with raw datasets')
    parser.add_argument('output_dir', help='Directory to save processed datasets')
    parser.add_argument('--model', default='openai/whisper-tiny', help='Whisper model name')
    parser.add_argument('--language', default='km', help='Language code')
    parser.add_argument('--task', default='transcribe', help='Task type')
    
    args = parser.parse_args()
    
    # Run preprocessing
    preprocess_whisper_datasets(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_name=args.model,
        language=args.language,
        task=args.task
    )

if __name__ == "__main__":
    main()