# 🎯 Khmer ASR Training Guide

## Quick Start (5 Minutes to Training!)

### 1. Install Dependencies
```bash
# Install training requirements
pip install -r training_requirements.txt

# Or install core packages only
pip install torch torchaudio transformers datasets librosa soundfile
```

### 2. Start Training Immediately
```bash
# Run the training script
python train_asr_model.py
```

That's it! Your model will start training on your 110+ hours of Khmer speech data.

---

## 📋 Detailed Training Setup

### **System Requirements**
- **GPU**: Recommended (CUDA-compatible)
- **RAM**: 16GB+ recommended  
- **Storage**: 10GB+ free space for model checkpoints
- **Python**: 3.8+

### **Training Configuration**
The training script uses sensible defaults:
- **Model**: Wav2Vec2-base (pre-trained)
- **Batch Size**: 8 per device
- **Learning Rate**: 1e-4
- **Epochs**: 10
- **Early Stopping**: 3 patience

### **Training Output**
```
./khmer-wav2vec2/
├── config.json              # Model configuration
├── pytorch_model.bin         # Trained model weights
├── preprocessor_config.json  # Audio preprocessing config  
├── tokenizer_config.json     # Tokenizer configuration
├── vocab.json               # Khmer vocabulary
└── training_args.bin        # Training arguments
```

---

## 🚀 Advanced Training Options

### **1. Custom Configuration**
Edit the `ModelConfig` class in `train_asr_model.py`:

```python
@dataclass
class ModelConfig:
    # Change model size
    model_name: str = "facebook/wav2vec2-large"  # Larger model
    
    # Training parameters
    num_train_epochs: int = 20                   # More epochs
    per_device_train_batch_size: int = 4         # Smaller batch if GPU memory limited
    learning_rate: float = 5e-5                  # Lower learning rate
```

### **2. Different Base Models**
```python
# Options for model_name:
"facebook/wav2vec2-base"           # 95M parameters - fast training
"facebook/wav2vec2-large"          # 317M parameters - better quality  
"facebook/wav2vec2-large-960h"     # Pre-trained on English
"microsoft/wavlm-base-plus"        # WavLM model (alternative)
```

### **3. Data Augmentation** (Recommended!)
Add to the preprocessing function:
```python
import torchaudio.transforms as T

# Add noise and speed perturbation
def augment_audio(audio_array, sample_rate=16000):
    # Speed perturbation
    if random.random() < 0.5:
        speed_factor = random.uniform(0.9, 1.1)
        audio_array = librosa.effects.time_stretch(audio_array, rate=speed_factor)
    
    # Add noise
    if random.random() < 0.3:
        noise = np.random.normal(0, 0.005, audio_array.shape)
        audio_array = audio_array + noise
    
    return audio_array
```

---

## 📊 Training Monitoring

### **1. Check Training Progress**
```bash
# Monitor loss and metrics
tail -f ./khmer-wav2vec2/trainer_log.txt

# Or use tensorboard (if installed)
tensorboard --logdir ./khmer-wav2vec2/runs
```

### **2. Expected Training Time**
- **With GPU**: 4-8 hours for 10 epochs
- **CPU Only**: 20-40 hours (not recommended)

### **3. Expected Performance**
With your 110+ hours of data:
- **Baseline CER**: 15-25% (Character Error Rate)
- **Good Performance**: 8-15% CER
- **Excellent**: <8% CER (with data augmentation)

---

## 🧪 Testing Your Model

### **1. Quick Test**
```bash
# Test on dataset samples
python inference_demo.py
```

### **2. Test on Custom Audio**
```python
from inference_demo import KhmerASRInference

asr = KhmerASRInference("./khmer-wav2vec2")
transcription = asr.transcribe_audio("your_audio.wav")
print(transcription)
```

---

## 🔧 Troubleshooting

### **Common Issues & Solutions**

#### **1. Out of Memory Error**
```python
# Reduce batch size
per_device_train_batch_size: int = 4  # or 2

# Enable gradient checkpointing (already enabled)
gradient_checkpointing=True

# Use FP16 training (already enabled)
fp16=True
```

#### **2. Slow Training**
```bash
# Check GPU usage
nvidia-smi

# Use smaller model for testing
model_name = "facebook/wav2vec2-base"  # instead of large
```

#### **3. Poor Performance**
1. **Increase training epochs**: `num_train_epochs = 20`
2. **Add data augmentation** (see above)
3. **Lower learning rate**: `learning_rate = 1e-5`
4. **Use larger model**: `wav2vec2-large`

#### **4. Vocabulary Issues**
The script automatically creates a character-level vocabulary from your transcriptions. If you see weird characters:
1. Check your transcription quality
2. Clean special characters if needed

---

## 🎯 Production Deployment

### **1. Model Optimization**
```python
# Convert to ONNX for faster inference
from transformers.onnx import export
export(model, "khmer_asr.onnx")

# Or use torch.jit for optimization
traced_model = torch.jit.trace(model, example_input)
```

### **2. Hugging Face Hub Upload**
```python
# Upload to Hugging Face for easy sharing
from transformers import Wav2Vec2ForCTC

model = Wav2Vec2ForCTC.from_pretrained("./khmer-wav2vec2")
model.push_to_hub("your-username/khmer-wav2vec2")
```

---

## 📈 Next Steps & Improvements

### **1. Immediate Improvements**
- [ ] Add data augmentation
- [ ] Try different learning rates
- [ ] Experiment with model sizes
- [ ] Add language model for better accuracy

### **2. Advanced Techniques**
- [ ] Multi-task learning (if you have other Khmer NLP tasks)
- [ ] Transfer learning from multilingual models
- [ ] Pseudo-labeling with unlabeled Khmer audio
- [ ] Ensemble models

### **3. Production Features**
- [ ] Real-time streaming ASR
- [ ] Voice activity detection
- [ ] Speaker diarization
- [ ] Punctuation restoration

---

## 🆘 Getting Help

### **Check Training Progress**
```python
# Monitor CER (Character Error Rate) - lower is better
# Typical progression:
# Epoch 1: CER ~0.8-1.0 (80-100%)
# Epoch 5: CER ~0.3-0.5 (30-50%)  
# Epoch 10: CER ~0.1-0.3 (10-30%)
```

### **Common Commands**
```bash
# Resume training from checkpoint
python train_asr_model.py --resume_from_checkpoint ./khmer-wav2vec2/checkpoint-1000

# Quick test
python inference_demo.py

# Check dataset
python example_usage.py
```

---

## 🎉 Success Metrics

Your training is successful if:
- ✅ CER drops below 0.3 (30%) on validation set
- ✅ Model generates readable Khmer text
- ✅ Performance is consistent across test samples
- ✅ No overfitting (train/val CER gap < 0.1)

**Your dataset is excellent for ASR training - 110+ hours is more than enough for production-quality models!**

---

*Happy Training! 🚀*

**Next**: Run `python train_asr_model.py` and watch your Khmer ASR model come to life!
