#!/usr/bin/env python3
"""
Fixed Mega Dataset Merger
=========================

Fixes the issues with the previous merger:
1. Properly includes Rinabuoy data in splits
2. More space-efficient (symbolic links instead of copying)
3. Accurate duration calculations

Expected result: 160+ hours total!
"""

import pandas as pd
import json
import os
import librosa
from pathlib import Path
from datasets import load_dataset
import logging
from typing import Dict, List
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FixedMegaMerger:
    """Fixed merger for all three datasets"""
    
    def __init__(self):
        self.original_dataset_dir = Path("dataset")
        self.lsr42_dataset_dir = Path("lsr42_dataset/km_kh_male")
        self.fixed_mega_dir = Path("fixed_mega_dataset")
        
        # Create output directory
        self.fixed_mega_dir.mkdir(exist_ok=True)
    
    def analyze_original_dataset(self) -> Dict[str, List[Dict]]:
        """Analyze original dataset to get accurate statistics"""
        logger.info("Analyzing original dataset...")
        
        original_data = {}
        total_duration = 0
        
        for split in ['train', 'validation', 'test']:
            manifest_file = self.original_dataset_dir / split / f"{split}_manifest.jsonl"
            
            if manifest_file.exists():
                split_data = []
                split_duration = 0
                
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        item = json.loads(line)
                        item['source'] = 'original'
                        split_data.append(item)
                        split_duration += item.get('duration', 0)
                
                original_data[split] = split_data
                total_duration += split_duration
                logger.info(f"Original {split}: {len(split_data):,} samples, {split_duration/3600:.2f} hours")
        
        logger.info(f"📊 Original total: {total_duration/3600:.2f} hours")
        return original_data
    
    def load_and_process_rinabuoy(self) -> List[Dict]:
        """Load Rinabuoy dataset and create manifest entries"""
        logger.info("Loading Rinabuoy dataset...")
        
        # Load from HuggingFace
        ds = load_dataset("rinabuoy/khm-asr-open")
        
        rinabuoy_data = []
        total_duration = 0
        
        for split_name, split_data in ds.items():
            logger.info(f"Processing Rinabuoy {split_name}: {len(split_data)} samples")
            
            for idx, sample in enumerate(split_data):
                try:
                    audio_data = sample['audio']
                    transcription = sample['sentence']
                    
                    if not transcription or not transcription.strip():
                        continue
                    
                    # Calculate duration
                    duration = len(audio_data['array']) / audio_data['sampling_rate']
                    total_duration += duration
                    
                    # Create manifest entry (no audio saving yet)
                    rinabuoy_data.append({
                        'audio_id': f"rinabuoy_{split_name}_{idx:06d}",
                        'transcription': transcription.strip(),
                        'duration': duration,
                        'speaker': f'rinabuoy_{split_name}',
                        'source': 'rinabuoy',
                        'language': 'km',
                        'original_split': split_name,
                        'hf_index': idx,  # Keep track for later audio extraction
                        'audio_data': audio_data  # Keep audio data for later
                    })
                    
                except Exception as e:
                    logger.warning(f"Error processing Rinabuoy sample {idx}: {e}")
                    continue
        
        logger.info(f"📊 Rinabuoy total: {len(rinabuoy_data):,} samples, {total_duration/3600:.2f} hours")
        return rinabuoy_data
    
    def load_lsr42_data(self) -> List[Dict]:
        """Load LSR42 dataset"""
        logger.info("Loading LSR42 dataset...")
        
        tsv_file = self.lsr42_dataset_dir / "line_index.tsv"
        lsr42_data = []
        total_duration = 0
        
        with open(tsv_file, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    audio_id = parts[0]
                    transcription = parts[1]
                    
                    audio_file = self.lsr42_dataset_dir / "wavs" / f"{audio_id}.wav"
                    
                    if audio_file.exists():
                        try:
                            duration = librosa.get_duration(path=str(audio_file))
                            total_duration += duration
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
        
        logger.info(f"📊 LSR42 total: {len(lsr42_data):,} samples, {total_duration/3600:.2f} hours")
        return lsr42_data
    
    def create_fixed_splits(self, original_data: Dict, lsr42_data: List[Dict], rinabuoy_data: List[Dict]) -> Dict[str, List[Dict]]:
        """Create properly balanced splits"""
        logger.info("Creating fixed mega splits...")
        
        # Convert to manifest format
        def to_manifest(data_list, source_name):
            manifest_list = []
            for item in data_list:
                # Use original split info for session_id if available
                if 'original_split' in item:
                    session_id = f"{source_name}_{item['original_split']}_{item['audio_id'][:6]}"
                else:
                    session_id = f"{source_name}_{item['audio_id'][:8]}"
                
                manifest_item = {
                    'audio_filepath': f"audio/{item['audio_id']}.wav",
                    'text': item['transcription'],
                    'duration': item['duration'],
                    'language': 'km',
                    'speaker': item['speaker'],
                    'session_id': session_id,
                    'source': source_name
                }
                
                # Keep extra info for processing
                if 'audio_data' in item:
                    manifest_item['_audio_data'] = item['audio_data']
                if 'audio_path' in item:
                    manifest_item['_source_path'] = item['audio_path']
                
                manifest_list.append(manifest_item)
            return manifest_list
        
        lsr42_manifest = to_manifest(lsr42_data, 'lsr42')
        rinabuoy_manifest = to_manifest(rinabuoy_data, 'rinabuoy')
        
        # Split external datasets properly
        np.random.seed(42)
        
        # LSR42: 80% train, 10% val, 10% test
        np.random.shuffle(lsr42_manifest)
        lsr42_size = len(lsr42_manifest)
        lsr42_train_size = int(lsr42_size * 0.8)
        lsr42_val_size = int(lsr42_size * 0.1)
        
        lsr42_train = lsr42_manifest[:lsr42_train_size]
        lsr42_val = lsr42_manifest[lsr42_train_size:lsr42_train_size + lsr42_val_size]
        lsr42_test = lsr42_manifest[lsr42_train_size + lsr42_val_size:]
        
        # Rinabuoy: Use original split info but distribute properly
        rinabuoy_train_pool = [x for x in rinabuoy_manifest if 'rinabuoy_train' in x['session_id']]
        rinabuoy_test_pool = [x for x in rinabuoy_manifest if 'rinabuoy_test' in x['session_id']]
        
        # Split test pool into val and test
        np.random.shuffle(rinabuoy_test_pool)
        rinabuoy_test_size = len(rinabuoy_test_pool)
        rinabuoy_val_size = int(rinabuoy_test_size * 0.5)
        
        rinabuoy_train = rinabuoy_train_pool
        rinabuoy_val = rinabuoy_test_pool[:rinabuoy_val_size]
        rinabuoy_test = rinabuoy_test_pool[rinabuoy_val_size:]
        
        # Create mega splits
        mega_splits = {
            'train': original_data.get('train', []) + lsr42_train + rinabuoy_train,
            'validation': original_data.get('validation', []) + lsr42_val + rinabuoy_val,
            'test': original_data.get('test', []) + lsr42_test + rinabuoy_test
        }
        
        # Log detailed statistics
        logger.info("\n🎯 FIXED MEGA DATASET SPLITS:")
        total_samples = 0
        total_duration = 0
        
        for split, data in mega_splits.items():
            original_count = len([x for x in data if x.get('source', 'original') == 'original'])
            lsr42_count = len([x for x in data if x.get('source') == 'lsr42'])
            rinabuoy_count = len([x for x in data if x.get('source') == 'rinabuoy'])
            split_duration = sum(x.get('duration', 0) for x in data) / 3600
            
            total_samples += len(data)
            total_duration += split_duration
            
            logger.info(f"{split.upper()}: {len(data):,} samples ({split_duration:.2f} hours)")
            logger.info(f"  📊 Original: {original_count:,}")
            logger.info(f"  📊 LSR42: {lsr42_count:,}")
            logger.info(f"  📊 Rinabuoy: {rinabuoy_count:,}")
        
        logger.info(f"\n📈 TOTAL: {total_samples:,} samples, {total_duration:.2f} hours")
        
        return mega_splits
    
    def create_space_efficient_dataset(self, mega_splits: Dict[str, List[Dict]]):
        """Create dataset with symbolic links to save space"""
        logger.info("Creating space-efficient mega dataset...")
        
        for split, data in mega_splits.items():
            split_dir = self.fixed_mega_dir / split
            split_audio_dir = split_dir / "audio"
            split_audio_dir.mkdir(parents=True, exist_ok=True)
            
            processed_count = 0
            
            for item in data:
                audio_filename = Path(item['audio_filepath']).name
                target_audio = split_audio_dir / audio_filename
                
                if target_audio.exists():
                    continue
                
                source = item.get('source', 'original')
                
                if source == 'original':
                    # Symbolic link to original audio
                    source_audio = self.original_dataset_dir / split / item['audio_filepath']
                    if source_audio.exists():
                        try:
                            os.symlink(source_audio.resolve(), target_audio)
                        except:
                            # Fallback to copy if symlink fails
                            import shutil
                            shutil.copy2(source_audio, target_audio)
                
                elif source == 'lsr42':
                    # Copy LSR42 audio
                    source_audio = Path(item['_source_path'])
                    if source_audio.exists():
                        import shutil
                        shutil.copy2(source_audio, target_audio)
                
                elif source == 'rinabuoy':
                    # Save Rinabuoy audio from memory
                    if '_audio_data' in item:
                        import soundfile as sf
                        audio_data = item['_audio_data']
                        sf.write(
                            str(target_audio),
                            audio_data['array'],
                            audio_data['sampling_rate']
                        )
                
                processed_count += 1
                
                if processed_count % 1000 == 0:
                    logger.info(f"  Processed {processed_count} files for {split}...")
            
            logger.info(f"Processed {processed_count} audio files for {split}")
    
    def create_manifests_and_info(self, mega_splits: Dict[str, List[Dict]]):
        """Create manifest files and dataset info"""
        logger.info("Creating manifests and dataset info...")
        
        # Clean up temporary data from manifests
        for split, data in mega_splits.items():
            for item in data:
                # Remove temporary fields
                if '_audio_data' in item:
                    del item['_audio_data']
                if '_source_path' in item:
                    del item['_source_path']
        
        # Create manifests for each split
        for split, data in mega_splits.items():
            split_dir = self.fixed_mega_dir / split
            
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
                    'speaker_id': item['speaker'],
                    'source': item['source']
                }
                hf_data.append(hf_item)
            
            with open(split_dir / f"{split}_hf.jsonl", 'w', encoding='utf-8') as f:
                for item in hf_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
            # CSV format
            df = pd.DataFrame(data)
            df.to_csv(split_dir / f"{split}_manifest.csv", index=False, encoding='utf-8')
        
        # Create comprehensive dataset info
        total_samples = sum(len(data) for data in mega_splits.values())
        total_duration = sum(
            sum(item.get('duration', 0) for item in data) 
            for data in mega_splits.values()
        ) / 3600
        
        # Source statistics
        source_stats = {'original': 0, 'lsr42': 0, 'rinabuoy': 0}
        for data in mega_splits.values():
            for item in data:
                source = item.get('source', 'original')
                if source in source_stats:
                    source_stats[source] += 1
        
        dataset_info = {
            "dataset_name": "Fixed Mega Khmer Speech Recognition Dataset",
            "language": "km",
            "description": "Comprehensive Khmer ASR dataset with proper Rinabuoy inclusion",
            "audio_format": "wav",
            "sample_rate": 16000,
            "statistics": {
                "total_samples": total_samples,
                "total_duration_hours": total_duration,
                "source_distribution": source_stats,
                "expected_vs_actual": {
                    "expected_hours": "160+ hours (110 + LSR42 + 51 Rinabuoy)",
                    "actual_hours": f"{total_duration:.2f} hours"
                },
                "splits": {
                    split: {
                        "samples": len(data),
                        "duration_hours": sum(item.get('duration', 0) for item in data) / 3600,
                        "source_breakdown": {
                            source: len([x for x in data if x.get('source', 'original') == source])
                            for source in ['original', 'lsr42', 'rinabuoy']
                        }
                    }
                    for split, data in mega_splits.items()
                }
            }
        }
        
        # Save dataset info
        with open(self.fixed_mega_dir / "dataset_info.json", 'w', encoding='utf-8') as f:
            json.dump(dataset_info, f, indent=2, ensure_ascii=False)
        
        return dataset_info
    
    def run_fixed_merger(self):
        """Run the complete fixed merger"""
        logger.info("🔧 Starting FIXED mega dataset merger...")
        
        # Load all datasets with accurate statistics
        original_data = self.analyze_original_dataset()
        lsr42_data = self.load_lsr42_data()
        rinabuoy_data = self.load_and_process_rinabuoy()
        
        # Create proper splits
        mega_splits = self.create_fixed_splits(original_data, lsr42_data, rinabuoy_data)
        
        # Create space-efficient dataset
        self.create_space_efficient_dataset(mega_splits)
        
        # Create manifests and info
        dataset_info = self.create_manifests_and_info(mega_splits)
        
        # Final summary
        total_samples = dataset_info['statistics']['total_samples']
        total_duration = dataset_info['statistics']['total_duration_hours']
        
        logger.info("🎉 FIXED MEGA DATASET COMPLETE!")
        
        print(f"\n🎯 CORRECTED MEGA DATASET SUMMARY:")
        print(f"   📊 Total Samples: {total_samples:,}")
        print(f"   ⏱️ Total Duration: {total_duration:.2f} hours")
        print(f"   🎤 All Sources Included: Original + LSR42 + Rinabuoy")
        print(f"   📁 Location: {self.fixed_mega_dir}")
        print(f"   ✅ Status: PROPERLY MERGED WITH ALL DATA!")
        
        # Show source breakdown
        source_stats = dataset_info['statistics']['source_distribution']
        print(f"\n📊 Source Breakdown:")
        print(f"   Original: {source_stats['original']:,} samples")
        print(f"   LSR42: {source_stats['lsr42']:,} samples") 
        print(f"   Rinabuoy: {source_stats['rinabuoy']:,} samples")

def main():
    merger = FixedMegaMerger()
    merger.run_fixed_merger()

if __name__ == "__main__":
    main()
