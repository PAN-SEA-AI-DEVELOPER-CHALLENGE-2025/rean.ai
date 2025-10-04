#!/usr/bin/env python3
"""
Simple SageMaker Package Installer
Minimal approach that works reliably on SageMaker instances
"""

import subprocess
import sys

def install_simple():
    """Simple, reliable installation for SageMaker"""
    
    print("🚀 Simple SageMaker Installation")
    print("=" * 40)
    
    # Step 1: Core packages that usually work
    basic_installs = [
        "pip install --upgrade pip",
        "pip install torch torchvision torchaudio",
        "pip install transformers datasets",
        "pip install boto3 sagemaker",
        "pip install pandas numpy scikit-learn",
        "pip install tqdm evaluate jiwer",
        "pip install accelerate"
    ]
    
    print("📦 Installing basic packages...")
    for cmd in basic_installs:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True)
    
    # Step 2: Try conda for librosa (most reliable)
    print("\n🎵 Installing audio packages...")
    audio_commands = [
        "conda install -c conda-forge librosa numba -y",
        "pip install soundfile resampy"
    ]
    
    for cmd in audio_commands:
        print(f"Running: {cmd}")
        try:
            subprocess.run(cmd, shell=True, check=True)
            print("✅ Success")
        except subprocess.CalledProcessError:
            print("⚠️ Command failed, continuing...")
    
    # Step 3: Fallback for librosa if conda failed
    print("\n🔄 Fallback librosa installation...")
    fallback_commands = [
        "pip install numba==0.56.4",  # Specific working version
        "pip install librosa==0.9.2 --no-deps",  # No dependencies to avoid conflicts
        "pip install joblib>=0.14",  # Required dependency
        "pip install decorator>=4.0.11",  # Required dependency
    ]
    
    for cmd in fallback_commands:
        print(f"Running: {cmd}")
        subprocess.run(cmd, shell=True)
    
    print("\n✅ Installation complete!")
    
    # Quick test
    print("\n🔍 Quick test...")
    test_code = """
import torch
import transformers
import datasets
import pandas as pd
import numpy as np
print("✅ Core packages working!")
try:
    import librosa
    print(f"✅ Librosa working: {librosa.__version__}")
except:
    print("⚠️ Librosa may need manual install")
try:
    import soundfile
    print("✅ Soundfile working")
except:
    print("⚠️ Soundfile may need manual install")
"""
    
    exec(test_code)

if __name__ == "__main__":
    install_simple()