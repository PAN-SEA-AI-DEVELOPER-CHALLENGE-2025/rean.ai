#!/usr/bin/env python3
"""
SageMaker Whisper Fine-tuning for Khmer ASR
==========================================

Fine-tune Whisper Tiny and Base models on your 138+ hour Khmer dataset
using SageMaker ml.g4dn.2xlarge instances.
"""

import json
import boto3
import sagemaker
from sagemaker.pytorch import PyTorch
from sagemaker.inputs import TrainingInput
from datetime import datetime
import os

class SageMakerWhisperTrainer:
    """SageMaker Whisper training job manager"""
    
    def __init__(self, region='us-east-1'):
        self.session = sagemaker.Session()
        self.role = sagemaker.get_execution_role()
        self.bucket = self.session.default_bucket()
        self.region = region
        
        print(f"🚀 SageMaker Whisper Trainer Initialized")
        print(f"   📦 S3 Bucket: {self.bucket}")
        print(f"   🎭 IAM Role: {self.role}")
        print(f"   🌍 Region: {self.region}")
    
    def upload_dataset_to_s3(self, dataset_path="mega_dataset"):
        """Upload your mega dataset to S3"""
        print(f"📤 Uploading dataset to S3...")
        
        # Upload dataset
        dataset_s3_path = f"s3://{self.bucket}/khmer-whisper-dataset"
        
        # Use AWS CLI for faster upload
        import subprocess
        subprocess.run([
            "aws", "s3", "sync", 
            dataset_path, 
            f"{dataset_s3_path}/data",
            "--exclude", "*.pyc",
            "--exclude", "__pycache__/*"
        ], check=True)
        
        print(f"✅ Dataset uploaded to: {dataset_s3_path}")
        return dataset_s3_path
    
    def create_training_job(self, model_size="tiny", dataset_s3_path=None):
        """Create SageMaker training job for Whisper fine-tuning"""
        
        if not dataset_s3_path:
            dataset_s3_path = self.upload_dataset_to_s3()
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        job_name = f"whisper-{model_size}-khmer-{timestamp}"
        
        print(f"🎯 Creating training job: {job_name}")
        
        # Hyperparameters optimized for ml.g4dn.2xlarge (1 GPU, 32GB RAM)
        hyperparameters = {
            # Model configuration
            "model_name_or_path": f"openai/whisper-{model_size}",
            "language": "km",
            "task": "transcribe",
            
            # Training parameters optimized for g4dn.2xlarge
            "per_device_train_batch_size": 16 if model_size == "tiny" else 8,
            "per_device_eval_batch_size": 32 if model_size == "tiny" else 16,
            "gradient_accumulation_steps": 2 if model_size == "tiny" else 4,
            "learning_rate": 1e-5,
            "warmup_steps": 1000,
            "max_steps": 10000 if model_size == "tiny" else 15000,
            "eval_steps": 1000,
            "save_steps": 1000,
            "logging_steps": 100,
            
            # Optimization
            "fp16": True,  # Use mixed precision for faster training
            "dataloader_num_workers": 4,
            "group_by_length": True,
            
            # Regularization
            "weight_decay": 0.01,
            "max_grad_norm": 1.0,
            "dropout_rate": 0.1,
            
            # Data parameters
            "max_duration_in_seconds": 30,
            "min_duration_in_seconds": 1,
            "preprocessing_num_workers": 8,
            
            # Generation config for evaluation
            "predict_with_generate": True,
            "generation_max_length": 225,
            "generation_num_beams": 1,  # Faster for evaluation
        }
        
        # Metric definitions for SageMaker monitoring
        metric_definitions = [
            {"Name": "train:loss", "Regex": "'train_loss': ([0-9\\.]+)"},
            {"Name": "eval:loss", "Regex": "'eval_loss': ([0-9\\.]+)"},
            {"Name": "eval:wer", "Regex": "'eval_wer': ([0-9\\.]+)"},
            {"Name": "learning_rate", "Regex": "'learning_rate': ([0-9\\.e-]+)"},
        ]
        
        # Create PyTorch estimator
        estimator = PyTorch(
            entry_point="whisper_sagemaker_train.py",
            source_dir="./",
            role=self.role,
            instance_type="ml.g4dn.2xlarge",
            instance_count=1,
            framework_version="2.0.0",
            py_version="py310",
            
            # Job configuration
            job_name=job_name,
            max_run=24*3600,  # 24 hours max
            
            hyperparameters=hyperparameters,
            metric_definitions=metric_definitions,
            
            # Environment variables
            environment={
                "TRANSFORMERS_CACHE": "/tmp/transformers_cache",
                "HF_HOME": "/tmp/hf_cache",
                "CUDA_LAUNCH_BLOCKING": "1",
            },
            
            # Checkpointing
            checkpoint_s3_uri=f"s3://{self.bucket}/whisper-checkpoints/{job_name}",
            checkpoint_local_path="/opt/ml/checkpoints",
            
            # Output
            output_path=f"s3://{self.bucket}/whisper-models/{job_name}",
            
            # Debugging
            debugger_hook_config=False,  # Disable for faster training
            disable_profiler=True,
        )
        
        # Training data input
        train_input = TrainingInput(
            s3_data=f"{dataset_s3_path}/data",
            distribution="FullyReplicated"
        )
        
        # Start training
        print(f"🚀 Starting training job: {job_name}")
        print(f"   💾 Dataset: {dataset_s3_path}")
        print(f"   🎯 Model: Whisper {model_size}")
        print(f"   🖥️ Instance: ml.g4dn.2xlarge")
        print(f"   ⏱️ Expected duration: {2-4 if model_size == 'tiny' else 4-8} hours")
        
        estimator.fit({"training": train_input}, wait=False)
        
        return {
            "job_name": job_name,
            "estimator": estimator,
            "model_size": model_size,
            "expected_duration_hours": 2-4 if model_size == "tiny" else 4-8
        }
    
    def train_both_models(self, dataset_s3_path=None):
        """Train both Whisper Tiny and Base models"""
        if not dataset_s3_path:
            dataset_s3_path = self.upload_dataset_to_s3()
        
        print("🎯 Training both Whisper Tiny and Base models")
        
        # Start Tiny model training
        tiny_job = self.create_training_job("tiny", dataset_s3_path)
        print(f"✅ Whisper Tiny job started: {tiny_job['job_name']}")
        
        # Start Base model training
        base_job = self.create_training_job("base", dataset_s3_path)
        print(f"✅ Whisper Base job started: {base_job['job_name']}")
        
        print(f"\n🎪 Training Summary:")
        print(f"   📊 Dataset: 110K+ samples, 138+ hours")
        print(f"   🎯 Models: Whisper Tiny + Base")
        print(f"   💰 Cost estimate: $15-30 total for both models")
        print(f"   ⏱️ Total time: 6-12 hours")
        
        return {"tiny": tiny_job, "base": base_job}
    
    def monitor_jobs(self, jobs):
        """Monitor training job progress"""
        sm_client = boto3.client('sagemaker')
        
        for model_name, job_info in jobs.items():
            job_name = job_info["job_name"]
            
            try:
                response = sm_client.describe_training_job(TrainingJobName=job_name)
                status = response['TrainingJobStatus']
                
                print(f"📊 {model_name.upper()} ({job_name}): {status}")
                
                if status == "InProgress":
                    # Show metrics if available
                    if 'FinalMetricDataList' in response:
                        for metric in response['FinalMetricDataList']:
                            print(f"   📈 {metric['MetricName']}: {metric['Value']}")
                            
            except Exception as e:
                print(f"❌ Error checking {job_name}: {e}")

def main():
    """Main training orchestrator"""
    print("🚀 SageMaker Whisper Fine-tuning for Khmer ASR")
    print("=" * 60)
    
    # Initialize trainer
    trainer = SageMakerWhisperTrainer()
    
    # Train both models
    jobs = trainer.train_both_models()
    
    print(f"\n🎉 Training jobs submitted!")
    print(f"Monitor progress in SageMaker console or run:")
    print(f"python sagemaker_whisper_trainer.py --monitor")
    
    return jobs

if __name__ == "__main__":
    import sys
    
    if "--monitor" in sys.argv:
        # Monitor existing jobs
        trainer = SageMakerWhisperTrainer()
        # Add monitoring logic here
        print("📊 Monitoring mode - implement job status checking")
    else:
        main()