#!/bin/bash

# Khmer Voice Processing API Test Script
# This script tests the voice processing functionality using curl commands

set -e  # Exit on any error

# Configuration
API_BASE="http://localhost:8000"
TEST_FILE="data/temp/test_khmer_audio.wav"
SESSION_ID=""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Test functions
test_api_health() {
    log_info "Testing API health..."
    
    if curl -s -f "$API_BASE/health" > /dev/null; then
        log_success "API server is running"
        return 0
    else
        log_error "API server is not responding"
        log_info "Make sure the server is running: python start_server.py"
        return 1
    fi
}

test_service_status() {
    log_info "Checking voice processing services..."
    
    response=$(curl -s "$API_BASE/api/voice/status")
    
    if [ $? -eq 0 ]; then
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        log_success "Service status retrieved"
        return 0
    else
        log_error "Failed to get service status"
        return 1
    fi
}

test_process_local_file() {
    local file_path="$1"
    
    log_info "Testing local file processing: $file_path"
    
    if [ ! -f "$file_path" ]; then
        log_warning "Test file not found: $file_path"
        log_info "Create a test Khmer audio file at this location"
        return 1
    fi
    
    # Prepare request payload
    local request_data='{
        "local_file_path": "'$file_path'",
        "use_mfa": false,
        "save_chunks": true,
        "vad_aggressiveness": 2,
        "min_chunk_duration": 1.5,
        "max_chunk_duration": 5.0,
        "transcription_model": "base"
    }'
    
    log_info "Sending processing request..."
    echo "Request payload:"
    echo "$request_data" | jq '.' 2>/dev/null || echo "$request_data"
    
    # Send request
    local response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$request_data" \
        "$API_BASE/api/voice/process")
    
    if [ $? -eq 0 ]; then
        echo "Response:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        
        # Extract session ID
        SESSION_ID=$(echo "$response" | jq -r '.session_id' 2>/dev/null || echo "")
        
        if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "null" ]; then
            log_success "Processing completed! Session ID: $SESSION_ID"
            return 0
        else
            log_error "Processing failed or session ID not found"
            return 1
        fi
    else
        log_error "Failed to send processing request"
        return 1
    fi
}

test_session_details() {
    local session_id="$1"
    
    if [ -z "$session_id" ]; then
        log_warning "No session ID provided for session details test"
        return 1
    fi
    
    log_info "Getting session details: $session_id"
    
    local response=$(curl -s "$API_BASE/api/voice/sessions/$session_id")
    
    if [ $? -eq 0 ]; then
        echo "Session details:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        log_success "Session details retrieved"
        return 0
    else
        log_error "Failed to get session details"
        return 1
    fi
}

test_csv_download() {
    local session_id="$1"
    
    if [ -z "$session_id" ]; then
        log_warning "No session ID provided for CSV download test"
        return 1
    fi
    
    log_info "Testing CSV download for session: $session_id"
    
    # Create downloads directory
    mkdir -p downloads
    
    # List available CSV files
    local csv_info=$(curl -s "$API_BASE/api/voice/sessions/$session_id/csv")
    echo "Available CSV files:"
    echo "$csv_info" | jq '.' 2>/dev/null || echo "$csv_info"
    
    # Download chunks.csv
    log_info "Downloading chunks.csv..."
    if curl -s -o "downloads/chunks.csv" "$API_BASE/api/voice/download/chunks.csv"; then
        local line_count=$(wc -l < "downloads/chunks.csv" 2>/dev/null || echo "0")
        log_success "Downloaded chunks.csv ($line_count lines)"
        
        # Show first few lines
        log_info "First 3 lines of chunks.csv:"
        head -n 3 "downloads/chunks.csv" 2>/dev/null || echo "Cannot read file"
    else
        log_error "Failed to download chunks.csv"
    fi
    
    # Download words.csv
    log_info "Downloading words.csv..."
    if curl -s -o "downloads/words.csv" "$API_BASE/api/voice/download/words.csv"; then
        local line_count=$(wc -l < "downloads/words.csv" 2>/dev/null || echo "0")
        log_success "Downloaded words.csv ($line_count lines)"
    else
        log_warning "Failed to download words.csv (may not exist)"
    fi
}

test_list_sessions() {
    log_info "Listing recent sessions..."
    
    local response=$(curl -s "$API_BASE/api/voice/sessions?limit=5")
    
    if [ $? -eq 0 ]; then
        echo "Recent sessions:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        log_success "Session list retrieved"
        return 0
    else
        log_error "Failed to list sessions"
        return 1
    fi
}

test_cleanup() {
    log_info "Testing cleanup functionality..."
    
    local response=$(curl -s -X POST "$API_BASE/api/voice/cleanup")
    
    if [ $? -eq 0 ]; then
        echo "Cleanup response:"
        echo "$response" | jq '.' 2>/dev/null || echo "$response"
        log_success "Cleanup completed"
        return 0
    else
        log_error "Cleanup failed"
        return 1
    fi
}

# Main test execution
main() {
    echo "🇰🇭 Khmer Voice Processing API Test Script"
    echo "================================================"
    
    # Test basic connectivity
    if ! test_api_health; then
        exit 1
    fi
    
    echo ""
    
    # Test service status
    test_service_status
    
    echo ""
    echo "================================================"
    
    # Test file processing
    if test_process_local_file "$TEST_FILE"; then
        echo ""
        echo "================================================"
        
        # Test session details
        test_session_details "$SESSION_ID"
        
        echo ""
        echo "================================================"
        
        # Test CSV download
        test_csv_download "$SESSION_ID"
    else
        log_warning "Skipping session-dependent tests due to processing failure"
    fi
    
    echo ""
    echo "================================================"
    
    # Test session listing
    test_list_sessions
    
    echo ""
    echo "================================================"
    
    # Test cleanup
    test_cleanup
    
    echo ""
    echo "🎉 Test script completed!"
    echo ""
    echo "📚 Next steps:"
    echo "   • Check downloads/ directory for CSV files"
    echo "   • Check result/chunks/ directory for audio chunks"
    echo "   • View API docs: $API_BASE/docs"
    echo "   • Create test audio files for processing"
    
    # Show test file suggestions
    echo ""
    echo "💡 Test file suggestions:"
    echo "   • Create: $TEST_FILE"
    echo "   • Format: WAV, 16kHz or 22kHz"
    echo "   • Duration: 30-60 seconds of Khmer speech"
    echo "   • Quality: Clear, minimal background noise"
}

# Check dependencies
check_dependencies() {
    if ! command -v curl &> /dev/null; then
        log_error "curl is required but not installed"
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log_warning "jq is not installed - JSON output will not be formatted"
        log_info "Install jq for better output formatting: apt-get install jq (Ubuntu) or brew install jq (macOS)"
    fi
}

# Handle command line arguments
if [ "$1" = "help" ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Khmer Voice Processing API Test Script"
    echo ""
    echo "Usage: $0 [test_file]"
    echo ""
    echo "Arguments:"
    echo "  test_file    Path to audio file for testing (default: $TEST_FILE)"
    echo ""
    echo "Examples:"
    echo "  $0                                    # Use default test file"
    echo "  $0 my_khmer_audio.wav                # Use custom test file"
    echo "  $0 /path/to/khmer_speech.wav         # Use file with full path"
    echo ""
    echo "Requirements:"
    echo "  • API server running on localhost:8000"
    echo "  • curl command available"
    echo "  • jq command (optional, for formatted JSON output)"
    echo "  • Test audio file in WAV format"
    exit 0
fi

# Use custom test file if provided
if [ -n "$1" ]; then
    TEST_FILE="$1"
fi

# Run tests
check_dependencies
main
