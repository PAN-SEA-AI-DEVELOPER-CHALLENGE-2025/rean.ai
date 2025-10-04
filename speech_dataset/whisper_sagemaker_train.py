#!/usr/bin/env python3
"""
SageMaker Training Script for Whisper Fine-tuning on Khmer Dataset
================================================================

This script runs inside the SageMaker training container.
Optimized for ml.g4dn.2xlarge instances (1 GPU, 32GB RAM).
"""

import os
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

import torch
import numpy as np
import pandas as pd
from datasets import Dataset, DatasetDict, Audio
from transformers import (
    WhisperForConditionalGeneration,
    WhisperTokenizer,
    WhisperProcessor,
    WhisperFeatureExtractor,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback
)
from dataclasses import dataclass
import evaluate
import librosa
import soundfile as sf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DataCollatorSpeechSeq2SeqWithPadding:
    """Custom data collator for Whisper fine-tuning"""
    processor: Any
    decoder_start_token_id: int

    def __call__(self, features):
        input_features = [{"input_features": feature["input_features"]} for feature in features]
        batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")

        label_features = [{"input_ids": feature["labels"]} for feature in features]
        labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")

        labels = labels_batch["input_ids"].masked_fill(labels_batch.attention_mask.ne(1), -100)

        if (labels[:, 0] == self.decoder_start_token_id).all().cpu().item():
            labels = labels[:, 1:]

        batch["labels"] = labels
        return batch

class KhmerWhisperTrainer:
    """Whisper fine-tuning trainer for Khmer ASR"""
    
    def __init__(self, args):
        self.args = args
        self.setup_model_and_processor()
        self.wer_metric = evaluate.load("wer")
        
    def setup_model_and_processor(self):
        """Initialize Whisper model and processor"""
        logger.info(f"🔧 Loading Whisper model: {self.args.model_name_or_path}")
        
        self.processor = WhisperProcessor.from_pretrained(
            self.args.model_name_or_path,
            language=self.args.language,
            task=self.args.task
        )
        
        self.model = WhisperForConditionalGeneration.from_pretrained(
            self.args.model_name_or_path,
            dropout_rate=self.args.dropout_rate
        )
        
        # Configure model for Khmer
        self.model.generation_config.language = self.args.language
        self.model.generation_config.task = self.args.task
        self.model.generation_config.forced_decoder_ids = None
        
        logger.info(f"✅ Model loaded: {self.model.config.name_or_path}")
        logger.info(f"   📊 Parameters: {self.model.num_parameters():,}")
        
    def load_dataset(self):
        """Load and preprocess the Khmer dataset"""
        logger.info("📂 Loading Khmer dataset...")
        
        data_path = Path(os.environ.get("SM_CHANNEL_TRAINING", "/opt/ml/input/data/training"))
        
        # Load train/validation/test manifests
        datasets = {}
        for split in ["train", "validation", "test"]:
            manifest_path = data_path / f"{split}_manifest.json"
            
            if manifest_path.exists():
                logger.info(f"   📄 Loading {split}: {manifest_path}")
                
                # Load manifest
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest_data = [json.loads(line) for line in f]
                
                # Convert to dataset
                df = pd.DataFrame(manifest_data)
                
                # Ensure audio paths are absolute
                df["audio_filepath"] = df["audio_filepath"].apply(
                    lambda x: str(data_path / x) if not os.path.isabs(x) else x
                )
                
                # Filter by duration if specified
                if hasattr(self.args, 'max_duration_in_seconds'):
                    df = df[df["duration"] <= self.args.max_duration_in_seconds]
                if hasattr(self.args, 'min_duration_in_seconds'):
                    df = df[df["duration"] >= self.args.min_duration_in_seconds]
                
                # Create HuggingFace dataset
                dataset = Dataset.from_pandas(df)
                dataset = dataset.cast_column("audio_filepath", Audio(sampling_rate=16000))
                
                datasets[split] = dataset
                logger.info(f"   ✅ {split}: {len(dataset)} samples")
        
        # Create DatasetDict
        dataset_dict = DatasetDict(datasets)
        
        # Preprocess datasets
        logger.info("🔄 Preprocessing audio and text...")
        dataset_dict = dataset_dict.map(
            self.prepare_dataset,
            remove_columns=dataset_dict["train"].column_names,
            num_proc=self.args.preprocessing_num_workers,
            desc="Preprocessing"
        )
        
        return dataset_dict
    
    def prepare_dataset(self, batch):
        """Preprocess individual samples"""
        # Load and preprocess audio
        audio = batch["audio_filepath"]["array"]
        
        # Extract features
        input_features = self.processor.feature_extractor(
            audio, 
            sampling_rate=16000, 
            return_tensors="pt"
        ).input_features[0]
        
        # Tokenize text
        labels = self.processor.tokenizer(batch["text"]).input_ids
        
        return {
            "input_features": input_features,
            "labels": labels
        }
    
    def compute_metrics(self, pred):
        """Compute WER and other metrics"""
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        
        # Replace -100 with pad token id
        label_ids[label_ids == -100] = self.processor.tokenizer.pad_token_id
        
        # Decode predictions and references
        pred_str = self.processor.tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = self.processor.tokenizer.batch_decode(label_ids, skip_special_tokens=True)
        
        # Compute WER
        wer = 100 * self.wer_metric.compute(predictions=pred_str, references=label_str)
        
        return {"wer": wer}
    
    def train(self):
        """Main training loop"""
        logger.info("🚀 Starting Whisper fine-tuning...")
        
        # Load dataset
        dataset = self.load_dataset()
        
        # Data collator
        data_collator = DataCollatorSpeechSeq2SeqWithPadding(
            processor=self.processor,
            decoder_start_token_id=self.model.config.decoder_start_token_id
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=os.environ.get("SM_MODEL_DIR", "/opt/ml/model"),
            
            # Training parameters
            per_device_train_batch_size=self.args.per_device_train_batch_size,
            per_device_eval_batch_size=self.args.per_device_eval_batch_size,
            gradient_accumulation_steps=self.args.gradient_accumulation_steps,
            learning_rate=self.args.learning_rate,
            weight_decay=self.args.weight_decay,
            max_grad_norm=self.args.max_grad_norm,
            
            # Schedule
            max_steps=self.args.max_steps,
            warmup_steps=self.args.warmup_steps,
            
            # Evaluation and saving
            eval_strategy="steps",
            eval_steps=self.args.eval_steps,
            save_strategy="steps",
            save_steps=self.args.save_steps,
            save_total_limit=3,
            
            # Logging
            logging_steps=self.args.logging_steps,
            report_to=[],  # Disable wandb/tensorboard for SageMaker
            
            # Optimization
            fp16=self.args.fp16,
            dataloader_num_workers=self.args.dataloader_num_workers,
            group_by_length=self.args.group_by_length,
            
            # Generation for evaluation
            predict_with_generate=self.args.predict_with_generate,
            generation_max_length=self.args.generation_max_length,
            generation_num_beams=self.args.generation_num_beams,
            
            # Load best model at end
            load_best_model_at_end=True,
            metric_for_best_model="wer",
            greater_is_better=False,
        )
        
        # Create trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset["validation"] if "validation" in dataset else dataset["test"],
            data_collator=data_collator,
            compute_metrics=self.compute_metrics,
            tokenizer=self.processor.feature_extractor,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
        )
        
        # Start training
        logger.info("🎯 Training started!")
        trainer.train()
        
        # Save final model
        logger.info("💾 Saving model...")
        trainer.save_model()
        self.processor.save_pretrained(training_args.output_dir)
        
        # Final evaluation
        if "test" in dataset:
            logger.info("🧪 Final evaluation on test set...")
            test_results = trainer.evaluate(dataset["test"])
            logger.info(f"📊 Test WER: {test_results['eval_wer']:.2f}%")
            
            # Save test results
            with open(os.path.join(training_args.output_dir, "test_results.json"), "w") as f:
                json.dump(test_results, f, indent=2)
        
        logger.info("✅ Training completed!")

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Fine-tune Whisper on Khmer dataset")
    
    # Model arguments
    parser.add_argument("--model_name_or_path", type=str, default="openai/whisper-tiny")
    parser.add_argument("--language", type=str, default="km")
    parser.add_argument("--task", type=str, default="transcribe")
    
    # Training arguments
    parser.add_argument("--per_device_train_batch_size", type=int, default=16)
    parser.add_argument("--per_device_eval_batch_size", type=int, default=32)
    parser.add_argument("--gradient_accumulation_steps", type=int, default=2)
    parser.add_argument("--learning_rate", type=float, default=1e-5)
    parser.add_argument("--weight_decay", type=float, default=0.01)
    parser.add_argument("--max_grad_norm", type=float, default=1.0)
    parser.add_argument("--dropout_rate", type=float, default=0.1)
    
    # Schedule arguments
    parser.add_argument("--max_steps", type=int, default=10000)
    parser.add_argument("--warmup_steps", type=int, default=1000)
    parser.add_argument("--eval_steps", type=int, default=1000)
    parser.add_argument("--save_steps", type=int, default=1000)
    parser.add_argument("--logging_steps", type=int, default=100)
    
    # Data arguments
    parser.add_argument("--max_duration_in_seconds", type=float, default=30.0)
    parser.add_argument("--min_duration_in_seconds", type=float, default=1.0)
    parser.add_argument("--preprocessing_num_workers", type=int, default=8)
    
    # Optimization arguments
    parser.add_argument("--fp16", action="store_true", default=True)
    parser.add_argument("--dataloader_num_workers", type=int, default=4)
    parser.add_argument("--group_by_length", action="store_true", default=True)
    
    # Generation arguments
    parser.add_argument("--predict_with_generate", action="store_true", default=True)
    parser.add_argument("--generation_max_length", type=int, default=225)
    parser.add_argument("--generation_num_beams", type=int, default=1)
    
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_args()
    
    logger.info("🚀 SageMaker Whisper Fine-tuning Starting...")
    logger.info(f"   🎯 Model: {args.model_name_or_path}")
    logger.info(f"   🗣️ Language: {args.language}")
    logger.info(f"   💻 Device: {'GPU' if torch.cuda.is_available() else 'CPU'}")
    
    # Create trainer and start training
    trainer = KhmerWhisperTrainer(args)
    trainer.train()

if __name__ == "__main__":
    main()