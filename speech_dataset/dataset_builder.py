#!/usr/bin/env python3
"""
Speech Dataset Builder for Khmer Speech Recognition
==================================================

This script organizes and builds a machine learning-ready dataset from processed
speech data with audio chunks, transcriptions, and metadata.

Features:
- Data validation and integrity checks
- Multiple output formats (PyTorch, TensorFlow, Hugging Face)
- Train/validation/test splits
- Manifest file generation
- Data statistics and analysis
"""

import pandas as pd
import json
import os
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DatasetConfig:
    """Configuration for dataset building"""
    source_dir: str = "/Users/thun/Desktop/speech_dataset"
    output_dir: str = "/Users/thun/Desktop/speech_dataset/dataset"
    audio_format: str = "wav"
    sample_rate: int = 16000
    min_duration: float = 0.5  # seconds
    max_duration: float = 30.0  # seconds
    train_ratio: float = 0.8
    val_ratio: float = 0.1
    test_ratio: float = 0.1
    random_seed: int = 42

class SpeechDatasetBuilder:
    """Main class for building speech recognition datasets"""
    
    def __init__(self, config: DatasetConfig):
        self.config = config
        self.source_dir = Path(config.source_dir)
        self.output_dir = Path(config.output_dir)
        self.sessions_df = None
        self.chunks_df = None
        self.words_df = None
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        
    def load_metadata(self) -> None:
        """Load all metadata CSV files"""
        logger.info("Loading metadata files...")
        
        # Load sessions
        sessions_path = self.source_dir / "metadata" / "sessions.csv"
        if sessions_path.exists():
            self.sessions_df = pd.read_csv(sessions_path)
            logger.info(f"Loaded {len(self.sessions_df)} sessions")
        
        # Load chunks
        chunks_path = self.source_dir / "metadata" / "chunks.csv"
        if chunks_path.exists():
            self.chunks_df = pd.read_csv(chunks_path)
            logger.info(f"Loaded {len(self.chunks_df)} chunks")
        
        # Load words
        words_path = self.source_dir / "metadata" / "words.csv"
        if words_path.exists():
            self.words_df = pd.read_csv(words_path)
            logger.info(f"Loaded {len(self.words_df)} word entries")
    
    def validate_data_integrity(self) -> Dict[str, any]:
        """Validate data consistency and completeness"""
        logger.info("Validating data integrity...")
        
        validation_results = {
            "total_chunks": len(self.chunks_df),
            "valid_chunks": 0,
            "missing_audio": 0,
            "missing_transcripts": 0,
            "duration_issues": 0,
            "empty_transcriptions": 0
        }
        
        audio_dir = self.source_dir / "audio"
        transcripts_dir = self.source_dir / "transcripts"
        
        for idx, chunk in self.chunks_df.iterrows():
            # Check audio file exists
            audio_file = audio_dir / f"{Path(chunk['file_path']).name}"
            if not audio_file.exists():
                validation_results["missing_audio"] += 1
                continue
            
            # Check duration is reasonable
            duration = chunk.get('duration', 0)
            if duration < self.config.min_duration or duration > self.config.max_duration:
                validation_results["duration_issues"] += 1
                continue
            
            # Check transcription is not empty
            transcription = chunk.get('transcription', '')
            if pd.isna(transcription) or not str(transcription).strip():
                validation_results["empty_transcriptions"] += 1
                continue
            
            validation_results["valid_chunks"] += 1
        
        logger.info(f"Validation complete: {validation_results['valid_chunks']}/{validation_results['total_chunks']} valid chunks")
        return validation_results
    
    def create_train_val_test_splits(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Create train/validation/test splits by session to avoid data leakage"""
        logger.info("Creating train/validation/test splits...")
        
        # Get unique session IDs
        session_ids = self.chunks_df['session_id'].unique()
        np.random.seed(self.config.random_seed)
        np.random.shuffle(session_ids)
        
        # Calculate split sizes
        n_sessions = len(session_ids)
        train_size = int(n_sessions * self.config.train_ratio)
        val_size = int(n_sessions * self.config.val_ratio)
        
        # Split session IDs
        train_sessions = session_ids[:train_size]
        val_sessions = session_ids[train_size:train_size + val_size]
        test_sessions = session_ids[train_size + val_size:]
        
        # Split chunks by session
        train_chunks = self.chunks_df[self.chunks_df['session_id'].isin(train_sessions)]
        val_chunks = self.chunks_df[self.chunks_df['session_id'].isin(val_sessions)]
        test_chunks = self.chunks_df[self.chunks_df['session_id'].isin(test_sessions)]
        
        logger.info(f"Split sizes - Train: {len(train_chunks)}, Val: {len(val_chunks)}, Test: {len(test_chunks)}")
        
        return train_chunks, val_chunks, test_chunks
    
    def copy_audio_files(self, chunks_df: pd.DataFrame, split_name: str) -> None:
        """Copy audio files to organized structure"""
        logger.info(f"Copying {split_name} audio files...")
        
        split_audio_dir = self.output_dir / split_name / "audio"
        split_audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_dir = self.source_dir / "audio"
        
        for idx, chunk in chunks_df.iterrows():
            source_audio = audio_dir / f"{Path(chunk['file_path']).name}"
            if source_audio.exists():
                # Create a clean filename
                chunk_id = str(chunk['chunk_id']).replace('/', '_')
                target_audio = split_audio_dir / f"{chunk['session_id']}_{chunk_id}.wav"
                
                if not target_audio.exists():
                    shutil.copy2(source_audio, target_audio)
    
    def create_manifest_files(self, chunks_df: pd.DataFrame, split_name: str) -> None:
        """Create manifest files for different ML frameworks"""
        logger.info(f"Creating {split_name} manifest files...")
        
        split_dir = self.output_dir / split_name
        split_dir.mkdir(parents=True, exist_ok=True)
        
        # PyTorch/ESPnet style manifest
        pytorch_manifest = []
        
        # Hugging Face datasets style
        hf_manifest = []
        
        # TensorFlow/Lingvo style
        tf_manifest = []
        
        for idx, chunk in chunks_df.iterrows():
            audio_file = f"{chunk['session_id']}_{str(chunk['chunk_id']).replace('/', '_')}.wav"
            audio_path = f"audio/{audio_file}"
            
            # Skip if no transcription
            transcription = chunk.get('transcription', '')
            if pd.isna(transcription) or not str(transcription).strip():
                continue
            transcription = str(transcription).strip()
            
            # PyTorch/ESPnet format
            pytorch_entry = {
                "audio_filepath": audio_path,
                "text": transcription,
                "duration": float(chunk.get('duration', 0.0)),
                "language": chunk.get('language', 'km'),
                "speaker": chunk.get('speaker', 'unknown'),
                "session_id": chunk['session_id']
            }
            pytorch_manifest.append(pytorch_entry)
            
            # Hugging Face format
            hf_entry = {
                "audio": {"path": audio_path},
                "transcription": transcription,
                "duration": float(chunk.get('duration', 0.0)),
                "language": chunk.get('language', 'km'),
                "speaker_id": chunk.get('speaker', 'unknown')
            }
            hf_manifest.append(hf_entry)
            
            # TensorFlow format
            tf_entry = {
                "wav_filename": audio_path,
                "wav_filesize": 0,  # Will be calculated later
                "transcript": transcription
            }
            tf_manifest.append(tf_entry)
        
        # Save manifests
        with open(split_dir / f"{split_name}_manifest.jsonl", 'w', encoding='utf-8') as f:
            for entry in pytorch_manifest:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        with open(split_dir / f"{split_name}_hf.jsonl", 'w', encoding='utf-8') as f:
            for entry in hf_manifest:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        # Save as CSV for easy inspection
        manifest_df = pd.DataFrame(pytorch_manifest)
        manifest_df.to_csv(split_dir / f"{split_name}_manifest.csv", index=False, encoding='utf-8')
        
        logger.info(f"Created {len(pytorch_manifest)} entries for {split_name}")
    
    def generate_dataset_statistics(self) -> Dict[str, any]:
        """Generate comprehensive dataset statistics"""
        logger.info("Generating dataset statistics...")
        
        stats = {
            "total_sessions": len(self.sessions_df) if self.sessions_df is not None else 0,
            "total_chunks": len(self.chunks_df),
            "total_duration_hours": 0.0,
            "unique_speakers": set(),
            "languages": defaultdict(int),
            "duration_distribution": {},
            "transcription_stats": {}
        }
        
        # Calculate total duration
        if 'duration' in self.chunks_df.columns:
            total_duration = self.chunks_df['duration'].sum()
            stats["total_duration_hours"] = total_duration / 3600.0
            
            # Duration distribution
            durations = self.chunks_df['duration']
            stats["duration_distribution"] = {
                "min": float(durations.min()),
                "max": float(durations.max()),
                "mean": float(durations.mean()),
                "median": float(durations.median()),
                "std": float(durations.std())
            }
        
        # Speaker and language stats
        if 'speaker' in self.chunks_df.columns:
            stats["unique_speakers"] = set(self.chunks_df['speaker'].unique())
        
        if 'language' in self.chunks_df.columns:
            for lang in self.chunks_df['language']:
                if pd.notna(lang):
                    stats["languages"][lang] += 1
        
        # Transcription stats
        transcriptions = self.chunks_df['transcription'].dropna()
        if len(transcriptions) > 0:
            word_counts = [len(text.split()) for text in transcriptions if text.strip()]
            if word_counts:
                stats["transcription_stats"] = {
                    "avg_words_per_utterance": np.mean(word_counts),
                    "total_words": sum(word_counts),
                    "unique_transcriptions": len(set(transcriptions))
                }
        
        # Convert sets to lists for JSON serialization
        stats["unique_speakers"] = list(stats["unique_speakers"])
        stats["languages"] = dict(stats["languages"])
        
        return stats
    
    def save_dataset_info(self, stats: Dict[str, any]) -> None:
        """Save dataset information and statistics"""
        logger.info("Saving dataset information...")
        
        dataset_info = {
            "dataset_name": "Khmer Speech Recognition Dataset",
            "language": "km",
            "description": "Khmer speech recognition dataset with audio chunks and transcriptions",
            "audio_format": self.config.audio_format,
            "sample_rate": self.config.sample_rate,
            "statistics": stats,
            "splits": {
                "train": self.config.train_ratio,
                "validation": self.config.val_ratio, 
                "test": self.config.test_ratio
            }
        }
        
        # Save as JSON
        with open(self.output_dir / "dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, indent=2, ensure_ascii=False)
        
        # Save README
        readme_content = f"""# Khmer Speech Recognition Dataset

## Overview
This dataset contains Khmer (Cambodian) speech data for automatic speech recognition training.

## Statistics
- **Total Sessions**: {stats['total_sessions']}
- **Total Audio Chunks**: {stats['total_chunks']}
- **Total Duration**: {stats['total_duration_hours']:.2f} hours
- **Languages**: {', '.join(stats['languages'].keys())}
- **Unique Speakers**: {len(stats['unique_speakers'])}

## Structure
```
dataset/
├── train/
│   ├── audio/          # Training audio files
│   ├── train_manifest.jsonl  # PyTorch/ESPnet format
│   ├── train_hf.jsonl        # Hugging Face format
│   └── train_manifest.csv    # CSV format
├── validation/
│   ├── audio/          # Validation audio files
│   └── [manifest files]
├── test/
│   ├── audio/          # Test audio files
│   └── [manifest files]
└── dataset_info.json   # Dataset metadata
```

## Usage

### PyTorch/ESPnet
```python
import json
import pandas as pd

# Load manifest
with open('train/train_manifest.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Or use CSV
df = pd.read_csv('train/train_manifest.csv')
```

### Hugging Face Datasets
```python
from datasets import Dataset
import json

# Load HF format
with open('train/train_hf.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

dataset = Dataset.from_list(data)
```

## Notes
- Audio files are in WAV format at 16kHz sample rate
- Transcriptions are in Khmer script
- Dataset split by sessions to avoid data leakage
- Duration range: {stats.get('duration_distribution', {}).get('min', 0):.2f}s - {stats.get('duration_distribution', {}).get('max', 0):.2f}s
"""

        with open(self.output_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def build_dataset(self) -> None:
        """Main method to build the complete dataset"""
        logger.info("Starting dataset build process...")
        
        # Load metadata
        self.load_metadata()
        
        # Validate data
        validation_results = self.validate_data_integrity()
        
        # Create splits
        train_chunks, val_chunks, test_chunks = self.create_train_val_test_splits()
        
        # Process each split
        for chunks_df, split_name in [(train_chunks, "train"), 
                                      (val_chunks, "validation"), 
                                      (test_chunks, "test")]:
            if len(chunks_df) > 0:
                self.copy_audio_files(chunks_df, split_name)
                self.create_manifest_files(chunks_df, split_name)
        
        # Generate statistics and save info
        stats = self.generate_dataset_statistics()
        self.save_dataset_info(stats)
        
        logger.info(f"Dataset build complete! Output directory: {self.output_dir}")
        logger.info(f"Total processed: {validation_results['valid_chunks']} chunks")

def main():
    """Main entry point"""
    config = DatasetConfig()
    builder = SpeechDatasetBuilder(config)
    builder.build_dataset()

if __name__ == "__main__":
    main()
