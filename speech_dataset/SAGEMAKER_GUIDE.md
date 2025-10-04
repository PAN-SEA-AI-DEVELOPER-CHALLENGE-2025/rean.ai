# SageMaker Whisper Fine-tuning Guide
# ==================================

## 🎯 Overview

This guide helps you fine-tune Whisper Tiny and Base models on your 138+ hour Khmer dataset using AWS SageMaker with `ml.g4dn.2xlarge` instances.

## 📊 Dataset Summary

- **Total Samples**: 110,555
- **Total Duration**: 138.56 hours  
- **Languages**: Khmer (km)
- **Sources**: Original (81K), LSR42 (2.9K), Rinabuoy (26K)
- **Splits**: Train (90K), Validation (10K), Test (10K)

## 🚀 Quick Start

### 1. Prerequisites

```bash
# Install requirements
pip install -r sagemaker_requirements.txt

# Configure AWS credentials
aws configure
```

### 2. Start Training

```python
from sagemaker_whisper_trainer import SageMakerWhisperTrainer

# Initialize trainer
trainer = SageMakerWhisperTrainer(region='us-east-1')

# Train both models
jobs = trainer.train_both_models()
```

### 3. Monitor Progress

```python
# Check job status
trainer.monitor_jobs(jobs)
```

## ⚙️ Configuration Details

### Instance Configuration
- **Type**: `ml.g4dn.2xlarge`
- **GPU**: 1x NVIDIA T4 (16GB)
- **vCPUs**: 8
- **RAM**: 32GB
- **Cost**: ~$1.20/hour

### Model Configurations

#### Whisper Tiny
- **Parameters**: 39M
- **Batch Size**: 16 (train), 32 (eval)
- **Training Time**: 2-4 hours
- **Cost Estimate**: $5-10

#### Whisper Base  
- **Parameters**: 74M
- **Batch Size**: 8 (train), 16 (eval)
- **Training Time**: 4-8 hours
- **Cost Estimate**: $10-20

### Hyperparameters

```python
{
    # Optimization
    "learning_rate": 1e-5,
    "weight_decay": 0.01,
    "warmup_steps": 1000,
    "max_grad_norm": 1.0,
    
    # Training schedule
    "max_steps": 10000,  # Tiny: 10K, Base: 15K
    "eval_steps": 1000,
    "save_steps": 1000,
    
    # Data filtering
    "max_duration_in_seconds": 30,
    "min_duration_in_seconds": 1,
    
    # Performance
    "fp16": True,
    "gradient_accumulation_steps": 2,  # Tiny: 2, Base: 4
}
```

## 📁 File Structure

```
speech_dataset/
├── sagemaker_whisper_trainer.py   # Main trainer class
├── whisper_sagemaker_train.py     # SageMaker training script
├── sagemaker_requirements.txt     # Python dependencies
├── mega_dataset/                  # Your prepared dataset
│   ├── train_manifest.json
│   ├── validation_manifest.json 
│   ├── test_manifest.json
│   └── audio/                     # Audio files
└── SAGEMAKER_GUIDE.md            # This guide
```

## 🎪 Training Workflow

### Phase 1: Dataset Upload
1. **Upload to S3**: Automatically sync your `mega_dataset/` to S3
2. **Validation**: Verify all manifest files and audio paths
3. **Duration**: ~30 minutes for 138GB dataset

### Phase 2: Training Job Submission
1. **Job Creation**: Submit Whisper Tiny and Base jobs
2. **Resource Allocation**: Provision `ml.g4dn.2xlarge` instances
3. **Container Setup**: Load PyTorch 2.0 + Transformers environment

### Phase 3: Model Fine-tuning
1. **Data Loading**: Stream audio from S3 with preprocessing
2. **Training Loop**: Fine-tune with gradient accumulation + mixed precision
3. **Evaluation**: Track WER on validation set every 1000 steps
4. **Checkpointing**: Save model every 1000 steps to S3

### Phase 4: Model Deployment (Optional)
1. **Model Registry**: Register best models to SageMaker Model Registry
2. **Endpoint Creation**: Deploy for real-time inference
3. **Batch Transform**: Process large audio batches

## 📊 Expected Results

### Whisper Tiny
- **Baseline WER**: ~15-20% (English)
- **Expected Khmer WER**: ~25-35% (after fine-tuning)
- **Inference Speed**: ~2x real-time on CPU

### Whisper Base
- **Baseline WER**: ~10-15% (English)  
- **Expected Khmer WER**: ~20-30% (after fine-tuning)
- **Inference Speed**: ~1x real-time on CPU

## 💰 Cost Breakdown

### Training Costs (ml.g4dn.2xlarge @ $1.20/hour)
- **Whisper Tiny**: 2-4 hours = $2.40-4.80
- **Whisper Base**: 4-8 hours = $4.80-9.60
- **Data Transfer**: ~$1-2 for 138GB upload
- **Storage**: ~$3-5/month for S3 storage
- **Total**: $8-20 for both models

### Ongoing Costs
- **Model Storage**: $0.023/GB/month in S3
- **Inference Endpoint**: $0.20-2.00/hour depending on instance
- **Batch Transform**: $0.10-0.50/hour for large batches

## 🔧 Troubleshooting

### Common Issues

#### Out of Memory
```python
# Reduce batch size
"per_device_train_batch_size": 4,  # Instead of 8/16
"gradient_accumulation_steps": 8,  # Increase to maintain effective batch size
```

#### Slow Training
```python
# Optimize data loading
"dataloader_num_workers": 8,  # Max for g4dn.2xlarge
"preprocessing_num_workers": 8,
"group_by_length": True,
```

#### High WER
```python
# Adjust learning rate
"learning_rate": 5e-6,  # Lower learning rate
"warmup_steps": 2000,   # Longer warmup
```

### Monitoring Commands

```bash
# Check training progress
aws sagemaker describe-training-job --training-job-name whisper-tiny-khmer-20241201-120000

# Download logs
aws logs get-log-events --log-group-name /aws/sagemaker/TrainingJobs --log-stream-name whisper-tiny-khmer-20241201-120000

# Monitor costs
aws ce get-cost-and-usage --time-period Start=2024-12-01,End=2024-12-02 --granularity DAILY
```

## 🎯 Next Steps

1. **Start Training**: Run the trainer script to begin fine-tuning
2. **Monitor Progress**: Watch training metrics and costs in SageMaker console  
3. **Evaluate Models**: Compare Tiny vs Base performance on your test set
4. **Deploy Best Model**: Create inference endpoint for production use
5. **Iterate**: Fine-tune hyperparameters based on results

## 📞 Support

- **SageMaker Documentation**: https://docs.aws.amazon.com/sagemaker/
- **Whisper Documentation**: https://huggingface.co/docs/transformers/model_doc/whisper
- **Cost Calculator**: https://calculator.aws/#/

---
**Ready to fine-tune Whisper on your 138-hour Khmer dataset! 🎉**