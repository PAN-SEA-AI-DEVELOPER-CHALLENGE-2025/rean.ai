#!/usr/bin/env python3
"""
Fix LSR42 missing transcripts in the fixed_mega_dataset
Maps transcripts from lsr42_dataset/km_kh_male/line_index.tsv to the manifest files
"""

import json
import pandas as pd
import os
from pathlib import Path

def load_lsr42_transcripts():
    """Load LSR42 transcripts from the line_index.tsv file"""
    transcript_file = "lsr42_dataset/km_kh_male/line_index.tsv"
    
    if not os.path.exists(transcript_file):
        print(f"❌ Transcript file not found: {transcript_file}")
        return {}
    
    print(f"📖 Loading transcripts from {transcript_file}")
    
    # Read the TSV file - first column is filename, third column is transcript
    transcripts = {}
    
    with open(transcript_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            parts = line.strip().split('\t')
            if len(parts) >= 3:
                filename = parts[0].strip()
                transcript = parts[2].strip()
                transcripts[filename] = transcript
            else:
                print(f"⚠️ Line {line_num} has {len(parts)} parts, expected at least 3")
    
    print(f"✅ Loaded {len(transcripts)} transcripts")
    return transcripts

def fix_manifest_file(manifest_path, transcripts_dict):
    """Fix a single manifest file by adding missing LSR42 transcripts"""
    print(f"\n🔧 Processing: {manifest_path}")
    
    if not os.path.exists(manifest_path):
        print(f"❌ Manifest file not found: {manifest_path}")
        return False
    
    # Read original manifest
    with open(manifest_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Process each line
    fixed_lines = []
    lsr42_fixed = 0
    lsr42_missing = 0
    
    for line in lines:
        try:
            entry = json.loads(line.strip())
            
            # If this is an LSR42 entry with empty text
            if entry.get('source') == 'lsr42' and entry.get('text', '').strip() == '':
                # Extract filename from audio_filepath
                audio_path = entry['audio_filepath']
                # audio_path is like "audio/khm_0877_3629809050.wav"
                filename = Path(audio_path).stem  # gets "khm_0877_3629809050"
                
                # Look for transcript
                if filename in transcripts_dict:
                    entry['text'] = transcripts_dict[filename]
                    lsr42_fixed += 1
                    print(f"✅ Fixed: {filename} -> '{entry['text'][:50]}...'")
                else:
                    lsr42_missing += 1
                    print(f"❌ No transcript found for: {filename}")
            
            fixed_lines.append(json.dumps(entry, ensure_ascii=False) + '\n')
            
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON decode error: {e}")
            fixed_lines.append(line)  # Keep original line if can't parse
    
    # Write fixed manifest
    backup_path = manifest_path + '.backup'
    print(f"💾 Creating backup: {backup_path}")
    os.rename(manifest_path, backup_path)
    
    with open(manifest_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    print(f"✅ Fixed {lsr42_fixed} LSR42 entries")
    if lsr42_missing > 0:
        print(f"⚠️ {lsr42_missing} LSR42 entries still missing transcripts")
    
    return True

def main():
    print("🔧 Fixing LSR42 missing transcripts in fixed_mega_dataset")
    print("=" * 60)
    
    # Load LSR42 transcripts
    transcripts = load_lsr42_transcripts()
    
    if not transcripts:
        print("❌ No transcripts loaded. Exiting.")
        return
    
    # Process each manifest file
    manifest_files = [
        "fixed_mega_dataset/train/train_manifest.jsonl",
        "fixed_mega_dataset/validation/validation_manifest.jsonl", 
        "fixed_mega_dataset/test/test_manifest.jsonl"
    ]
    
    for manifest_file in manifest_files:
        if os.path.exists(manifest_file):
            success = fix_manifest_file(manifest_file, transcripts)
            if not success:
                print(f"❌ Failed to process {manifest_file}")
        else:
            print(f"⚠️ Manifest file not found: {manifest_file}")
    
    print("\n" + "=" * 60)
    print("🎉 LSR42 transcript fixing complete!")
    print("\nTo verify the fix:")
    print("grep 'lsr42' fixed_mega_dataset/train/train_manifest.jsonl | head -2")

if __name__ == "__main__":
    main()