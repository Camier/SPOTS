#!/bin/bash
# Safe workspace cleanup script for SPOTS project
# Created: 2025-08-04

echo "🧹 Starting workspace cleanup..."

# Create archive directory for backups
mkdir -p data/archive

# Function to clean Python cache
clean_python_cache() {
    echo "🐍 Cleaning Python cache files..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    find . -name "*.pyo" -delete 2>/dev/null
    echo "✅ Python cache cleaned"
}

# Function to handle database backups
handle_db_backups() {
    echo "💾 Handling database backups..."
    
    # Move old backups to archive (keeping newest)
    for backup in data/occitanie_spots_backup_before_{cleaning,immediate_enrichment,nominatim,practical_enrichment}.db; do
        if [ -f "$backup" ]; then
            mv "$backup" data/archive/
            echo "  Archived: $(basename $backup)"
        fi
    done
    
    echo "✅ Database backups archived"
}

# Function to clean empty directories
clean_empty_dirs() {
    echo "📁 Removing empty directories..."
    
    # Remove known empty dirs
    rmdir logs 2>/dev/null && echo "  Removed: logs/"
    rmdir sessions 2>/dev/null && echo "  Removed: sessions/"
    rmdir tests/backend/test_basic 2>/dev/null && echo "  Removed: tests/backend/test_basic/"
    
    echo "✅ Empty directories cleaned"
}

# Function to update gitignore
update_gitignore() {
    echo "📝 Updating .gitignore..."
    
    # Check if patterns already exist
    if ! grep -q "*.backup" .gitignore; then
        echo -e "\n# Backup files\n*.backup\n*_backup_*" >> .gitignore
    fi
    
    if ! grep -q "sessions/" .gitignore; then
        echo -e "\n# Empty directories\nlogs/\nsessions/" >> .gitignore
    fi
    
    echo "✅ .gitignore updated"
}

# Main cleanup process
echo "==================================="
echo "SPOTS Workspace Cleanup"
echo "==================================="

# Ask for confirmation
read -p "🤔 Proceed with cleanup? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled"
    exit 1
fi

# Execute cleanup
clean_python_cache
handle_db_backups
clean_empty_dirs
update_gitignore

# Summary
echo ""
echo "==================================="
echo "📊 Cleanup Summary"
echo "==================================="
echo "✅ Python cache files removed"
echo "✅ Old database backups archived to data/archive/"
echo "✅ Empty directories removed"
echo "✅ .gitignore updated"
echo ""
echo "💡 Next steps:"
echo "  1. Review archived files in data/archive/"
echo "  2. Commit your changes: git add -A && git commit -m 'Workspace cleanup'"
echo "  3. Remove archived files if no longer needed: rm -rf data/archive"
echo ""
echo "🎉 Cleanup complete!"