#!/usr/bin/env python3
"""
Data Loader Utilities for Khmer Speech Dataset
==============================================

Provides PyTorch and TensorFlow data loaders for the processed speech dataset.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SpeechDataLoader:
    """Base class for speech data loading"""
    
    def __init__(self, manifest_path: str, audio_dir: str, sample_rate: int = 16000):
        self.manifest_path = Path(manifest_path)
        self.audio_dir = Path(audio_dir)
        self.sample_rate = sample_rate
        self.data = self._load_manifest()
    
    def _load_manifest(self) -> List[Dict]:
        """Load manifest file"""
        if self.manifest_path.suffix == '.jsonl':
            with open(self.manifest_path, 'r', encoding='utf-8') as f:
                return [json.loads(line) for line in f]
        elif self.manifest_path.suffix == '.csv':
            df = pd.read_csv(self.manifest_path)
            return df.to_dict('records')
        else:
            raise ValueError(f"Unsupported manifest format: {self.manifest_path.suffix}")
    
    def __len__(self) -> int:
        return len(self.data)
    
    def __getitem__(self, idx: int) -> Dict:
        return self.data[idx]

class PyTorchDataLoader(SpeechDataLoader):
    """PyTorch-compatible data loader"""
    
    def __init__(self, manifest_path: str, audio_dir: str, sample_rate: int = 16000):
        super().__init__(manifest_path, audio_dir, sample_rate)
        
        try:
            import torch
            import torchaudio
            self.torch = torch
            self.torchaudio = torchaudio
        except ImportError:
            raise ImportError("PyTorch and torchaudio are required for PyTorchDataLoader")
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio file and return waveform and sample rate"""
        # Remove 'audio/' prefix if present since audio_dir already points to audio folder
        if audio_path.startswith('audio/'):
            audio_path = audio_path[6:]
        full_path = self.audio_dir / audio_path
        waveform, sr = self.torchaudio.load(str(full_path))
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        
        # Resample if necessary
        if sr != self.sample_rate:
            resampler = self.torchaudio.transforms.Resample(sr, self.sample_rate)
            waveform = resampler(waveform)
        
        return waveform.squeeze().numpy(), self.sample_rate
    
    def create_dataset(self):
        """Create PyTorch Dataset"""
        from torch.utils.data import Dataset
        
        class SpeechDataset(Dataset):
            def __init__(self, loader):
                self.loader = loader
            
            def __len__(self):
                return len(self.loader)
            
            def __getitem__(self, idx):
                item = self.loader[idx]
                audio, sr = self.loader.load_audio(item['audio_filepath'])
                
                return {
                    'audio': audio,
                    'text': item['text'],
                    'duration': item['duration'],
                    'sample_rate': sr,
                    'speaker': item.get('speaker', 'unknown'),
                    'language': item.get('language', 'km')
                }
        
        return SpeechDataset(self)

class HuggingFaceDataLoader(SpeechDataLoader):
    """Hugging Face Datasets-compatible loader"""
    
    def __init__(self, manifest_path: str, audio_dir: str, sample_rate: int = 16000):
        super().__init__(manifest_path, audio_dir, sample_rate)
        
        try:
            from datasets import Dataset, Audio
            self.Dataset = Dataset
            self.Audio = Audio
        except ImportError:
            raise ImportError("datasets library is required for HuggingFaceDataLoader")
    
    def create_dataset(self):
        """Create Hugging Face Dataset"""
        # Prepare data with full audio paths
        data = []
        for item in self.data:
            if 'audio' in item and 'path' in item['audio']:
                # Remove 'audio/' prefix if present since audio_dir already points to audio folder
                audio_path = item['audio']['path']
                if audio_path.startswith('audio/'):
                    audio_path = audio_path[6:]
                audio_path = self.audio_dir / audio_path
                data.append({
                    'audio': str(audio_path),
                    'transcription': item['transcription'],
                    'duration': item['duration'],
                    'language': item.get('language', 'km'),
                    'speaker_id': item.get('speaker_id', 'unknown')
                })
        
        # Create dataset and cast audio column
        dataset = self.Dataset.from_list(data)
        dataset = dataset.cast_column('audio', self.Audio(sampling_rate=self.sample_rate))
        
        return dataset

class TensorFlowDataLoader(SpeechDataLoader):
    """TensorFlow-compatible data loader"""
    
    def __init__(self, manifest_path: str, audio_dir: str, sample_rate: int = 16000):
        super().__init__(manifest_path, audio_dir, sample_rate)
        
        try:
            import tensorflow as tf
            self.tf = tf
        except ImportError:
            raise ImportError("TensorFlow is required for TensorFlowDataLoader")
    
    def load_audio(self, audio_path: str) -> Tuple[np.ndarray, int]:
        """Load audio using TensorFlow"""
        # Remove 'audio/' prefix if present since audio_dir already points to audio folder  
        if audio_path.startswith('audio/'):
            audio_path = audio_path[6:]
        full_path = str(self.audio_dir / audio_path)
        audio_binary = self.tf.io.read_file(full_path)
        waveform, sr = self.tf.audio.decode_wav(audio_binary)
        
        # Convert to desired sample rate if needed
        if sr != self.sample_rate:
            waveform = self.tf.signal.resample(waveform, int(len(waveform) * self.sample_rate / sr))
        
        return waveform.numpy().flatten(), self.sample_rate
    
    def create_dataset(self):
        """Create TensorFlow Dataset"""
        def generator():
            for item in self.data:
                audio, sr = self.load_audio(item['wav_filename'])
                yield {
                    'audio': audio,
                    'text': item['transcript'],
                    'sample_rate': sr
                }
        
        output_signature = {
            'audio': self.tf.TensorSpec(shape=(None,), dtype=self.tf.float32),
            'text': self.tf.TensorSpec(shape=(), dtype=self.tf.string),
            'sample_rate': self.tf.TensorSpec(shape=(), dtype=self.tf.int32)
        }
        
        return self.tf.data.Dataset.from_generator(
            generator,
            output_signature=output_signature
        )

# Example usage functions
def load_pytorch_dataset(dataset_dir: str, split: str = "train"):
    """Load PyTorch dataset"""
    manifest_path = f"{dataset_dir}/{split}/{split}_manifest.jsonl"
    audio_dir = f"{dataset_dir}/{split}/audio"
    
    loader = PyTorchDataLoader(manifest_path, audio_dir)
    return loader.create_dataset()

def load_huggingface_dataset(dataset_dir: str, split: str = "train"):
    """Load Hugging Face dataset"""
    manifest_path = f"{dataset_dir}/{split}/{split}_hf.jsonl"
    audio_dir = f"{dataset_dir}/{split}/audio"
    
    loader = HuggingFaceDataLoader(manifest_path, audio_dir)
    return loader.create_dataset()

def load_tensorflow_dataset(dataset_dir: str, split: str = "train"):
    """Load TensorFlow dataset"""
    manifest_path = f"{dataset_dir}/{split}/{split}_tf.jsonl"  
    audio_dir = f"{dataset_dir}/{split}/audio"
    
    loader = TensorFlowDataLoader(manifest_path, audio_dir)
    return loader.create_dataset()

if __name__ == "__main__":
    # Example usage
    dataset_dir = "/Users/thun/Desktop/speech_dataset/dataset"
    
    print("Loading PyTorch dataset...")
    try:
        pytorch_dataset = load_pytorch_dataset(dataset_dir, "train")
        print(f"PyTorch dataset size: {len(pytorch_dataset)}")
        
        # Test loading one sample
        sample = pytorch_dataset[0]
        print(f"Sample audio shape: {sample['audio'].shape}")
        print(f"Sample text: {sample['text']}")
        
    except ImportError as e:
        print(f"PyTorch not available: {e}")
    
    print("\nLoading Hugging Face dataset...")
    try:
        hf_dataset = load_huggingface_dataset(dataset_dir, "train")
        print(f"HF dataset size: {len(hf_dataset)}")
        
    except ImportError as e:
        print(f"Hugging Face datasets not available: {e}")
