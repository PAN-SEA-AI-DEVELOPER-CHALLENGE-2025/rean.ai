#!/usr/bin/env python3
"""
Conflict-Free SageMaker Installation
Handles dependency conflicts and ensures working Whisper setup
"""

import subprocess
import sys

def run_cmd(cmd, description, ignore_errors=False):
    """Run command with proper error handling"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        if ignore_errors:
            print(f"⚠️ {description} - Warning (continuing): {e.stderr.strip()}")
            return False
        else:
            print(f"❌ {description} - Failed: {e.stderr.strip()}")
            return False

def install_whisper_dependencies():
    """Install only essential packages for Whisper training"""
    
    print("🚀 Installing Whisper Training Dependencies")
    print("=" * 50)
    
    # Step 1: Essential packages only
    essential_commands = [
        ("pip install --upgrade pip setuptools wheel", "Upgrading pip tools"),
        ("conda install -c conda-forge librosa numba -y", "Installing audio processing"),
        ("pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118", "Installing PyTorch with CUDA"),
        ("pip install transformers==4.35.2", "Installing Transformers (specific version)"),
        ("pip install datasets==2.14.7", "Installing Datasets (specific version)"),
        ("pip install soundfile", "Installing SoundFile"),
    ]
    
    for cmd, desc in essential_commands:
        run_cmd(cmd, desc, ignore_errors=True)
    
    # Step 2: Training specific packages
    training_commands = [
        ("pip install evaluate jiwer", "Installing evaluation metrics"),
        ("pip install accelerate", "Installing training acceleration"),
        ("pip install boto3", "Installing AWS SDK"),
        ("pip install tqdm", "Installing progress bars"),
    ]
    
    print("\n📊 Installing training packages...")
    for cmd, desc in training_commands:
        run_cmd(cmd, desc, ignore_errors=True)
    
    # Step 3: Fix dependency conflicts
    print("\n🔧 Resolving dependency conflicts...")
    fix_commands = [
        ("pip install --upgrade multiprocess>=0.70.18", "Fixing multiprocess version"),
        ("pip install --force-reinstall --no-deps datasets", "Reinstalling datasets without deps"),
    ]
    
    for cmd, desc in fix_commands:
        run_cmd(cmd, desc, ignore_errors=True)
    
    # Step 4: Verification
    print("\n🔍 Testing critical imports...")
    test_imports()

def test_imports():
    """Test critical package imports"""
    packages = {
        "torch": "PyTorch",
        "transformers": "Transformers", 
        "datasets": "Datasets",
        "librosa": "Librosa",
        "soundfile": "SoundFile",
        "evaluate": "Evaluate",
        "boto3": "AWS SDK",
        "accelerate": "Accelerate"
    }
    
    working = []
    failed = []
    
    for pkg, name in packages.items():
        try:
            __import__(pkg)
            working.append(name)
            print(f"✅ {name}")
        except ImportError as e:
            failed.append((name, str(e)))
            print(f"❌ {name}: {e}")
    
    print(f"\n📊 Results: {len(working)}/{len(packages)} packages working")
    
    if failed:
        print("\n🔧 Manual fixes for failed packages:")
        for name, error in failed:
            if "librosa" in name.lower():
                print("   !conda install -c conda-forge librosa -y")
            elif "soundfile" in name.lower():
                print("   !pip install soundfile --force-reinstall")
            else:
                print(f"   !pip install {name.lower()} --force-reinstall")
    
    # Show system info if torch works
    try:
        import torch
        print(f"\n🎯 System Info:")
        print(f"   Python: {sys.version.split()[0]}")
        print(f"   PyTorch: {torch.__version__}")
        print(f"   CUDA: {torch.cuda.is_available()}")
        if torch.cuda.is_available():
            print(f"   GPU: {torch.cuda.get_device_name(0)}")
    except:
        pass
    
    return len(failed) == 0

def create_requirements_minimal():
    """Create minimal requirements file that actually works"""
    minimal_reqs = """# Minimal Working Requirements for Whisper on SageMaker
torch>=2.0.0
transformers==4.35.2
datasets==2.14.7
librosa==0.10.1
soundfile>=0.12.1
evaluate>=0.4.0
jiwer>=3.0.0
accelerate>=0.24.0
boto3>=1.28.0
tqdm>=4.65.0
numpy>=1.24.0
"""
    
    with open("minimal_requirements.txt", "w") as f:
        f.write(minimal_reqs)
    
    print("📝 Created minimal_requirements.txt")

if __name__ == "__main__":
    install_whisper_dependencies()
    create_requirements_minimal()
    
    print("\n🎉 Installation complete!")
    print("\n💡 Next steps:")
    print("   1. If any packages failed, run the suggested manual fixes")
    print("   2. Restart your kernel")
    print("   3. Continue with your Whisper training notebook")
    print("   4. Ignore multiprocess version warnings - they won't affect training")