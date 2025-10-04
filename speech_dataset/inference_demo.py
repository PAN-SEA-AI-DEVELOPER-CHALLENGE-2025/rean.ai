#!/usr/bin/env python3
"""
Khmer ASR Inference Demo
=======================

Demo script to test your trained Khmer ASR model on new audio files.
"""

import torch
import librosa
import soundfile as sf
from pathlib import Path
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC

class KhmerASRInference:
    """Inference class for Khmer ASR model"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.processor = None
        self.model = None
        self.load_model()
    
    def load_model(self):
        """Load the trained model and processor"""
        print(f"Loading model from {self.model_path}...")
        
        # Load processor and model
        self.processor = Wav2Vec2Processor.from_pretrained(self.model_path)
        self.model = Wav2Vec2ForCTC.from_pretrained(self.model_path)
        
        # Set to evaluation mode
        self.model.eval()
        
        print("Model loaded successfully!")
    
    def transcribe_audio(self, audio_path: str, sampling_rate: int = 16000) -> str:
        """Transcribe audio file to text"""
        # Load audio
        speech, sr = librosa.load(audio_path, sr=sampling_rate)
        
        # Process audio
        inputs = self.processor(
            speech, 
            sampling_rate=sampling_rate, 
            return_tensors="pt", 
            padding=True
        )
        
        # Get predictions
        with torch.no_grad():
            logits = self.model(inputs.input_values).logits
        
        # Decode predictions
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        
        return transcription
    
    def transcribe_from_dataset(self, dataset_dir: str, split: str = "test", num_samples: int = 5):
        """Transcribe samples from your dataset for testing"""
        import json
        
        manifest_path = Path(dataset_dir) / split / f"{split}_manifest.jsonl"
        
        if not manifest_path.exists():
            print(f"Manifest not found: {manifest_path}")
            return
        
        print(f"\nTesting on {num_samples} samples from {split} set:")
        print("=" * 60)
        
        count = 0
        with open(manifest_path, 'r', encoding='utf-8') as f:
            for line in f:
                if count >= num_samples:
                    break
                
                item = json.loads(line)
                audio_path = Path(dataset_dir) / split / item['audio_filepath']
                
                if audio_path.exists():
                    # Get prediction
                    predicted_text = self.transcribe_audio(str(audio_path))
                    actual_text = item['text']
                    
                    print(f"\nSample {count + 1}:")
                    print(f"Audio: {audio_path.name}")
                    print(f"Actual:    {actual_text}")
                    print(f"Predicted: {predicted_text}")
                    print("-" * 60)
                    
                    count += 1

def demo_inference():
    """Demo function showing how to use the inference class"""
    model_path = "./khmer-wav2vec2"  # Path to your trained model
    dataset_dir = "./dataset"         # Path to your dataset
    
    # Check if model exists
    if not Path(model_path).exists():
        print(f"❌ Model not found at {model_path}")
        print("Please train the model first using: python train_asr_model.py")
        return
    
    try:
        # Initialize inference
        asr = KhmerASRInference(model_path)
        
        # Test on dataset samples
        asr.transcribe_from_dataset(dataset_dir, "test", num_samples=5)
        
        # Test on custom audio file (if you have one)
        custom_audio = "your_audio_file.wav"  # Replace with your audio file
        if Path(custom_audio).exists():
            print(f"\n🎤 Testing custom audio: {custom_audio}")
            transcription = asr.transcribe_audio(custom_audio)
            print(f"Transcription: {transcription}")
        
    except Exception as e:
        print(f"❌ Error during inference: {e}")

if __name__ == "__main__":
    demo_inference()
