#!/bin/zsh
#
# Sync template repository from source-of-truth starter kit
#
# Usage:
#   Run from the template repository directory:
#   ./sync-from-source.sh [--dry-run]
#
# This script copies all files from the source-of-truth to the
# current directory (template repo), excluding git files and .env
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Source of truth location
SOURCE_OF_TRUTH="/Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit"

# Current directory (template repo - where script is run from)
TEMPLATE_REPO="$(pwd)"

# Parse arguments
DRY_RUN=false
if [[ "${1:-}" == "--dry-run" ]]; then
    DRY_RUN=true
fi

# Check if source of truth exists
if [ ! -d "$SOURCE_OF_TRUTH" ]; then
    echo "${RED}❌ Source of truth not found: $SOURCE_OF_TRUTH${NC}"
    echo ""
    echo "Please update SOURCE_OF_TRUTH in this script if the path has changed."
    exit 1
fi

echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "${BLUE}  Sync Template from Source of Truth${NC}"
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "${CYAN}Source:${NC} $SOURCE_OF_TRUTH"
echo "${CYAN}Target:${NC} $TEMPLATE_REPO"
if [ "$DRY_RUN" = true ]; then
    echo "${YELLOW}Mode:${NC} DRY RUN (no changes will be made)"
fi
echo ""

# Confirm if not dry run
if [ "$DRY_RUN" = false ]; then
    echo "${YELLOW}⚠️  This will overwrite files in the template repository.${NC}"
    echo ""
    read -q "REPLY?Continue? (y/N): "
    echo ""
    if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
        echo "${BLUE}Cancelled.${NC}"
        exit 0
    fi
fi

# Files/directories to exclude
EXCLUDE=(
    ".git"
    ".DS_Store"
    "__pycache__"
    "*.pyc"
    ".env"
    "sync-check.sh"
    "sync-from-source.sh"
)

# Build rsync exclude arguments
RSYNC_EXCLUDE=""
for item in "${EXCLUDE[@]}"; do
    RSYNC_EXCLUDE="$RSYNC_EXCLUDE --exclude='$item'"
done

# Sync files
echo "${BLUE}Syncing files...${NC}"

if [ "$DRY_RUN" = true ]; then
    # Show what would be synced
    rsync -avn --delete \
        --exclude='.git' \
        --exclude='.DS_Store' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='sync-check.sh' \
        --exclude='sync-from-source.sh' \
        "$SOURCE_OF_TRUTH/" "$TEMPLATE_REPO/"
else
    # Actually sync
    rsync -av --delete \
        --exclude='.git' \
        --exclude='.DS_Store' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.env' \
        --exclude='sync-check.sh' \
        --exclude='sync-from-source.sh' \
        "$SOURCE_OF_TRUTH/" "$TEMPLATE_REPO/"
    
    echo ""
    echo "${GREEN}✅ Sync complete!${NC}"
    echo ""
    echo "${BLUE}Next steps:${NC}"
    echo "1. Review changes: git status"
    echo "2. Test the template: ./tests/run_all.py"
    echo "3. Commit if ready: git add -A && git commit -m 'sync: Update from source of truth'"
    echo ""
fi
