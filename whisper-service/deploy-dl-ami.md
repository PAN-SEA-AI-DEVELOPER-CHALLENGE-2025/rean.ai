# Deployment Guide for Deep Learning AMI (Ubuntu 22.04)

## 🎯 Optimized for 20-30 Concurrent Users

This guide provides specific instructions for deploying your dual-language transcription service on AWS Deep Learning AMI with GPU acceleration.

## 📋 Prerequisites

### 1. Launch EC2 Instance
- **AMI**: Deep Learning AMI (Ubuntu 22.04) Version 77.0 or later
- **Instance Type**: **g4dn.2xlarge** (recommended for 20-30 users)
- **Storage**: 50GB GP3 EBS volume (minimum)
- **Security Group**: Allow ports 22 (SSH), 80 (HTTP), 5000 (API)

### 2. Instance Specifications Verification
```bash
# Verify GPU availability
nvidia-smi

# Check CUDA version
nvcc --version

# Verify Docker with GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

## 🚀 Quick Deployment

### 1. Clone and Setup
```bash
# Clone your service
git clone <your-repo>
cd whisper-service

# Verify Deep Learning AMI has required tools
which docker
which docker-compose
which nvidia-docker
```

### 2. Configure for GPU
```bash
# Set environment variables for optimal performance
export CUDA_VISIBLE_DEVICES=0
export WHISPER_MODEL_SIZE=turbo

# Enable GPU support for Docker
sudo systemctl restart docker
```

### 3. Deploy with GPU Support
```bash
# Build and run with GPU acceleration
docker-compose up --build -d

# Monitor GPU usage
watch -n 1 nvidia-smi
```

### 4. Performance Optimization
```bash
# Increase file descriptor limits for concurrent connections
echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf

# Optimize network settings
echo "net.core.somaxconn = 1024" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## 📊 Performance Tuning for Concurrent Users

### 1. Application-Level Optimization
Add these environment variables to your docker-compose.yml:

```yaml
environment:
  - WORKERS=4                    # Gunicorn workers
  - THREADS=8                   # Threads per worker  
  - MAX_REQUESTS=1000          # Requests per worker before restart
  - TIMEOUT=300                # Request timeout (5 minutes)
  - KEEPALIVE=2                # Keep-alive connections
```

### 2. Create Production Dockerfile
```dockerfile
# Add to end of Dockerfile
FROM your-existing-dockerfile

# Install Gunicorn for production
RUN pip install gunicorn[gevent]==21.2.0

# Production startup command
CMD ["gunicorn", "--workers", "4", "--threads", "8", "--timeout", "300", "--bind", "0.0.0.0:5000", "--max-requests", "1000", "--preload", "app:app"]
```

### 3. Load Balancer Setup (Optional)
For high availability, set up Application Load Balancer:

```bash
# Create target group
aws elbv2 create-target-group \
  --name whisper-service-targets \
  --protocol HTTP \
  --port 5000 \
  --vpc-id <your-vpc-id> \
  --health-check-path /health \
  --health-check-interval-seconds 30 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3
```

## 🔧 Monitoring & Scaling

### 1. Resource Monitoring
```bash
# Create monitoring script
cat > monitor.sh << 'EOF'
#!/bin/bash
while true; do
  echo "=== $(date) ==="
  echo "GPU Usage:"
  nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
  echo "CPU Usage:"
  top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1
  echo "Memory Usage:"
  free -h | grep Mem: | awk '{print $3"/"$2}'
  echo "Active Connections:"
  netstat -an | grep :5000 | grep ESTABLISHED | wc -l
  echo "================================"
  sleep 30
done
EOF

chmod +x monitor.sh
nohup ./monitor.sh > monitoring.log 2>&1 &
```

### 2. Auto-scaling Trigger Points
Monitor these metrics for scaling decisions:

| Metric | Scale Up Threshold | Scale Down Threshold |
|--------|-------------------|---------------------|
| **GPU Utilization** | > 80% for 5+ minutes | < 30% for 10+ minutes |
| **CPU Utilization** | > 70% for 5+ minutes | < 40% for 10+ minutes |
| **Memory Usage** | > 85% | < 50% |
| **Response Time** | > 10 seconds avg | < 3 seconds avg |

### 3. Horizontal Scaling
When vertical scaling isn't enough:

```bash
# Deploy multiple instances behind ALB
# Instance 1: Primary (English + Khmer)
# Instance 2+: English only (faster startup)

# Route traffic based on endpoint:
# /transcribe/english -> All instances
# /transcribe/khmer -> Primary instance only
```

## 💰 Cost Optimization

### Instance Type Comparison for 20-30 Users:

| Instance | Monthly Cost | GPU Memory | Performance | Best For |
|----------|-------------|------------|-------------|----------|
| **g4dn.xlarge** | ~$380 | 16GB | Good | Development/Testing |
| **g4dn.2xlarge** | ~$540 | 16GB | Excellent | **Production** |
| **g5.2xlarge** | ~$870 | 24GB | Premium | High-performance needs |

### Cost-Saving Tips:
1. **Use Spot Instances**: Save 50-70% with interruption tolerance
2. **Reserved Instances**: Save 30-60% for 1-3 year commitments  
3. **Schedule downtime**: Stop instances during off-hours
4. **Monitor usage**: Use CloudWatch to optimize resource allocation

## 🚨 Troubleshooting

### Common Issues:

1. **GPU Not Detected**
```bash
# Check Docker GPU support
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi

# Restart Docker daemon
sudo systemctl restart docker
```

2. **Model Loading Failures**
```bash
# Check disk space (models are large)
df -h

# Verify CUDA/PyTorch compatibility
python -c "import torch; print(torch.cuda.is_available())"
```

3. **High Memory Usage**
```bash
# Clear GPU memory
sudo fuser -v /dev/nvidia*
# Restart service if needed
docker-compose restart
```

4. **Slow Response Times**
```bash
# Check concurrent connections
netstat -an | grep :5000 | grep ESTABLISHED | wc -l

# Monitor GPU utilization
nvidia-smi -l 1
```

## 🎯 Performance Expectations

### Expected Performance on g4dn.2xlarge:
- **English (Whisper)**: 2-6 seconds per request
- **Khmer (MMS)**: 3-8 seconds per request  
- **Concurrent capacity**: 20-30 users comfortably
- **Peak throughput**: ~300-500 requests/hour
- **GPU utilization**: 60-80% under load

### Scaling Indicators:
- **Scale up** when response times > 10 seconds consistently
- **Scale down** when GPU utilization < 30% for extended periods
- **Add instances** when queue depth > 10 requests

This configuration should handle your 20-30 concurrent users efficiently while maintaining good response times and cost-effectiveness.
