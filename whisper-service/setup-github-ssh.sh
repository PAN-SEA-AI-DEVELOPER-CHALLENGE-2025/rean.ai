#!/bin/bash

# GitHub SSH Setup Script for EC2
# This script configures SSH access to GitHub from your EC2 instance

echo "🔑 Setting up GitHub SSH access on EC2..."

# Step 1: Generate SSH key pair
echo "📧 Enter your GitHub email address:"
read -p "Email: " github_email

if [ -z "$github_email" ]; then
    echo "❌ Email is required!"
    exit 1
fi

echo "🔐 Generating SSH key pair..."

# Check if key already exists
if [ -f ~/.ssh/id_ed25519 ]; then
    echo "⚠️  SSH key already exists!"
    read -p "Overwrite existing key? (y/n): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Using existing key..."
        ssh-add ~/.ssh/id_ed25519 2>/dev/null || true
    else
        ssh-keygen -t ed25519 -C "$github_email" -f ~/.ssh/id_ed25519 -N ""
    fi
else
    ssh-keygen -t ed25519 -C "$github_email" -f ~/.ssh/id_ed25519 -N ""
fi

# Step 2: Start SSH agent and add key
echo "🚀 Starting SSH agent and adding key..."
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Step 3: Create SSH config for GitHub
echo "📝 Creating SSH config..."
mkdir -p ~/.ssh
cat > ~/.ssh/config << EOF
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentitiesOnly yes
EOF

# Set proper permissions
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# Step 4: Display public key
echo ""
echo "🔑 Your PUBLIC key (copy this to GitHub):"
echo "=============================================="
cat ~/.ssh/id_ed25519.pub
echo "=============================================="
echo ""

# Step 5: Instructions
echo "📋 Next steps:"
echo "1. Copy the public key above"
echo "2. Go to GitHub.com → Settings → SSH and GPG keys"
echo "3. Click 'New SSH key'"
echo "4. Paste the key and give it a title (e.g., 'EC2-Production')"
echo "5. Click 'Add SSH key'"
echo ""
echo "6. Test the connection by running:"
echo "   ssh -T git@github.com"
echo ""
echo "7. Clone your repository:"
echo "   git clone git@github.com:yourusername/whisper-service.git"
echo "   # Replace 'yourusername' with your actual GitHub username"

# Step 6: Test function
test_github_connection() {
    echo "🧪 Testing GitHub SSH connection..."
    ssh -T git@github.com
}

echo ""
read -p "Do you want to test the connection now? (y/n): " test_now
if [[ $test_now =~ ^[Yy]$ ]]; then
    echo "Note: You need to add the public key to GitHub first!"
    test_github_connection
fi

echo "✅ SSH setup complete!"
