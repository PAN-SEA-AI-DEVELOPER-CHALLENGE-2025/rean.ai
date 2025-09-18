#!/bin/bash

# Pan-Sea Environment Setup Script
# This script helps create the necessary .env files for Docker

echo "🔧 Pan-Sea Environment Setup"
echo "============================"

# Function to generate a random secret key
generate_secret_key() {
    python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || \
    openssl rand -base64 32 2>/dev/null || \
    echo "$(date +%s)_$(whoami)_$(hostname)_random_secret_key"
}

# Create backend .env file
BACKEND_ENV="pan-sea-backend/.env"
if [ -f "$BACKEND_ENV" ]; then
    echo "⚠️  Backend .env file already exists at $BACKEND_ENV"
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Skipping backend .env creation"
    else
        rm "$BACKEND_ENV"
    fi
fi

if [ ! -f "$BACKEND_ENV" ]; then
    echo "📝 Creating backend .env file..."
    
    # Generate a secret key
    SECRET_KEY=$(generate_secret_key)
    
    # Copy from template and replace placeholders
    cp pan-sea-backend/env.template "$BACKEND_ENV"
    
    # Replace the secret key
    if command -v sed >/dev/null 2>&1; then
        sed -i.bak "s/your_secret_key_here_generate_a_random_string/$SECRET_KEY/" "$BACKEND_ENV"
        rm "${BACKEND_ENV}.bak" 2>/dev/null
    fi
    
    echo "✅ Created $BACKEND_ENV"
    echo ""
    echo "⚠️  IMPORTANT: Please edit $BACKEND_ENV and add your actual values for:"
    echo "   - SUPABASE_URL"
    echo "   - SUPABASE_KEY"
    echo "   - OPENAI_API_KEY"
    echo "   - DATABASE_URL (if using direct PostgreSQL)"
    echo ""
fi

# Create frontend .env file
FRONTEND_ENV="pan-sea-frontend/.env.local"
if [ ! -f "$FRONTEND_ENV" ]; then
    echo "📝 Creating frontend .env.local file..."
    
    cat > "$FRONTEND_ENV" << 'EOF'
# Frontend Environment Variables

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# External API Keys
NEXT_PUBLIC_GEMINI_API_KEY=your_gemini_api_key_here

# Development Settings
NEXT_TELEMETRY_DISABLED=1
EOF
    
    echo "✅ Created $FRONTEND_ENV"
    echo ""
    echo "⚠️  IMPORTANT: Please edit $FRONTEND_ENV and add your actual values for:"
    echo "   - NEXT_PUBLIC_GEMINI_API_KEY"
    echo ""
fi

echo "🐳 Environment files created! Next steps:"
echo "1. Edit the .env files with your actual API keys and database URLs"
echo "2. Run: docker-compose up --build"
echo ""
echo "🔧 Quick start with minimal config:"
echo "If you just want to test without external services:"
echo "1. Set DEBUG=True in backend .env"
echo "2. Comment out Supabase-related code temporarily"
echo "3. Use SQLite instead of PostgreSQL for testing"
echo ""
echo "📚 Check DOCKER-README.md for more details!"
