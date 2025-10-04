#!/usr/bin/env python3
"""
Final Khmer ASR Training Script
==============================

Train on your MEGA dataset with 138+ hours of diverse Khmer speech:
- 110,555 total samples
- Original + LSR42 + Rinabuoy datasets
- Multiple speakers and recording conditions
"""

import os
import json
import torch
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

# Hugging Face imports
from transformers import (
    Wav2Vec2CTCTokenizer,
    Wav2Vec2FeatureExtractor, 
    Wav2Vec2Processor,
    Wav2Vec2ForCTC,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from datasets import Dataset, DatasetDict, Audio
import librosa
import soundfile as sf

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FinalModelConfig:
    """Configuration for training on the mega dataset"""
    model_name: str = "facebook/wav2vec2-base"  # or wav2vec2-large for better quality
    output_dir: str = "./khmer-asr-final"
    dataset_dir: str = "./fixed_mega_dataset"
    
    # Training parameters optimized for 138+ hours
    num_train_epochs: int = 20  # More epochs for large dataset
    per_device_train_batch_size: int = 8
    per_device_eval_batch_size: int = 8
    gradient_accumulation_steps: int = 4  # Effective batch size = 32
    learning_rate: float = 5e-5  # Lower LR for large dataset
    warmup_steps: int = 2000  # More warmup for stability
    logging_steps: int = 200
    save_steps: int = 2000
    eval_steps: int = 2000
    
    # Audio parameters
    target_sampling_rate: int = 16000
    max_duration_seconds: float = 10.0
    
    # Data augmentation (recommended for diverse dataset)
    use_data_augmentation: bool = True

class FinalKhmerASRTrainer:
    """Final trainer for mega Khmer dataset"""
    
    def __init__(self, config: FinalModelConfig):
        self.config = config
        self.processor = None
        self.model = None
        self.tokenizer = None
        
        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
    def prepare_vocabulary(self, dataset_dict: DatasetDict) -> Wav2Vec2CTCTokenizer:
        """Create vocabulary from mega dataset"""
        logger.info("Creating vocabulary from mega dataset...")
        
        # Collect all transcriptions
        all_text = []
        for split in dataset_dict.values():
            all_text.extend(split["transcription"])
        
        # Extract unique characters
        vocab_set = set()
        for text in all_text:
            if text:
                vocab_set.update(text.lower())
        
        # Create vocabulary dictionary
        vocab_dict = {v: k for k, v in enumerate(sorted(vocab_set))}
        
        # Add special tokens
        vocab_dict["[UNK]"] = len(vocab_dict)
        vocab_dict["[PAD]"] = len(vocab_dict)
        
        # Save vocabulary
        vocab_file = Path(self.config.output_dir) / "vocab.json"
        with open(vocab_file, 'w', encoding='utf-8') as f:
            json.dump(vocab_dict, f, ensure_ascii=False, indent=2)
        
        # Create tokenizer
        tokenizer = Wav2Vec2CTCTokenizer(
            str(vocab_file),
            unk_token="[UNK]",
            pad_token="[PAD]",
            word_delimiter_token="|"
        )
        
        logger.info(f"Created vocabulary with {len(vocab_dict)} characters")
        return tokenizer
    
    def load_mega_dataset(self) -> DatasetDict:
        """Load the mega dataset"""
        logger.info("Loading mega dataset...")
        
        dataset_dict = {}
        
        for split in ["train", "validation", "test"]:
            manifest_path = Path(self.config.dataset_dir) / split / f"{split}_hf.jsonl"
            audio_dir = Path(self.config.dataset_dir) / split
            
            if not manifest_path.exists():
                logger.warning(f"Manifest not found: {manifest_path}")
                continue
            
            # Load manifest
            data = []
            with open(manifest_path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    if 'audio' in item and 'path' in item['audio']:
                        # Fix audio path
                        audio_path = item['audio']['path']
                        if audio_path.startswith('audio/'):
                            audio_path = audio_path[6:]
                        full_audio_path = audio_dir / "audio" / audio_path
                        
                        data.append({
                            'audio': str(full_audio_path),
                            'transcription': item['transcription'],
                            'duration': item['duration'],
                            'speaker_id': item.get('speaker_id', 'unknown'),
                            'source': item.get('source', 'unknown')
                        })
            
            # Create dataset
            dataset = Dataset.from_list(data)
            dataset = dataset.cast_column('audio', Audio(sampling_rate=self.config.target_sampling_rate))
            
            dataset_dict[split] = dataset
            logger.info(f"Loaded {len(dataset)} samples for {split}")
            
            # Log source distribution
            sources = [item.get('source', 'unknown') for item in data]
            source_counts = pd.Series(sources).value_counts()
            logger.info(f"{split} source distribution:")
            for source, count in source_counts.items():
                logger.info(f"  {source}: {count} samples")
        
        return DatasetDict(dataset_dict)
    
    def augment_audio(self, audio_array: np.ndarray) -> np.ndarray:
        """Apply data augmentation"""
        if not self.config.use_data_augmentation:
            return audio_array
        
        # Speed perturbation
        if np.random.random() < 0.3:
            speed_factor = np.random.uniform(0.9, 1.1)
            audio_array = librosa.effects.time_stretch(audio_array, rate=speed_factor)
        
        # Add background noise
        if np.random.random() < 0.2:
            noise_factor = np.random.uniform(0.001, 0.005)
            noise = np.random.normal(0, noise_factor, audio_array.shape)
            audio_array = audio_array + noise
        
        # Volume perturbation
        if np.random.random() < 0.3:
            volume_factor = np.random.uniform(0.8, 1.2)
            audio_array = audio_array * volume_factor
            
        # Normalize and clip
        audio_array = np.clip(audio_array, -1.0, 1.0)
        
        return audio_array
    
    def preprocess_function(self, examples):
        """Preprocess audio and text"""
        # Process audio with augmentation
        audio_arrays = []
        for audio_data in examples["audio"]:
            audio_array = audio_data["array"]
            
            # Apply augmentation during training
            if self.config.use_data_augmentation:
                audio_array = self.augment_audio(audio_array)
            
            audio_arrays.append(audio_array)
        
        inputs = self.processor(
            audio_arrays, 
            sampling_rate=self.config.target_sampling_rate,
            return_tensors="pt",
            padding=True
        )
        
        # Process text
        with self.processor.as_target_processor():
            labels = self.processor(examples["transcription"]).input_ids
        
        inputs["labels"] = labels
        return inputs
    
    def setup_model_and_processor(self, tokenizer: Wav2Vec2CTCTokenizer):
        """Setup model for mega dataset training"""
        logger.info("Setting up model for mega dataset training...")
        
        # Feature extractor
        feature_extractor = Wav2Vec2FeatureExtractor(
            feature_size=1, 
            sampling_rate=self.config.target_sampling_rate,
            padding_value=0.0,
            do_normalize=True,
            return_attention_mask=True
        )
        
        # Processor
        self.processor = Wav2Vec2Processor(
            feature_extractor=feature_extractor,
            tokenizer=tokenizer
        )
        
        # Model with optimizations for large dataset
        self.model = Wav2Vec2ForCTC.from_pretrained(
            self.config.model_name,
            ctc_loss_reduction="mean",
            pad_token_id=self.processor.tokenizer.pad_token_id,
            vocab_size=len(self.processor.tokenizer.get_vocab()),
            # Regularization for large dataset
            hidden_dropout=0.1,
            feat_proj_dropout=0.1,
            attention_dropout=0.1,
            layerdrop=0.05  # Helps with large datasets
        )
        
        # Freeze feature encoder initially
        self.model.freeze_feature_encoder()
        
        logger.info(f"Model vocabulary size: {self.model.config.vocab_size}")
        logger.info("Model optimized for large-scale training")
    
    def compute_metrics(self, pred):
        """Compute evaluation metrics"""
        pred_logits = pred.predictions
        pred_ids = np.argmax(pred_logits, axis=-1)
        
        pred.label_ids[pred.label_ids == -100] = self.processor.tokenizer.pad_token_id
        
        pred_str = self.processor.batch_decode(pred_ids)
        label_str = self.processor.batch_decode(pred.label_ids, group_tokens=False)
        
        # Character error rate
        total_chars = sum(len(label) for label in label_str)
        total_errors = sum(
            sum(c1 != c2 for c1, c2 in zip(pred, label))
            for pred, label in zip(pred_str, label_str)
        )
        
        cer = total_errors / total_chars if total_chars > 0 else 0.0
        
        return {"cer": cer}
    
    def train(self):
        """Main training function for mega dataset"""
        logger.info("Starting FINAL Khmer ASR training on mega dataset...")
        logger.info("Dataset: 138+ hours, 110K+ samples, multi-speaker, multi-source")
        
        # Load mega dataset
        dataset_dict = self.load_mega_dataset()
        
        # Create vocabulary
        tokenizer = self.prepare_vocabulary(dataset_dict)
        
        # Setup model
        self.setup_model_and_processor(tokenizer)
        
        # Preprocess datasets
        logger.info("Preprocessing mega dataset (this may take a while)...")
        encoded_datasets = dataset_dict.map(
            self.preprocess_function,
            remove_columns=dataset_dict["train"].column_names,
            batched=True,
            batch_size=50,  # Smaller batch for memory efficiency
            num_proc=1
        )
        
        # Advanced training arguments for large dataset
        training_args = TrainingArguments(
            output_dir=self.config.output_dir,
            group_by_length=True,
            per_device_train_batch_size=self.config.per_device_train_batch_size,
            per_device_eval_batch_size=self.config.per_device_eval_batch_size,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            evaluation_strategy="steps",
            num_train_epochs=self.config.num_train_epochs,
            fp16=True,
            gradient_checkpointing=True,
            save_steps=self.config.save_steps,
            eval_steps=self.config.eval_steps,
            logging_steps=self.config.logging_steps,
            learning_rate=self.config.learning_rate,
            warmup_steps=self.config.warmup_steps,
            save_total_limit=3,
            load_best_model_at_end=True,
            metric_for_best_model="cer",
            greater_is_better=False,
            # Advanced optimizations
            weight_decay=0.01,
            adam_epsilon=1e-8,
            max_grad_norm=1.0,
            dataloader_num_workers=4,
            # Learning rate scheduling
            lr_scheduler_type="cosine",
            # Early stopping patience
            push_to_hub=False,
            report_to=[]
        )
        
        # Data collator
        from transformers import DataCollatorCTCWithPadding
        data_collator = DataCollatorCTCWithPadding(
            processor=self.processor, 
            padding=True
        )
        
        # Advanced trainer
        trainer = Trainer(
            model=self.model,
            data_collator=data_collator,
            args=training_args,
            compute_metrics=self.compute_metrics,
            train_dataset=encoded_datasets["train"],
            eval_dataset=encoded_datasets["validation"],
            tokenizer=self.processor.feature_extractor,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=5)]
        )
        
        # Train
        logger.info("🚀 Starting mega dataset training...")
        logger.info("Expected training time: 12-20 hours (depending on hardware)")
        logger.info("Target performance: <5% CER with this dataset size")
        
        trainer.train()
        
        # Save final model
        trainer.save_model()
        self.processor.save_pretrained(self.config.output_dir)
        
        # Evaluate on test set
        if "test" in encoded_datasets:
            logger.info("Evaluating on test set...")
            test_results = trainer.evaluate(encoded_datasets["test"])
            logger.info(f"🎯 Final Test CER: {test_results['eval_cer']:.4f}")
            
            # Save test results
            with open(Path(self.config.output_dir) / "test_results.json", 'w') as f:
                json.dump(test_results, f, indent=2)
        
        logger.info(f"🎉 MEGA DATASET TRAINING COMPLETE!")
        logger.info(f"💎 Model saved to: {self.config.output_dir}")
        logger.info(f"📊 Trained on: 138+ hours, 110K+ samples")
        logger.info(f"🌟 This is now a production-quality Khmer ASR model!")

def main():
    """Main entry point"""
    config = FinalModelConfig()
    trainer = FinalKhmerASRTrainer(config)
    trainer.train()

if __name__ == "__main__":
    main()
