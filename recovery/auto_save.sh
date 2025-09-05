#!/bin/bash
# Auto-save important files every 30 seconds

RECOVERY_DIR="recovery"
PROJECT_ROOT="/home/kevin/Projects/tumor-detection-segmentation"

while true; do
    timestamp=$(date '+%Y%m%d_%H%M%S')
    backup_dir="$RECOVERY_DIR/auto_backup_$timestamp"
    
    # Create backup directory
    mkdir -p "$backup_dir"
    
    # Copy important files
    find "$PROJECT_ROOT" -name "*.py" -path "*/src/*" -exec cp --parents {} "$backup_dir" \;
    find "$PROJECT_ROOT" -name "*.json" -path "*/config/*" -exec cp --parents {} "$backup_dir" \;
    find "$PROJECT_ROOT" -name "*.ipynb" -path "*/notebooks/*" -exec cp --parents {} "$backup_dir" \;
    
    # Copy VSCode settings
    if [ -d "$PROJECT_ROOT/.vscode" ]; then
        cp -r "$PROJECT_ROOT/.vscode" "$backup_dir/"
    fi
    
    # Keep only last 10 backups
    ls -dt "$RECOVERY_DIR"/auto_backup_* | tail -n +11 | xargs rm -rf
    
    sleep 30
done
