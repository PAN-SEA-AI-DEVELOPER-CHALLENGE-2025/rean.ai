#!/usr/bin/env python3
"""
Dataset Merger for Khmer Speech Recognition
==========================================

Merges your original dataset with the LSR42 Khmer dataset to create
a larger, more diverse training dataset.

Your datasets:
1. Original: 81,340 samples (110+ hours) - broadcast/TTS style
2. LSR42: 2,906 samples - male speaker recordings

Combined: ~84,000+ samples with speaker diversity!
"""

import pandas as pd
import json
import shutil
import librosa
from pathlib import Path
import logging
from typing import Dict, List
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatasetMerger:
    """Merges multiple Khmer speech datasets"""
    
    def __init__(self):
        self.original_dataset_dir = Path("dataset")
        self.lsr42_dataset_dir = Path("lsr42_dataset/km_kh_male")
        self.merged_dataset_dir = Path("merged_dataset")
        
        # Create merged dataset directory
        self.merged_dataset_dir.mkdir(exist_ok=True)
    
    def load_lsr42_data(self) -> List[Dict]:
        """Load and process LSR42 dataset"""
        logger.info("Loading LSR42 dataset...")
        
        # Read transcription file
        tsv_file = self.lsr42_dataset_dir / "line_index.tsv"
        lsr42_data = []
        
        with open(tsv_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    audio_id = parts[0]
                    transcription = parts[1]
                    
                    # Audio file path
                    audio_file = self.lsr42_dataset_dir / "wavs" / f"{audio_id}.wav"
                    
                    if audio_file.exists():
                        # Get audio duration
                        try:
                            duration = librosa.get_duration(filename=str(audio_file))
                        except:
                            duration = 0.0
                        
                        lsr42_data.append({
                            'audio_id': audio_id,
                            'transcription': transcription,
                            'audio_path': str(audio_file),
                            'duration': duration,
                            'speaker': 'lsr42_male',
                            'source': 'lsr42',
                            'language': 'km'
                        })
        
        logger.info(f"Loaded {len(lsr42_data)} samples from LSR42")
        return lsr42_data
    
    def load_original_data(self) -> Dict[str, List[Dict]]:
        """Load original dataset manifests"""
        logger.info("Loading original dataset...")
        
        original_data = {}
        
        for split in ['train', 'validation', 'test']:
            manifest_file = self.original_dataset_dir / split / f"{split}_manifest.jsonl"
            
            if manifest_file.exists():
                split_data = []
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        item = json.loads(line)
                        # Add source identifier
                        item['source'] = 'original'
                        split_data.append(item)
                
                original_data[split] = split_data
                logger.info(f"Loaded {len(split_data)} samples from original {split}")
        
        return original_data
    
    def merge_and_split_data(self, original_data: Dict, lsr42_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Merge datasets and create new splits"""
        logger.info("Merging datasets and creating new splits...")
        
        # Convert LSR42 data to manifest format
        lsr42_manifest = []
        for item in lsr42_data:
            lsr42_manifest.append({
                'audio_filepath': f"audio/{item['audio_id']}.wav",
                'text': item['transcription'],
                'duration': item['duration'],
                'language': 'km',
                'speaker': 'lsr42_male',
                'session_id': f"lsr42_{item['audio_id'][:8]}",
                'source': 'lsr42'
            })
        
        # Combine all data
        all_train = original_data.get('train', []) + lsr42_manifest
        all_val = original_data.get('validation', [])
        all_test = original_data.get('test', [])
        
        # Create new splits ensuring LSR42 data is distributed across splits
        np.random.seed(42)
        np.random.shuffle(lsr42_manifest)
        
        # Split LSR42 data: 80% train, 10% val, 10% test
        lsr42_size = len(lsr42_manifest)
        lsr42_train_size = int(lsr42_size * 0.8)
        lsr42_val_size = int(lsr42_size * 0.1)
        
        lsr42_train = lsr42_manifest[:lsr42_train_size]
        lsr42_val = lsr42_manifest[lsr42_train_size:lsr42_train_size + lsr42_val_size]
        lsr42_test = lsr42_manifest[lsr42_train_size + lsr42_val_size:]
        
        # Create merged splits
        merged_data = {
            'train': original_data.get('train', []) + lsr42_train,
            'validation': original_data.get('validation', []) + lsr42_val,
            'test': original_data.get('test', []) + lsr42_test
        }
        
        # Log statistics
        for split, data in merged_data.items():
            original_count = len([x for x in data if x.get('source') == 'original'])
            lsr42_count = len([x for x in data if x.get('source') == 'lsr42'])
            total_duration = sum(x.get('duration', 0) for x in data) / 3600
            
            logger.info(f"{split.capitalize()}: {len(data)} total samples")
            logger.info(f"  - Original: {original_count}, LSR42: {lsr42_count}")
            logger.info(f"  - Duration: {total_duration:.2f} hours")
        
        return merged_data
    
    def copy_audio_files(self, merged_data: Dict[str, List[Dict]]):
        """Copy audio files to merged dataset structure"""
        logger.info("Copying audio files...")
        
        for split, data in merged_data.items():
            split_audio_dir = self.merged_dataset_dir / split / "audio"
            split_audio_dir.mkdir(parents=True, exist_ok=True)
            
            for item in data:
                if item.get('source') == 'original':
                    # Copy from original dataset
                    source_audio = self.original_dataset_dir / split / item['audio_filepath']
                    target_audio = split_audio_dir / Path(item['audio_filepath']).name
                    
                elif item.get('source') == 'lsr42':
                    # Copy from LSR42 dataset  
                    audio_filename = Path(item['audio_filepath']).name
                    source_audio = self.lsr42_dataset_dir / "wavs" / audio_filename
                    target_audio = split_audio_dir / audio_filename
                
                # Copy file if it doesn't exist
                if source_audio.exists() and not target_audio.exists():
                    shutil.copy2(source_audio, target_audio)
    
    def create_merged_manifests(self, merged_data: Dict[str, List[Dict]]):
        """Create manifest files for merged dataset"""
        logger.info("Creating merged manifest files...")
        
        for split, data in merged_data.items():
            split_dir = self.merged_dataset_dir / split
            split_dir.mkdir(parents=True, exist_ok=True)
            
            # PyTorch/ESPnet format
            with open(split_dir / f"{split}_manifest.jsonl", 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            # Hugging Face format
            hf_data = []
            for item in data:
                hf_item = {
                    'audio': {'path': item['audio_filepath']},
                    'transcription': item['text'],
                    'duration': item['duration'],
                    'language': item['language'],
                    'speaker_id': item['speaker']
                }
                hf_data.append(hf_item)
            
            with open(split_dir / f"{split}_hf.jsonl", 'w', encoding='utf-8') as f:
                for item in hf_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            # CSV format
            df = pd.DataFrame(data)
            df.to_csv(split_dir / f"{split}_manifest.csv", index=False, encoding='utf-8')
    
    def create_merged_dataset_info(self, merged_data: Dict[str, List[Dict]]):
        """Create dataset info for merged dataset"""
        logger.info("Creating merged dataset info...")
        
        # Calculate statistics
        total_samples = sum(len(data) for data in merged_data.values())
        total_duration = sum(
            sum(item.get('duration', 0) for item in data) 
            for data in merged_data.values()
        ) / 3600
        
        # Speaker statistics
        all_speakers = set()
        source_stats = {'original': 0, 'lsr42': 0}
        
        for data in merged_data.values():
            for item in data:
                all_speakers.add(item.get('speaker', 'unknown'))
                source = item.get('source', 'unknown')
                if source in source_stats:
                    source_stats[source] += 1
        
        dataset_info = {
            "dataset_name": "Merged Khmer Speech Recognition Dataset",
            "language": "km",
            "description": "Combined Khmer ASR dataset with original + LSR42 data",
            "audio_format": "wav",
            "sample_rate": 16000,
            "statistics": {
                "total_samples": total_samples,
                "total_duration_hours": total_duration,
                "unique_speakers": len(all_speakers),
                "source_distribution": source_stats,
                "splits": {
                    split: {
                        "samples": len(data),
                        "duration_hours": sum(item.get('duration', 0) for item in data) / 3600
                    }
                    for split, data in merged_data.items()
                }
            }
        }
        
        # Save dataset info
        with open(self.merged_dataset_dir / "dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, indent=2, ensure_ascii=False)
        
        # Create README
        readme_content = f"""# Merged Khmer Speech Recognition Dataset

## Overview
This is a merged dataset combining:
1. **Original Dataset**: {source_stats['original']} samples from broadcast/TTS data
2. **LSR42 Dataset**: {source_stats['lsr42']} samples from male speaker recordings

## Statistics
- **Total Samples**: {total_samples:,}
- **Total Duration**: {total_duration:.2f} hours
- **Unique Speakers**: {len(all_speakers)}
- **Language**: Khmer (km)

## Data Sources
- **Original**: High-quality broadcast/TTS style (consistent quality)
- **LSR42**: Male speaker recordings (adds speaker diversity)

## Split Distribution
{chr(10).join(f"- **{split.capitalize()}**: {info['samples']:,} samples ({info['duration_hours']:.2f} hours)" for split, info in dataset_info['statistics']['splits'].items())}

## Usage
This merged dataset provides:
✅ **Larger training set**: More data for better model performance
✅ **Speaker diversity**: Multiple speakers vs single speaker
✅ **Quality diversity**: Different recording conditions
✅ **Better generalization**: Models trained on this will be more robust

Use the same training scripts as before - they'll automatically work with the merged dataset!

```python
# Use merged dataset for training
python train_asr_model.py --dataset_dir merged_dataset
```
"""
        
        with open(self.merged_dataset_dir / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def merge_datasets(self):
        """Main function to merge all datasets"""
        logger.info("🔄 Starting dataset merger...")
        
        # Load datasets
        lsr42_data = self.load_lsr42_data()
        original_data = self.load_original_data()
        
        # Merge and split
        merged_data = self.merge_and_split_data(original_data, lsr42_data)
        
        # Copy audio files
        self.copy_audio_files(merged_data)
        
        # Create manifests
        self.create_merged_manifests(merged_data)
        
        # Create dataset info
        self.create_merged_dataset_info(merged_data)
        
        logger.info("🎉 Dataset merger complete!")
        logger.info(f"📁 Merged dataset available at: {self.merged_dataset_dir}")
        
        # Print summary
        total_samples = sum(len(data) for data in merged_data.values())
        total_duration = sum(
            sum(item.get('duration', 0) for item in data) 
            for data in merged_data.values()
        ) / 3600
        
        print(f"\n🎯 MERGED DATASET SUMMARY:")
        print(f"   📊 Total Samples: {total_samples:,}")
        print(f"   ⏱️ Total Duration: {total_duration:.2f} hours")
        print(f"   🎤 Speaker Diversity: Original + LSR42 male speaker")
        print(f"   📁 Location: {self.merged_dataset_dir}")
        print(f"\n✅ Ready for training with improved diversity!")

def main():
    merger = DatasetMerger()
    merger.merge_datasets()

if __name__ == "__main__":
    main()
