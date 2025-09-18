# 🧪 Voice Processing Testing Guide

This guide explains how to test the Khmer voice splitting and segmentation functionality.

## 📋 Prerequisites

1. **Server Running**: Make sure the API server is running on port 8000
   ```bash
   python start_server.py
   ```

2. **Dependencies Installed**: Install all required dependencies
   ```bash
   pip install -r requirements.txt
   ```

3. **Test Audio Files**: Prepare Khmer audio files for testing (WAV format recommended)

## 🎯 Quick Testing Methods

### Method 1: Automated Test Suite
Run the comprehensive test suite:
```bash
python tests/test_voice_processing.py
```

This will test:
- ✅ Service availability (VAD, Whisper, MFA, CSV)
- ✅ Session management
- ✅ CSV export functionality
- ✅ File processing (if test files are available)

### Method 2: Interactive Demo
Run the interactive demo script:
```bash
python examples/test_khmer_voice_processing.py
```

This will:
- 🔍 Check all services
- 🎙️ Process any available test files
- 📊 Download CSV results
- 📋 Show session details

### Method 3: Manual API Testing
Test individual endpoints using curl or the API docs.

## 🔧 Detailed Testing Steps

### Step 1: Check Service Status
```bash
curl -X GET "http://localhost:8000/api/voice/status"
```

Expected response:
```json
{
  "s3_service": true,
  "vad_service": true,
  "transcription_service": true,
  "mfa_service": false,
  "csv_service": true,
  "use_mfa": false,
  "save_chunks": true
}
```

### Step 2: Prepare Test Audio

Create a test Khmer audio file:
1. **Record**: Record 30-60 seconds of Khmer speech
2. **Format**: Save as WAV file (16kHz or 22kHz recommended)
3. **Location**: Place in one of these locations:
   - `data/temp/test_khmer_audio.wav`
   - `result/sample_khmer.wav`
   - Any custom path

### Step 3: Process Audio File

#### Option A: Local File Processing
```bash
curl -X POST "http://localhost:8000/api/voice/process" \
  -H "Content-Type: application/json" \
  -d '{
    "local_file_path": "data/temp/test_khmer_audio.wav",
    "use_mfa": false,
    "save_chunks": true,
    "vad_aggressiveness": 2,
    "min_chunk_duration": 1.5,
    "max_chunk_duration": 5.0,
    "transcription_model": "base"
  }'
```

#### Option B: S3 File Processing (if S3 configured)
```bash
curl -X POST "http://localhost:8000/api/voice/process" \
  -H "Content-Type: application/json" \
  -d '{
    "s3_key": "audio-files/khmer-speech-01.wav",
    "use_mfa": false,
    "save_chunks": true,
    "transcription_model": "base"
  }'
```

Expected response:
```json
{
  "success": true,
  "session_id": "abc123...",
  "processing_duration": 15.32,
  "data": {
    "total_chunks": 8,
    "total_duration": 45.6,
    "speech_ratio": 0.85,
    "successful_transcriptions": 8,
    "failed_transcriptions": 0,
    "saved_chunks": 8,
    "csv_exported": true,
    "chunks_summary": [...]
  }
}
```

### Step 4: Verify Results

#### Check Session Details
```bash
curl -X GET "http://localhost:8000/api/voice/sessions/{session_id}"
```

#### List Available CSV Files
```bash
curl -X GET "http://localhost:8000/api/voice/sessions/{session_id}/csv"
```

#### Download CSV Results
```bash
# Download chunks metadata
curl -O "http://localhost:8000/api/voice/download/chunks.csv"

# Download word-level data
curl -O "http://localhost:8000/api/voice/download/words.csv"
```

### Step 5: Examine Results

#### Audio Chunks
Check the `result/chunks/` directory for saved audio chunks:
```bash
ls -la result/chunks/
```

Expected files:
```
test_khmer_audio_chunk_0.wav
test_khmer_audio_chunk_1.wav
test_khmer_audio_chunk_2.wav
...
```

#### CSV Metadata
Open the CSV files to see the results:

**chunks.csv** contains:
- `session_id`: Processing session identifier
- `chunk_id`: Individual chunk identifier
- `file_path`: Path to the audio chunk file
- `start_time`, `end_time`, `duration`: Timing information
- `transcription`: Khmer transcribed text
- `language`: Detected language (should be 'km' for Khmer)
- `speaker`: Speaker identifier
- `word_count`: Number of words in transcription

**words.csv** contains:
- Word-level timestamps and confidence scores
- Individual Khmer words with precise timing
- MFA-refined timestamps (if MFA was used)

## 🎛️ Configuration Options

### VAD (Voice Activity Detection) Settings
```json
{
  "vad_aggressiveness": 2,     // 0-3, 2 is optimal for Khmer
  "min_chunk_duration": 1.5,  // Minimum chunk length (seconds)
  "max_chunk_duration": 5.0   // Maximum chunk length (seconds)
}
```

### Transcription Settings
```json
{
  "transcription_model": "base",  // tiny, base, small, medium, large
  "use_mfa": false,              // Enable word-level alignment
  "save_chunks": true            // Save individual audio files
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Service Unavailable
```
Error: "Transcription service not available"
```
**Solution**: Check if Whisper model is properly installed:
```bash
python -c "import whisper; print('Whisper available')"
```

#### 2. Empty Transcriptions
```
Result: All chunks have empty transcriptions
```
**Possible causes**:
- Audio quality too low
- Background noise too high
- VAD settings too aggressive
- Audio file format not supported

**Solutions**:
- Reduce `vad_aggressiveness` to 1 or 2
- Use higher quality audio files
- Check audio file format (WAV recommended)

#### 3. MFA Alignment Fails
```
Error: "MFA alignment failed"
```
**Cause**: MFA requires custom Khmer models that may not be available.
**Solution**: Set `"use_mfa": false` for initial testing.

#### 4. CSV Export Issues
```
Error: "CSV export failed"
```
**Check**:
- File permissions in the result directory
- Disk space availability
- UTF-8 encoding support

### Performance Tips

1. **Audio Quality**: Use clean, high-quality Khmer speech recordings
2. **File Size**: Start with shorter files (30-60 seconds) for testing
3. **Model Selection**: Use 'base' model for balance of speed/accuracy
4. **Chunk Duration**: Use 1.5-5 second chunks for optimal Khmer processing

## 📊 Expected Output Examples

### Successful Processing Log
```
🎙️ Processing local file: data/temp/test_khmer_audio.wav
✅ Processing completed successfully!
📋 Session ID: 123e4567-e89b-12d3-a456-426614174000
⏱️  Processing Time: 12.45s

📊 Results:
   🔊 Total Chunks: 6
   📏 Total Duration: 38.2s
   🎯 Speech Ratio: 87.5%
   ✅ Successful Transcriptions: 6
   ❌ Failed Transcriptions: 0
   💾 Saved Chunks: 6
   📊 CSV Exported: true
```

### CSV Output Example (chunks.csv)
```csv
session_id,chunk_id,file_path,start_time,end_time,transcription,language,speaker
123e4567...,0,result/chunks/test_chunk_0.wav,0.0,3.2,សួស្តី​ អ្នក​ទាំងអស់​គ្នា,km,speaker_1
123e4567...,1,result/chunks/test_chunk_1.wav,3.2,6.8,ខ្ញុំ​នាម​ ស៊ុន​ សុភា,km,speaker_1
...
```

## 🎉 Success Criteria

Your voice processing system is working correctly if:

✅ **Service Status**: All services report as available  
✅ **Processing**: Audio files are processed without errors  
✅ **Chunking**: Audio is split into 1.5-5 second segments  
✅ **Transcription**: Khmer text is generated for each chunk  
✅ **CSV Export**: Metadata files are created with proper UTF-8 encoding  
✅ **File Output**: Audio chunks are saved (if enabled)  
✅ **Session Management**: Sessions can be listed and detailed  

## 📚 Next Steps

After successful testing:

1. **Production Setup**: Configure environment variables in `.env`
2. **S3 Integration**: Set up AWS S3 for cloud storage
3. **MFA Training**: Train custom Khmer MFA models for better alignment
4. **Batch Processing**: Process multiple files in production
5. **Monitoring**: Set up logging and monitoring for production use

For more details, check the API documentation at: http://localhost:8000/docs
