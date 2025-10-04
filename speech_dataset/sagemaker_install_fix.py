#!/usr/bin/env python3
"""
SageMaker Package Installation Fix
Handles librosa compilation issues on SageMaker instances
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run shell command with error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ Success: {description}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        print(f"Error: {e.stderr}")
        return False

def fix_sagemaker_packages():
    """Install packages with SageMaker-specific fixes"""
    
    print("🚀 SageMaker Package Installation Fix")
    print("=" * 50)
    
    # SageMaker-compatible commands (no sudo needed)
    commands = [
        # Update conda and pip
        ("pip install --upgrade pip", "Upgrading pip"),
        
        # Install core ML packages first
        ("pip install torch torchvision torchaudio --no-cache-dir", "Installing PyTorch"),
        ("pip install transformers>=4.35.0 --no-cache-dir", "Installing Transformers"),
        ("pip install datasets>=2.14.0 --no-cache-dir", "Installing Datasets"),
        
        # Install numba first (critical for librosa) - try conda first
        ("conda install -c conda-forge numba -y", "Installing numba via conda"),
        
        # Try librosa via conda-forge (pre-compiled, avoids compilation issues)
        ("conda install -c conda-forge librosa -y", "Installing librosa via conda"),
        
        # Install remaining audio packages
        ("pip install soundfile>=0.12.0 --no-cache-dir", "Installing soundfile"),
        ("pip install resampy>=0.4.0 --no-cache-dir", "Installing resampy"),
        
        # Install evaluation and ML packages
        ("pip install evaluate>=0.4.0 --no-cache-dir", "Installing evaluate"),
        ("pip install jiwer>=3.0.0 --no-cache-dir", "Installing jiwer"),
        ("pip install accelerate>=0.24.0 --no-cache-dir", "Installing accelerate"),
        ("pip install scikit-learn --no-cache-dir", "Installing scikit-learn"),
        ("pip install pandas --no-cache-dir", "Installing pandas"),
        ("pip install numpy --no-cache-dir", "Installing numpy"),
        
        # Install AWS packages
        ("pip install boto3 --no-cache-dir", "Installing boto3"),
        ("pip install sagemaker --no-cache-dir", "Installing sagemaker"),
        
        # Install optional packages
        ("pip install tensorboard --no-cache-dir", "Installing tensorboard"),
        ("pip install tqdm --no-cache-dir", "Installing tqdm"),
        ("pip install psutil --no-cache-dir", "Installing psutil"),
    ]
    
    # Fallback commands if conda fails
    fallback_commands = [
        ("pip install numba>=0.56.0 --no-cache-dir", "Installing numba via pip (fallback)"),
        ("pip install librosa==0.9.2 --no-deps --no-cache-dir", "Installing librosa 0.9.2 (fallback)"),
    ]
    
    # Execute main commands
    librosa_installed = False
    for command, description in commands:
        success = run_command(command, description)
        if "librosa via conda" in description and success:
            librosa_installed = True
    
    # Try fallbacks if librosa failed
    if not librosa_installed:
        print("\n🔄 Trying fallback installation methods...")
        for command, description in fallback_commands:
            run_command(command, description)
    
    print("\n🔍 Verifying installation...")
    
    # Verification script
    verification_code = '''
try:
    import torch
    import transformers
    import datasets
    import librosa
    import soundfile
    import evaluate
    import boto3
    import numpy as np
    import pandas as pd
    
    print("✅ All critical packages imported successfully!")
    print(f"PyTorch: {torch.__version__}")
    print(f"Transformers: {transformers.__version__}")
    print(f"Librosa: {librosa.__version__}")
    print(f"CUDA: {torch.cuda.is_available()}")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
'''
    
    # Write and run verification
    with open("/tmp/verify_packages.py", "w") as f:
        f.write(verification_code)
    
    run_command("python /tmp/verify_packages.py", "Package verification")
    
    print("\n🎉 SageMaker package installation complete!")
    print("\n💡 Usage in notebook:")
    print("   !python sagemaker_install_fix.py")

if __name__ == "__main__":
    fix_sagemaker_packages()