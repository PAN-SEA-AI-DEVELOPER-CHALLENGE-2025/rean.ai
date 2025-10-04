import sagemaker
import boto3
import os
from sagemaker import get_execution_role
from sagemaker.pytorch import PyTorch
import json
from datetime import datetime

# Initialize SageMaker session for Singapore region
sagemaker_session = sagemaker.Session(boto3.Session(region_name='ap-southeast-1'))
role = get_execution_role()
region = 'ap-southeast-1'  # Singapore region

# Use your existing S3 bucket with uploaded dataset
bucket = 'pan-sea-khmer-speech-dataset-sg'  # Your Singapore bucket
prefix = 'khmer-whisper-training'

print(f"🌟 SageMaker Session Initialized!")
print(f"📦 S3 Bucket: {bucket}")
print(f"🌍 Region: {region}")
print(f"🔑 Role: {role}")
print(f"📁 Prefix: {prefix}")

# Create S3 paths - Updated with your actual uploaded dataset path
dataset_s3_path = 's3://pan-sea-khmer-speech-dataset-sg/khmer-whisper-dataset/data'  # Your uploaded dataset
model_artifacts_path = f's3://{bucket}/{prefix}/model-artifacts'
logs_path = f's3://{bucket}/{prefix}/logs'

print(f"\n📊 S3 Paths:")
print(f"   Dataset: {dataset_s3_path}")
print(f"   Models: {model_artifacts_path}")
print(f"   Logs: {logs_path}")

# Verify dataset exists
s3_client = boto3.client('s3', region_name=region)
try:
    response = s3_client.list_objects_v2(
        Bucket='pan-sea-khmer-speech-dataset-sg',
        Prefix='khmer-whisper-dataset/data/',
        MaxKeys=5
    )
    if 'Contents' in response:
        print(f"✅ Dataset verified in S3: {len(response.get('Contents', []))} files found")
        print(f"📂 Sample files:")
        for obj in response['Contents'][:3]:
            print(f"   - {obj['Key']}")
    else:
        print("❌ No files found in dataset path")
except Exception as e:
    print(f"⚠️ Could not verify dataset: {e}")
    
# Install required packages
import subprocess
import sys
import warnings
warnings.filterwarnings('ignore')

print("🚀 Installing Whisper Dependencies for SageMaker")

# Essential packages
essential_packages = [
    "torch torchvision torchaudio",
    "transformers==4.35.2",
    "datasets==2.14.7", 
    "soundfile",
    "evaluate",
    "jiwer", 
    "accelerate",
    "boto3",
    "tqdm",
    "librosa==0.10.1"
]

# Install packages
for package in essential_packages:
    try:
        subprocess.run(f"pip install {package}", shell=True, check=True, capture_output=True)
        print(f"✅ {package}")
    except subprocess.CalledProcessError:
        print(f"⚠️ Warning: {package} installation failed")

# Test critical imports
try:
    import torch
    import transformers
    print(f"✅ PyTorch: {torch.__version__}")
    print(f"✅ Transformers: {transformers.__version__}")
    print(f"✅ CUDA Available: {torch.cuda.is_available()}")
    print("🎉 Ready for Whisper training!")
except Exception as e:
    print(f"❌ Import test failed: {e}")

# ✅ Load Dataset from S3 CSV Manifests (UPDATED)
import json
import pandas as pd
import librosa
import numpy as np
from pathlib import Path
from datasets import Dataset, DatasetDict, Audio
from transformers import WhisperFeatureExtractor, WhisperTokenizer
import torch
from torch.utils.data import DataLoader
import boto3
import io

class S3CSVDatasetLoader:
    """Load dataset from uploaded CSV manifest files in S3"""
    
    def __init__(self):
        self.feature_extractor = WhisperFeatureExtractor.from_pretrained("openai/whisper-tiny")
        self.tokenizer = WhisperTokenizer.from_pretrained("openai/whisper-tiny", language="km", task="transcribe")
        self.s3_client = boto3.client('s3', region_name='ap-southeast-1')
        self.bucket_name = 'pan-sea-khmer-speech-dataset-sg'
        
    def check_csv_manifests(self):
        """Check if CSV manifest files exist in S3"""
        print("🔍 Checking for CSV manifest files...")
        
        csv_files = {
            'train': 'khmer-whisper-dataset/data/train/train_manifest.csv',
            'validation': 'khmer-whisper-dataset/data/validation/validation_manifest.csv',
            'test': 'khmer-whisper-dataset/data/test/test_manifest.csv'
        }
        
        found_files = {}
        for split, s3_key in csv_files.items():
            try:
                self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
                found_files[split] = s3_key
                print(f"✅ {split}_manifest.csv found")
            except:
                print(f"❌ {split}_manifest.csv not found")
        
        return found_files
    
    def load_csv_from_s3(self, split, s3_key):
        """Download and load CSV manifest from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            csv_content = response['Body'].read()
            df = pd.read_csv(io.BytesIO(csv_content))
            print(f"✅ {split}: {len(df)} entries loaded")
            return df
        except Exception as e:
            print(f"❌ Failed to load {split}: {e}")
            return None
    
    def load_datasets(self, max_duration=20.0, min_duration=1.0, max_samples=None):
        """Load datasets from S3 CSV manifests"""
        print("🚀 Loading datasets from S3 CSV manifests")
        
        csv_files = self.check_csv_manifests()
        if not csv_files:
            print("❌ No CSV manifest files found!")
            return self.create_dummy_datasets()
        
        dataset_dict = {}
        
        for split in ['train', 'validation', 'test']:
            if split not in csv_files:
                print(f"⚠️ Skipping {split} - no CSV found")
                continue
            
            # Load and filter data
            df = self.load_csv_from_s3(split, csv_files[split])
            if df is None:
                continue
            
            # Filter by duration
            df_filtered = df[
                (df['duration'] >= min_duration) & 
                (df['duration'] <= max_duration)
            ]
            print(f"📊 {split}: {len(df):,} → {len(df_filtered):,} samples (after duration filter)")
            
            # Limit samples if specified
            if max_samples and len(df_filtered) > max_samples:
                df_filtered = df_filtered.head(max_samples)
                print(f"🔧 Limited to {max_samples} samples")
            
            # Convert to dataset format
            data = []
            for _, row in df_filtered.iterrows():
                audio_filename = row['audio_filepath']
                
                # Clean up audio filename paths
                if audio_filename.startswith('audio/audio/'):
                    audio_filename = audio_filename[6:]
                elif not audio_filename.startswith('audio/'):
                    audio_filename = f"audio/{audio_filename}"
                
                s3_audio_path = f"s3://{self.bucket_name}/khmer-whisper-dataset/data/{split}/{audio_filename}"
                
                entry = {
                    'audio_filepath': s3_audio_path,
                    'text': str(row['text']),
                    'duration': float(row['duration']),
                    'language': row.get('language', 'km'),
                    'source': row.get('source', 'mega_dataset'),
                    'speaker': row.get('speaker', 'unknown')
                }
                data.append(entry)
            
            # Create HuggingFace dataset
            if data:
                dataset = Dataset.from_list(data)
                try:
                    dataset = dataset.cast_column("audio_filepath", Audio(sampling_rate=16000))
                    print(f"✅ {split}: {len(data)} samples ready")
                except Exception as e:
                    print(f"⚠️ Audio casting warning: {e}")
                
                dataset_dict[split] = dataset
        
        return DatasetDict(dataset_dict) if dataset_dict else self.create_dummy_datasets()
    
    def create_dummy_datasets(self):
        """Create small dummy datasets for testing"""
        print("🎯 Creating dummy datasets for testing...")
        
        dataset_dict = {}
        sizes = {'train': 100, 'validation': 30, 'test': 30}
        
        for split, size in sizes.items():
            data = []
            for i in range(size):
                data.append({
                    'text': f'សាកល្បង ទី {i+1}',  # "Test number i" in Khmer
                    'audio_filepath': f'dummy_audio_{split}_{i}.wav',
                    'duration': 2.0 + (i % 3),
                    'language': 'km',
                    'source': 'dummy',
                    'speaker': 'unknown'
                })
            
            dataset = Dataset.from_list(data)
            dataset_dict[split] = dataset
            print(f"📝 {split}: {size} dummy samples")
        
        return DatasetDict(dataset_dict)

# Initialize loader and load datasets
print("🚀 Initializing S3 CSV Dataset Loader...")
dataset_loader = S3CSVDatasetLoader()

# Load FULL dataset (all samples)
datasets = dataset_loader.load_datasets(
    max_duration=20.0,
    min_duration=1.0, 
    max_samples=None  # Use ALL samples - no limit!
)

# Show results
if datasets:
    print(f"\n📊 Final Dataset Summary:")
    print("=" * 40)
    
    total_samples = 0
    for split, dataset in datasets.items():
        count = len(dataset)
        total_samples += count
        
        if 'duration' in dataset.column_names:
            hours = sum(dataset['duration']) / 3600
            print(f"  {split.capitalize()}: {count:,} samples ({hours:.2f} hours)")
        else:
            print(f"  {split.capitalize()}: {count:,} samples")
    
    print(f"  Total: {total_samples:,} samples")
    print(f"\n✅ Dataset variable 'datasets' created successfully!")
    print(f"🎯 You can now proceed with training!")
    
    # Show sample
    if total_samples > 0:
        sample_split = list(datasets.keys())[0]
        sample = datasets[sample_split][0]
        print(f"\n🔍 Sample from {sample_split}:")
        print(f"   Text: {sample['text'][:100]}...")
        print(f"   Duration: {sample['duration']} seconds")
        
        # Handle audio path safely (could be string, list, or other type)
        audio_path = sample['audio_filepath']
        if isinstance(audio_path, str):
            print(f"   Audio path: {audio_path[:60]}...")
        else:
            print(f"   Audio path: {str(audio_path)[:60]}...")
        

else:
    print(f"\n" + "="*50)
    print("❌ Dataset loading failed!")
    print("💡 Check CSV uploads and try again")
    
from transformers import (
    WhisperForConditionalGeneration, 
    WhisperTokenizer, 
    WhisperFeatureExtractor,
    WhisperProcessor
)
from dataclasses import dataclass
import torch.nn as nn

@dataclass
class WhisperModelConfig:
    """Configuration for Whisper models optimized for ml.g4dn.2xlarge"""
    model_name: str
    max_length: int = 448
    language: str = "km"
    task: str = "transcribe"
    batch_size_tiny: int = 16
    batch_size_base: int = 8
    gradient_accumulation_steps: int = 2
    learning_rate: float = 1e-5
    warmup_steps: int = 500
    max_steps: int = 5000
    eval_steps: int = 500
    save_steps: int = 1000

class WhisperModelManager:
    """Manage Whisper model configurations and initialization"""
    
    def __init__(self):
        self.models = {
            'tiny': WhisperModelConfig("openai/whisper-tiny"),
            'base': WhisperModelConfig("openai/whisper-base")
        }
    
    def load_model_components(self, model_size):
        """Load tokenizer, feature extractor, and model"""
        config = self.models[model_size]
        
        print(f"🔧 Loading Whisper {model_size.upper()} components...")
        
        # Load tokenizer
        tokenizer = WhisperTokenizer.from_pretrained(
            config.model_name, 
            language=config.language, 
            task=config.task
        )
        
        # Load feature extractor
        feature_extractor = WhisperFeatureExtractor.from_pretrained(config.model_name)
        
        # Load processor (combines tokenizer and feature extractor)
        processor = WhisperProcessor.from_pretrained(config.model_name)
        processor.tokenizer = tokenizer
        
        # Load model
        model = WhisperForConditionalGeneration.from_pretrained(config.model_name)
        
        # Configure model for Khmer
        model.generation_config.language = config.language
        model.generation_config.task = config.task
        model.generation_config.forced_decoder_ids = None
        
        print(f"✅ Whisper {model_size.upper()} loaded successfully!")
        print(f"   Parameters: {sum(p.numel() for p in model.parameters()):,}")
        print(f"   Trainable: {sum(p.numel() for p in model.parameters() if p.requires_grad):,}")
        
        return tokenizer, feature_extractor, processor, model, config

# Initialize model manager
model_manager = WhisperModelManager()

# Load Whisper Tiny components
print("🚀 Setting up Whisper models for training...")
tiny_tokenizer, tiny_feature_extractor, tiny_processor, tiny_model, tiny_config = model_manager.load_model_components('tiny')

print(f"\n📊 Model Configurations:")
print(f"  Whisper Tiny - Batch Size: {tiny_config.batch_size_tiny}")
print(f"  Whisper Base - Batch Size: {tiny_config.batch_size_base}")
print(f"  Max Length: {tiny_config.max_length}")
print(f"  Learning Rate: {tiny_config.learning_rate}")
print(f"  Gradient Accumulation: {tiny_config.gradient_accumulation_steps}")

# Check GPU memory
if torch.cuda.is_available():
    gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"\n💾 GPU Memory: {gpu_memory:.1f} GB")
    print("✅ Configurations optimized for ml.g4dn.2xlarge (16GB VRAM)")
    
    
from transformers import Seq2SeqTrainingArguments, Seq2SeqTrainer
from transformers import EarlyStoppingCallback
import evaluate
from dataclasses import dataclass
from typing import Any, Dict, List, Union
import torch

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Data collator for speech-to-text training - Fixed for input_features"""
    
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features: List[Dict[str, Union[List[int], torch.Tensor]]]) -> Dict[str, torch.Tensor]:
        # Handle both 'input_features' and model_input_names
        model_input_name = self.processor.model_input_names[0] if hasattr(self.processor, 'model_input_names') else 'input_features'
        
        # Extract input features - handle both naming conventions
        input_features = []
        for feature in features:
            if 'input_features' in feature:
                input_features.append({'input_features': feature['input_features']})
            elif model_input_name in feature:
                input_features.append({model_input_name: feature[model_input_name]})
            else:
                raise KeyError(f"Expected 'input_features' or '{model_input_name}' in feature dict, got keys: {list(feature.keys())}")
        
        # Extract labels
        label_features = [{"input_ids": feature["labels"]} for feature in features]

        # Pad input features
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
        
        # Pad labels
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        # Replace padding with -100 to ignore loss correctly
        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        # If bos token is appended in previous tokenization step,
        # cut bos token here as it's append later anyways
        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels

        return batch

def create_training_arguments(model_size, config, output_dir):
    """Create optimized training arguments for ml.g4dn.2xlarge"""
    
    # Adjust batch size based on model size
    if model_size == 'tiny':
        per_device_train_batch_size = config.batch_size_tiny
        per_device_eval_batch_size = config.batch_size_tiny
    else:  # base
        per_device_train_batch_size = config.batch_size_base
        per_device_eval_batch_size = config.batch_size_base
    
    return Seq2SeqTrainingArguments(
        output_dir=output_dir,
        per_device_train_batch_size=per_device_train_batch_size,
        per_device_eval_batch_size=per_device_eval_batch_size,
        gradient_accumulation_steps=config.gradient_accumulation_steps,
        learning_rate=config.learning_rate,
        warmup_steps=config.warmup_steps,
        max_steps=config.max_steps,
        gradient_checkpointing=True,  # Save memory
        fp16=True,  # Mixed precision for faster training
        evaluation_strategy="steps",
        eval_steps=config.eval_steps,
        save_steps=config.save_steps,
        logging_steps=100,
        report_to=["tensorboard"],
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",  # Use eval_loss instead of wer
        greater_is_better=False,
        save_total_limit=3,
        predict_with_generate=True,
        generation_max_length=config.max_length,
        dataloader_num_workers=4,
        remove_unused_columns=False,
        label_names=["labels"]
    )

def compute_metrics(eval_preds, tokenizer):
    """Compute WER and CER metrics with fallback for SageMaker"""
    import jiwer
    
    pred_ids, label_ids = eval_preds
    
    # Replace -100 with pad token id
    label_ids[label_ids == -100] = tokenizer.pad_token_id
    
    # Decode predictions and labels
    pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = tokenizer.batch_decode(label_ids, skip_special_tokens=True)
    
    # Compute metrics using jiwer as fallback
    try:
        # Try to use evaluate library first
        wer_metric = evaluate.load("wer")
        cer_metric = evaluate.load("cer")
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        cer = cer_metric.compute(predictions=pred_str, references=label_str)
    except Exception as e:
        print(f"⚠️ Evaluate library failed ({e}), using jiwer fallback...")
        # Use jiwer as fallback
        try:
            # Calculate WER using jiwer
            wer = jiwer.wer(label_str, pred_str)
            cer = jiwer.cer(label_str, pred_str)
        except Exception as e2:
            print(f"⚠️ jiwer also failed ({e2}), using basic accuracy...")
            # Basic accuracy fallback
            correct = sum(1 for p, l in zip(pred_str, label_str) if p.strip() == l.strip())
            accuracy = correct / len(pred_str) if len(pred_str) > 0 else 0
            wer = 1.0 - accuracy  # Approximate WER as 1 - accuracy
            cer = wer  # Use same value for CER
    
    return {"wer": wer, "cer": cer}

def setup_trainer(model, tokenizer, processor, config, datasets, model_size):
    """Setup Seq2SeqTrainer with all components"""
    
    # Create data collator
    data_collator = DataCollatorSpeechSeq2SeqWithPadding(
        processor=processor,
        decoder_start_token_id=model.generation_config.decoder_start_token_id,
    )
    
    # Create training arguments
    output_dir = f"./whisper-{model_size}-khmer"
    training_args = create_training_arguments(model_size, config, output_dir)
    
    # Create trainer
    trainer = Seq2SeqTrainer(
        args=training_args,
        model=model,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        data_collator=data_collator,
        compute_metrics=lambda eval_preds: compute_metrics(eval_preds, tokenizer),
        tokenizer=processor.feature_extractor,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    return trainer, training_args

print("⚙️ Training configuration setup complete!")
print("🎯 Optimized for ml.g4dn.2xlarge with 16GB VRAM")
print("✅ Mixed precision (FP16) enabled")
print("✅ Gradient checkpointing enabled for memory efficiency")
print("✅ Early stopping configured")

# ✅ Pre-Training Checklist - Run This Before Training
print("🔍 Checking Prerequisites for Whisper Training...")
print("=" * 50)

# Check if all required variables are defined
required_vars = {
    'datasets': 'Dataset loading (Cell 7)',
    'tiny_model': 'Whisper Tiny model (Cell 9)', 
    'tiny_tokenizer': 'Whisper Tiny tokenizer (Cell 9)',
    'tiny_processor': 'Whisper Tiny processor (Cell 9)',
    'tiny_config': 'Whisper Tiny config (Cell 9)',
    'setup_trainer': 'Training setup function (Cell 11)'
}

missing_vars = []
available_vars = []

for var_name, description in required_vars.items():
    try:
        if var_name in locals() or var_name in globals():
            available_vars.append(f"✅ {var_name} - {description}")
        else:
            missing_vars.append(f"❌ {var_name} - {description}")
    except:
        missing_vars.append(f"❌ {var_name} - {description}")

# Show status
print("🎯 Available Variables:")
for var in available_vars:
    print(f"   {var}")

if missing_vars:
    print(f"\n⚠️ Missing Variables ({len(missing_vars)}):")
    for var in missing_vars:
        print(f"   {var}")
    
    print(f"\n💡 Before training, you need to run these cells in order:")
    print(f"   1. Cell 3: SageMaker Setup")
    print(f"   2. Cell 5: Package Installation") 
    print(f"   3. Cell 7: Dataset Loading")
    print(f"   4. Cell 9: Model Configuration")
    print(f"   5. Cell 11: Training Setup")
    print(f"   6. Then you can run the training cells")
    
    print(f"\n🚫 Cannot start training - missing prerequisites!")
    
else:
    print(f"\n🎉 All prerequisites available!")
    print(f"✅ Ready to start Whisper training")
    
    # Show some stats if datasets is available
    try:
        if 'datasets' in locals() or 'datasets' in globals():
            print(f"\n📊 Dataset Info:")
            for split in datasets.keys():
                print(f"   {split}: {len(datasets[split]):,} samples")
    except:
        pass
        
print("\n" + "=" * 50)


# 🔄 CRITICAL: Preprocess Raw Dataset for Training
# This converts raw datasets (audio_filepath, text) -> training format (input_features, labels)

import torch
import librosa
import boto3
from io import BytesIO

def preprocess_dataset_for_training(raw_datasets, feature_extractor, tokenizer, max_samples=None):
    """Convert raw dataset with audio_filepath/text to training format with input_features/labels"""
    print("🔄 Converting datasets to training format...")
    
    s3_client = boto3.client('s3', region_name='ap-southeast-1')
    processed_datasets = {}
    
    for split_name, dataset in raw_datasets.items():
        print(f"📊 Processing {split_name}...")
        
        # Limit samples if specified
        if max_samples and len(dataset) > max_samples:
            dataset = dataset.select(range(max_samples))
            print(f"🔧 Limited to {max_samples} samples")
        
        processed_examples = []
        errors = 0
        
        for i, example in enumerate(dataset):
            try:
                if i % 500 == 0:
                    print(f"   Progress: {i}/{len(dataset)}")
                
                audio_array = None
                sampling_rate = 16000
                
                # Get audio file path
                audio_path = example['audio_filepath']
                
                # Handle HuggingFace Audio dict format
                if isinstance(audio_path, dict):
                    if 'array' in audio_path:
                        audio_array = audio_path['array']
                        sampling_rate = audio_path.get('sampling_rate', 16000)
                        if sampling_rate != 16000:
                            audio_array = librosa.resample(audio_array, orig_sr=sampling_rate, target_sr=16000)
                    elif 'path' in audio_path:
                        audio_path = audio_path['path']
                    else:
                        errors += 1
                        continue
                
                # Load audio from path if not already loaded
                if audio_array is None:
                    if isinstance(audio_path, str) and audio_path.startswith('s3://'):
                        # Parse S3 path
                        path_parts = audio_path[5:].split('/', 1)
                        bucket_name = path_parts[0]
                        s3_key = path_parts[1]
                        
                        try:
                            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)
                            audio_bytes = response['Body'].read()
                            audio_array, _ = librosa.load(BytesIO(audio_bytes), sr=16000)
                        except Exception:
                            errors += 1
                            if errors > 20:
                                raise Exception("Too many S3 errors!")
                            continue
                    elif isinstance(audio_path, str):
                        try:
                            audio_array, _ = librosa.load(audio_path, sr=16000)
                        except Exception:
                            errors += 1
                            continue
                    else:
                        errors += 1
                        continue
                # Convert audio to input_features
                input_features = feature_extractor(
                    audio_array, 
                    sampling_rate=16000, 
                    return_tensors="pt"
                ).input_features[0]
                
                # Convert text to labels
                text = str(example['text']).strip()
                if not text:
                    continue
                    
                labels = tokenizer(text).input_ids
                
                processed_example = {
                    'input_features': input_features,
                    'labels': labels,
                    'text': text,
                    'duration': example.get('duration', 0.0),
                    'source': example.get('source', 'unknown')
                }
                
                processed_examples.append(processed_example)
                
            except Exception:
                errors += 1
                if errors > 50:
                    raise Exception("Too many processing errors!")
        
        # Create processed dataset
        if processed_examples:
            from datasets import Dataset
            processed_dataset = Dataset.from_list(processed_examples)
            processed_datasets[split_name] = processed_dataset
            
            print(f"✅ {split_name}: {len(processed_examples)} samples processed ({errors} errors)")
        else:
            raise Exception(f"No valid samples processed for {split_name}!")
    
    if not processed_datasets:
        raise Exception("Preprocessing failed!")
    
    from datasets import DatasetDict
    final_datasets = DatasetDict(processed_datasets)
    
    print(f"🎉 Preprocessing complete: {sum(len(d) for d in processed_datasets.values())} total samples")
    return final_datasets

# Execute preprocessing
print("🚀 Starting dataset preprocessing...")

try:
    # Apply preprocessing
    processed_datasets = preprocess_dataset_for_training(
        datasets, 
        tiny_feature_extractor, 
        tiny_tokenizer,
        max_samples=None
    )
    
    # Replace datasets variable with processed version
    datasets = processed_datasets
    print("✅ Datasets preprocessed and ready for training!")
    
except Exception as e:
    print(f"❌ Preprocessing failed: {e}")
    print("💡 Check dataset loading and model configuration")
    raise e

import time
from datetime import datetime
import os

print("🚀 Starting Whisper Tiny Fine-tuning...")
print("=" * 60)

# Setup trainer for Tiny model
tiny_trainer, tiny_training_args = setup_trainer(
    model=tiny_model,
    tokenizer=tiny_tokenizer, 
    processor=tiny_processor,
    config=tiny_config,
    datasets=datasets,
    model_size="tiny"
)

# Print training info
print(f"📊 Whisper Tiny Training Configuration:")
print(f"   Model Parameters: {sum(p.numel() for p in tiny_model.parameters()):,}")
print(f"   Batch Size: {tiny_training_args.per_device_train_batch_size}")
print(f"   Gradient Accumulation: {tiny_training_args.gradient_accumulation_steps}")
print(f"   Effective Batch Size: {tiny_training_args.per_device_train_batch_size * tiny_training_args.gradient_accumulation_steps}")
print(f"   Max Steps: {tiny_training_args.max_steps}")
print(f"   Learning Rate: {tiny_training_args.learning_rate}")
print(f"   Output Directory: {tiny_training_args.output_dir}")

# Check GPU memory before training
if torch.cuda.is_available():
    torch.cuda.empty_cache()
    allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
    cached_memory = torch.cuda.memory_reserved(0) / 1024**3
    print(f"\n💾 Pre-training GPU Memory:")
    print(f"   Allocated: {allocated_memory:.2f} GB")
    print(f"   Cached: {cached_memory:.2f} GB")

print(f"\n⏰ Training Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("🎯 Expected training time: ~3-4 hours")

# Start training
start_time = time.time()

try:
    # Train the model
    tiny_trainer.train()
    
    training_time = time.time() - start_time
    print(f"\n🎉 Whisper Tiny Training Complete!")
    print(f"⏱️ Total Training Time: {training_time/3600:.2f} hours")
    
    # Save the final model
    tiny_trainer.save_model()
    tiny_trainer.tokenizer.save_pretrained(tiny_training_args.output_dir)
    
    print(f"💾 Model saved to: {tiny_training_args.output_dir}")
    
    # Get final metrics
    final_logs = tiny_trainer.state.log_history[-1]
    if 'eval_wer' in final_logs:
        print(f"📊 Final WER: {final_logs['eval_wer']:.4f}")
        print(f"📊 Final CER: {final_logs.get('eval_cer', 'N/A'):.4f}")
    
    # Memory usage after training
    if torch.cuda.is_available():
        allocated_memory = torch.cuda.memory_allocated(0) / 1024**3
        max_memory = torch.cuda.max_memory_allocated(0) / 1024**3
        print(f"\n💾 Post-training GPU Memory:")
        print(f"   Current: {allocated_memory:.2f} GB")
        print(f"   Peak: {max_memory:.2f} GB")
        
        # Clear cache for next model
        torch.cuda.empty_cache()
        print("🧹 GPU cache cleared for next model")
    
except Exception as e:
    print(f"❌ Training failed: {e}")
    import traceback
    traceback.print_exc()

print("=" * 60)


import boto3
import tarfile
from pathlib import Path
import json
from sagemaker.pytorch import PyTorchModel
from sagemaker import get_execution_role

class WhisperModelDeployment:
    """Handle model packaging and deployment to SageMaker"""
    
    def __init__(self, bucket, prefix, role):
        self.bucket = bucket
        self.prefix = prefix
        self.role = role
        self.s3_client = boto3.client('s3')
        self.sagemaker_client = boto3.client('sagemaker')
    
    def create_model_tar(self, model_dir, tar_name):
        """Create tar.gz file for SageMaker model"""
        print(f"📦 Creating model archive: {tar_name}")
        
        with tarfile.open(tar_name, 'w:gz') as tar:
            for file_path in Path(model_dir).rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(model_dir)
                    tar.add(file_path, arcname=arcname)
        
        print(f"✅ Model archive created: {tar_name}")
        return tar_name
    
    def upload_to_s3(self, file_path, s3_key):
        """Upload model to S3"""
        print(f"☁️ Uploading to S3: s3://{self.bucket}/{s3_key}")
        
        self.s3_client.upload_file(file_path, self.bucket, s3_key)
        s3_uri = f"s3://{self.bucket}/{s3_key}"
        
        print(f"✅ Upload complete: {s3_uri}")
        return s3_uri
    
    def create_inference_script(self, model_dir):
        """Create inference script for SageMaker endpoint"""
        inference_script = '''import torch
import json
import librosa
from transformers import WhisperForConditionalGeneration, WhisperProcessor

def model_fn(model_dir):
    model = WhisperForConditionalGeneration.from_pretrained(model_dir)
    processor = WhisperProcessor.from_pretrained(model_dir)
    return {'model': model, 'processor': processor}

def input_fn(request_body, request_content_type):
    if request_content_type == 'application/json':
        input_data = json.loads(request_body)
        if 'audio_path' in input_data:
            audio, sr = librosa.load(input_data['audio_path'], sr=16000)
        else:
            raise ValueError("Must provide 'audio_path'")
        return audio
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

def predict_fn(input_data, model_dict):
    model = model_dict['model']
    processor = model_dict['processor']
    
    input_features = processor(input_data, sampling_rate=16000, return_tensors="pt").input_features
    
    with torch.no_grad():
        predicted_ids = model.generate(input_features, max_length=448)
    
    transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
    return {"transcription": transcription}

def output_fn(prediction, content_type):
    if content_type == 'application/json':
        return json.dumps(prediction)
    else:
        raise ValueError(f"Unsupported content type: {content_type}")
'''
        
        script_path = Path(model_dir) / "inference.py"
        with open(script_path, 'w') as f:
            f.write(inference_script)
        
        print(f"✅ Inference script created")
        return script_path
    
    def deploy_model(self, model_s3_uri, model_name, instance_type="ml.t2.medium"):
        """Deploy model to SageMaker endpoint"""
        print(f"🚀 Deploying model: {model_name}")
        
        # Create PyTorch model
        pytorch_model = PyTorchModel(
            model_data=model_s3_uri,
            role=self.role,
            py_version='py39',
            framework_version='1.12',
            entry_point='inference.py'
        )
        
        # Deploy to endpoint
        predictor = pytorch_model.deploy(
            initial_instance_count=1,
            instance_type=instance_type,
            endpoint_name=f"{model_name}-endpoint"
        )
        
        print(f"✅ Model deployed to endpoint: {model_name}-endpoint")
        return predictor

# Initialize deployment manager
deployment_manager = WhisperModelDeployment(bucket, prefix, role)

# Deploy trained models to S3
if os.path.exists("./whisper-tiny-khmer"):
    print("🚀 Preparing Whisper Tiny for deployment...")
    deployment_manager.create_inference_script("./whisper-tiny-khmer")
    tiny_tar = deployment_manager.create_model_tar("./whisper-tiny-khmer", "whisper-tiny-khmer.tar.gz")
    tiny_s3_key = f"{prefix}/models/whisper-tiny-khmer.tar.gz"
    tiny_s3_uri = deployment_manager.upload_to_s3(tiny_tar, tiny_s3_key)
    print(f"✅ Whisper Tiny uploaded: {tiny_s3_uri}")

if os.path.exists("./whisper-base-khmer"):
    print("🚀 Preparing Whisper Base for deployment...")
    deployment_manager.create_inference_script("./whisper-base-khmer")
    base_tar = deployment_manager.create_model_tar("./whisper-base-khmer", "whisper-base-khmer.tar.gz")
    base_s3_key = f"{prefix}/models/whisper-base-khmer.tar.gz"
    base_s3_uri = deployment_manager.upload_to_s3(base_tar, base_s3_key)
    print(f"✅ Whisper Base uploaded: {base_s3_uri}")

# Create summary report
summary_report = {
    "training_date": datetime.now().isoformat(),
    "instance_type": "ml.g4dn.2xlarge",
    "dataset": "Khmer Speech Dataset",
    "models_trained": [],
    "s3_artifacts": []
}

if os.path.exists("./whisper-tiny-khmer"):
    summary_report["models_trained"].append("Whisper Tiny")
    if 'tiny_s3_uri' in locals():
        summary_report["s3_artifacts"].append({"model": "Whisper Tiny", "uri": tiny_s3_uri})

if os.path.exists("./whisper-base-khmer"):
    summary_report["models_trained"].append("Whisper Base")
    if 'base_s3_uri' in locals():
        summary_report["s3_artifacts"].append({"model": "Whisper Base", "uri": base_s3_uri})

# Save summary report
with open("training_summary.json", "w") as f:
    json.dump(summary_report, f, indent=2)

print("🎉 Training and deployment complete!")
print(f"📊 Models trained: {len(summary_report['models_trained'])}")
print(f"☁️ S3 artifacts: {len(summary_report['s3_artifacts'])}")
print(f"📝 Summary saved to: training_summary.json")

if summary_report['s3_artifacts']:
    print("📍 Model S3 locations:")
    for artifact in summary_report['s3_artifacts']:
        print(f"   {artifact['model']}: {artifact['uri']}")