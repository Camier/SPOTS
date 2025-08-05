#!/bin/bash

echo "🔐 Fixing secrets in repository..."

# Create .env.example
echo "📝 Creating .env.example..."
cat > .env.example << 'EOF'
# Hugging Face API Token
# Get yours at: https://huggingface.co/settings/tokens
HF_TOKEN=your_hugging_face_token_here

# IGN/Geoplatform API Keys
IGN_API_KEY=your_ign_api_key_here

# Other environment variables
# Add more as needed
EOF

# Add .env to .gitignore if not already there
if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo "📝 Adding .env to .gitignore..."
    echo -e "\n# Environment variables\n.env" >> .gitignore
fi

echo "🧹 Removing all HF tokens from code..."

# Find and replace all hardcoded HF tokens
find . -name "*.py" -type f ! -path "./venv/*" ! -path "./.git/*" -exec grep -l "hf_[a-zA-Z0-9]\{32\}" {} \; | while read file; do
    echo "  Cleaning: $file"
    # Replace the hardcoded token with environment variable usage
    sed -i 's/"hf_[a-zA-Z0-9]\{32\}"/os.getenv("HF_TOKEN")/g' "$file"
    sed -i "s/'hf_[a-zA-Z0-9]\{32\}'/os.getenv('HF_TOKEN')/g" "$file"
done

echo "✅ Secrets removed from code!"
echo ""
echo "📋 Next steps:"
echo "1. Review changes: git status && git diff"
echo "2. Reset to before the commit: git reset --soft HEAD~1"
echo "3. Stage all files again: git add -A"
echo "4. Commit without secrets: git commit -m 'feat: initial commit - Map validation framework with advanced features'"
echo "5. Push to GitHub: git push -f origin main"
echo ""
echo "This approach is cleaner since we only have one commit!"