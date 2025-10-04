# Light Deployment Guide - Few Users (2-5 concurrent)

## 🎯 Cost-Optimized for Low Traffic

This guide provides deployment instructions for small-scale usage with minimal costs while maintaining good performance.

## 📋 Instance Recommendations

### **🥇 Recommended: g4dn.large**
- **Cost**: ~$260/month ($0.36/hour)
- **Performance**: 2-6 seconds per request
- **Capacity**: 2-5 concurrent users
- **GPU**: NVIDIA T4 (16GB) - Full acceleration

### **🥈 Budget: t3.large** 
- **Cost**: ~$58/month ($0.08/hour)
- **Performance**: 10-30 seconds per request  
- **Capacity**: 1-3 concurrent users
- **CPU**: Intel Xeon - CPU inference only

### **🥉 Testing: t3.medium**
- **Cost**: ~$30/month ($0.04/hour)
- **Performance**: 15-45 seconds per request
- **Capacity**: 1-2 concurrent users
- **CPU**: Intel Xeon - Development only

## 🚀 Quick Deploy for g4dn.large

### 1. Launch Instance
```bash
# Use Deep Learning AMI (Ubuntu 22.04)
# Instance: g4dn.large
# Storage: 30GB GP3
# Security Group: Ports 22, 80, 5000
```

### 2. Deploy Light Configuration
```bash
# Clone service
git clone <your-repo>
cd whisper-service

# Use light configuration
cp docker-compose-light.yml docker-compose.yml
cp gunicorn-light.conf.py gunicorn.conf.py

# Deploy
docker-compose up --build -d
```

### 3. Monitor Performance
```bash
# Check GPU usage
watch -n 5 nvidia-smi

# Monitor service
curl http://localhost:5000/health

# Test endpoints
curl -X POST -F "file=@test.mp3" http://localhost:5000/transcribe/english
```

## 🚀 CPU-Only Deploy for t3.large

### 1. Modify for CPU-Only
```bash
# Edit docker-compose-light.yml - remove GPU sections:
# Remove:
# - CUDA_VISIBLE_DEVICES=0
# - devices section under deploy.resources.reservations

# Set CPU-only environment
export CUDA_VISIBLE_DEVICES=""
```

### 2. Use Smaller Models
```bash
# Set lighter models for CPU
export WHISPER_MODEL_SIZE=tiny  # Or base
```

### 3. Deploy
```bash
docker-compose -f docker-compose-light.yml up --build -d
```

## 📊 Expected Performance

### g4dn.large (GPU):
- **English**: 2-4 seconds
- **Khmer**: 3-6 seconds  
- **Concurrent**: 2-5 users comfortable
- **Throughput**: 50-100 requests/hour

### t3.large (CPU):
- **English**: 10-20 seconds
- **Khmer**: 15-30 seconds
- **Concurrent**: 1-3 users
- **Throughput**: 10-30 requests/hour

## 💰 Cost Analysis

### Monthly Costs:
| Instance | GPU | Users | Cost/Month | Use Case |
|----------|-----|-------|------------|----------|
| **g4dn.large** | ✅ T4 | 2-5 | $260 | Small business |
| **t3.large** | ❌ CPU | 1-3 | $58 | Personal/testing |
| **t3.medium** | ❌ CPU | 1-2 | $30 | Development |

### Additional Savings:
- **Spot Instances**: Save 50-70%
- **Schedule downtime**: Stop during nights/weekends
- **Reserved Instances**: Save 30% for 1-year commitment

## 🔧 Optimization Tips for Few Users

### 1. Model Selection
```bash
# For GPU instances
WHISPER_MODEL_SIZE=base     # Good balance
WHISPER_MODEL_SIZE=small    # Faster, still accurate

# For CPU instances  
WHISPER_MODEL_SIZE=tiny     # Fastest on CPU
WHISPER_MODEL_SIZE=base     # Better quality, slower
```

### 2. Resource Limits
```yaml
# docker-compose-light.yml
deploy:
  resources:
    limits:
      memory: 6G      # g4dn.large has 8GB total
      cpus: '1.5'     # Leave room for system
```

### 3. Auto-shutdown
```bash
# Create auto-shutdown script for cost savings
cat > auto-shutdown.sh << 'EOF'
#!/bin/bash
# Stop instance at 6 PM if no active requests
hour=$(date +%H)
if [ $hour -eq 18 ]; then
  active=$(netstat -an | grep :5000 | grep ESTABLISHED | wc -l)
  if [ $active -eq 0 ]; then
    sudo shutdown -h +5 "Auto-shutdown: No active users"
  fi
fi
EOF

# Schedule via cron
echo "0 18 * * * /path/to/auto-shutdown.sh" | crontab -
```

## 🎯 When to Upgrade

**Scale up to g4dn.2xlarge when:**
- Consistent 5+ concurrent users
- Response times > 10 seconds
- GPU utilization > 90%
- Queue depth > 5 requests

**Scale down to t3.large when:**
- Budget is primary concern
- Can tolerate 10-30 second responses
- Peak usage < 3 concurrent users
- Development/testing environment

## 🧪 Testing Your Load

```bash
# Test concurrent requests
for i in {1..5}; do
  curl -X POST -F "file=@test$i.mp3" http://localhost:5000/transcribe/english &
done
wait

# Monitor during test
nvidia-smi  # Check GPU usage
htop        # Check CPU/RAM
```

This light configuration will serve few users very cost-effectively while maintaining good performance!
