#!/bin/bash

echo "🔐 Removing secrets from git history..."

# List of files containing secrets
FILES=(
    "tools/geoai/config.py"
    "tools/geoai/coord-extractor.py"
    "tools/geoai/dataguard.py"
    "tools/geoai/gitgeo.py"
    "tools/geoai/mapdebug-assistant.py"
    "src/backend/services/code_improvement_service.py"
    "tools/analysis/analyze_with_code_models.py"
    "tools/analysis/analyze_with_hf_models.py"
    "tools/validation/query_hf_with_headers.py"
    "tools/validation/test_hf_diagnostic.py"
)

echo "📝 Creating .env.example file..."
cat > .env.example << 'EOF'
# Hugging Face API Token
# Get yours at: https://huggingface.co/settings/tokens
HF_TOKEN=your_hugging_face_token_here

# Other environment variables
# Add more as needed
EOF

echo "🧹 Removing hardcoded tokens from current files..."
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  Cleaning: $file"
        # Replace hardcoded HF tokens with environment variable
        sed -i 's/hf_[a-zA-Z0-9]\{32\}/os.getenv("HF_TOKEN")/g' "$file"
    fi
done

echo "💡 Next steps:"
echo "1. Review the changes: git diff"
echo "2. Commit the fixes: git add -A && git commit -m 'fix: remove hardcoded secrets, use environment variables'"
echo "3. Remove secrets from history: git filter-branch --force --index-filter 'git rm --cached --ignore-unmatch ${FILES[*]}' --prune-empty --tag-name-filter cat -- --all"
echo "4. Force push: git push --force origin main"
echo ""
echo "⚠️  WARNING: This will rewrite git history. Make sure no one else is using the repo yet!"