#!/usr/bin/env python3
"""
SageMaker-Optimized Whisper Dataset Preprocessing
Designed for SageMaker instances with built-in IAM roles and S3 access
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
from datasets import Dataset, DatasetDict
from transformers import WhisperFeatureExtractor, WhisperTokenizer
import warnings
warnings.filterwarnings("ignore")

def preprocess_for_sagemaker(datasets, output_dir=None, 
                            model_name='openai/whisper-tiny',
                            language='km', task='transcribe',
                            max_samples_per_split=None,
                            batch_size=10):
    """
    SageMaker-optimized preprocessing that works with your loaded datasets
    
    Args:
        datasets: Your loaded DatasetDict from the notebook
        output_dir: Optional - where to save processed datasets  
        max_samples_per_split: Limit samples to avoid memory issues
        batch_size: Process in small batches to avoid memory problems
    """
    
    print("🔄 SAGEMAKER WHISPER PREPROCESSING")
    print("=" * 50)
    
    # Use SageMaker's built-in S3 client (inherits IAM role)
    try:
        s3_client = boto3.client('s3')
        print("✅ Using SageMaker IAM role for S3 access")
    except Exception as e:
        print(f"❌ S3 client failed: {e}")
        return None
    
    # Initialize Whisper components
    print(f"🔧 Loading Whisper components ({model_name})...")
    try:
        feature_extractor = WhisperFeatureExtractor.from_pretrained(model_name)
        tokenizer = WhisperTokenizer.from_pretrained(model_name, language=language, task=task)
        print("✅ Whisper components loaded")
    except Exception as e:
        print(f"❌ Failed to load Whisper components: {e}")
        return None
    
    def process_batch(batch_samples):
        """Process a small batch of samples"""
        batch_results = {
            'input_features': [],
            'labels': []
        }
        
        for sample in batch_samples:
            try:
                # Handle different audio formats
                audio_data = sample.get('audio_filepath') or sample.get('audio')
                
                if isinstance(audio_data, dict):
                    # Audio is already loaded (HuggingFace Audio column format)
                    audio_array = audio_data['array']
                    sampling_rate = audio_data['sampling_rate']
                    
                    # Convert to numpy array if needed
                    if hasattr(audio_array, 'numpy'):
                        audio_array = audio_array.numpy()
                    audio_array = np.array(audio_array, dtype=np.float32)
                    
                    # Ensure mono
                    if len(audio_array.shape) > 1:
                        audio_array = np.mean(audio_array, axis=1)
                    
                    # Resample if needed
                    if sampling_rate != 16000:
                        import librosa
                        audio_array = librosa.resample(audio_array, orig_sr=sampling_rate, target_sr=16000)
                
                elif isinstance(audio_data, str) and audio_data.startswith('s3://'):
                    # Need to load from S3 path
                    parts = audio_data.replace('s3://', '').split('/', 1)
                    bucket_name = parts[0]
                    s3_key = parts[1]
                    
                    # Download audio
                    response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                    audio_bytes = response['Body'].read()
                    
                    # Load with soundfile
                    audio_array, sampling_rate = sf.read(io.BytesIO(audio_bytes))
                    
                    # Convert to mono float32
                    if len(audio_array.shape) > 1:
                        audio_array = np.mean(audio_array, axis=1)
                    audio_array = audio_array.astype(np.float32)
                    
                    # Resample if needed
                    if sampling_rate != 16000:
                        import librosa
                        audio_array = librosa.resample(audio_array, orig_sr=sampling_rate, target_sr=16000)
                
                else:
                    raise ValueError(f"Unsupported audio format: {type(audio_data)}")
                
                # Extract features
                input_features = feature_extractor(
                    audio_array,
                    sampling_rate=16000,
                    return_tensors="np"
                ).input_features[0]
                
                # Tokenize text
                text = str(sample.get('text', '')).strip()
                if not text:
                    raise ValueError("Empty text")
                
                with tokenizer.as_target_tokenizer():
                    labels = tokenizer(text).input_ids
                
                batch_results['input_features'].append(input_features)
                batch_results['labels'].append(labels)
                
            except Exception as e:
                print(f"⚠️ Sample failed: {e}")
                continue
        
        return batch_results
    
    # Process each split
    processed_splits = {}
    
    for split_name, dataset in datasets.items():
        print(f"\n🔄 Processing {split_name} split...")
        
        # Limit samples if requested
        if max_samples_per_split and len(dataset) > max_samples_per_split:
            dataset = dataset.select(range(max_samples_per_split))
            print(f"🔧 Limited to {max_samples_per_split} samples")
        
        # Process in batches
        all_input_features = []
        all_labels = []
        
        for i in tqdm(range(0, len(dataset), batch_size), desc=f"Processing {split_name}"):
            batch_indices = range(i, min(i + batch_size, len(dataset)))
            batch_samples = [dataset[idx] for idx in batch_indices]
            
            batch_results = process_batch(batch_samples)
            
            all_input_features.extend(batch_results['input_features'])
            all_labels.extend(batch_results['labels'])
            
            # Free memory periodically
            if i % (batch_size * 10) == 0:
                torch.cuda.empty_cache() if torch.cuda.is_available() else None
        
        if all_input_features:
            # Create processed dataset
            processed_data = {
                'input_features': all_input_features,
                'labels': all_labels
            }
            processed_splits[split_name] = Dataset.from_dict(processed_data)
            print(f"✅ {split_name}: {len(all_input_features)} samples processed")
        else:
            print(f"❌ {split_name}: No samples processed successfully")
    
    if not processed_splits:
        print("❌ PREPROCESSING FAILED - No splits processed")
        return None
    
    processed_datasets = DatasetDict(processed_splits)
    
    # Optionally save to disk
    if output_dir:
        print(f"\n💾 Saving processed datasets to {output_dir}...")
        processed_datasets.save_to_disk(output_dir)
        print("✅ Datasets saved")
    
    print(f"\n🎉 PREPROCESSING COMPLETE!")
    print(f"✅ Processed {sum(len(d) for d in processed_splits.values())} total samples")
    
    return processed_datasets

if __name__ == "__main__":
    print("🚀 SageMaker Whisper Preprocessing")
    print("💡 This script is designed to be imported in your SageMaker notebook")
    print("💡 Usage in notebook:")
    print("   from preprocess_whisper_data_sagemaker import preprocess_for_sagemaker")
    print("   processed_datasets = preprocess_for_sagemaker(datasets, max_samples_per_split=1000)")