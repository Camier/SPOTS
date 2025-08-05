#!/bin/bash
# Backup all SPOTS databases before refactoring

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "🔐 Backing up all databases to $BACKUP_DIR"

# Find all .db files
for db in $(find data -name "*.db" -type f); do
    echo "Backing up: $db"
    cp "$db" "$BACKUP_DIR/$(basename $db)"
done

# Also backup the quarantined JSON files
echo "Backing up quarantined data..."
cp -r data/quarantine "$BACKUP_DIR/"

# Create manifest
cat > "$BACKUP_DIR/manifest.txt" << EOF
SPOTS Database Backup
Date: $(date)
Refactoring Phase: Pre-Phase-1
Files backed up:
$(ls -la "$BACKUP_DIR")
EOF

echo "✅ Backup complete!"
echo "📁 Location: $BACKUP_DIR"
echo ""
echo "To restore:"
echo "  cp $BACKUP_DIR/*.db data/"