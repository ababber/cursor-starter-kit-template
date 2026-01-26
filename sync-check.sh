#!/bin/zsh
#
# Compare template repository with source-of-truth starter kit
#
# Usage:
#   Run from the template repository directory:
#   ./sync-check.sh
#
# This script compares the current directory (template repo) with
# the source-of-truth starter kit in the main repository.
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

# Check if source of truth exists
if [ ! -d "$SOURCE_OF_TRUTH" ]; then
    echo "${RED}❌ Source of truth not found: $SOURCE_OF_TRUTH${NC}"
    echo ""
    echo "Please update SOURCE_OF_TRUTH in this script if the path has changed."
    exit 1
fi

# Files/directories to exclude from comparison
EXCLUDE_PATTERNS=(
    ".git"
    ".DS_Store"
    "__pycache__"
    "*.pyc"
    ".env"
    "sync-check.sh"  # Don't compare this script itself
)

# Build find exclude arguments
FIND_EXCLUDE=""
for pattern in "${EXCLUDE_PATTERNS[@]}"; do
    FIND_EXCLUDE="$FIND_EXCLUDE -not -name '$pattern'"
done

echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "${BLUE}  Starter Kit Sync Check${NC}"
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "${CYAN}Source of Truth:${NC} $SOURCE_OF_TRUTH"
echo "${CYAN}Template Repo:${NC}  $TEMPLATE_REPO"
echo ""

# Function to get relative file list
get_file_list() {
    local base_dir="$1"
    cd "$base_dir"
    find . -type f \
        -not -path '*/.git/*' \
        -not -name '.DS_Store' \
        -not -name '*.pyc' \
        -not -path '*/__pycache__/*' \
        -not -name '.env' \
        -not -name 'sync-check.sh' \
        | sort
}

# Get file lists
echo "${BLUE}Scanning files...${NC}"
SOURCE_FILES=$(get_file_list "$SOURCE_OF_TRUTH")
TEMPLATE_FILES=$(get_file_list "$TEMPLATE_REPO")

# Find differences
MISSING_IN_TEMPLATE=$(comm -23 <(echo "$SOURCE_FILES") <(echo "$TEMPLATE_FILES"))
EXTRA_IN_TEMPLATE=$(comm -13 <(echo "$SOURCE_FILES") <(echo "$TEMPLATE_FILES"))
COMMON_FILES=$(comm -12 <(echo "$SOURCE_FILES") <(echo "$TEMPLATE_FILES"))

# Count differences
MISSING_COUNT=$(echo "$MISSING_IN_TEMPLATE" | grep -c . 2>/dev/null || true)
MISSING_COUNT=${MISSING_COUNT:-0}
EXTRA_COUNT=$(echo "$EXTRA_IN_TEMPLATE" | grep -c . 2>/dev/null || true)
EXTRA_COUNT=${EXTRA_COUNT:-0}
DIFF_COUNT=0

# Check for content differences in common files
echo "${BLUE}Checking file contents...${NC}"
DIFFERENT_FILES=""
for file in $COMMON_FILES; do
    if [ -f "$SOURCE_OF_TRUTH/$file" ] && [ -f "$TEMPLATE_REPO/$file" ]; then
        if ! diff -q "$SOURCE_OF_TRUTH/$file" "$TEMPLATE_REPO/$file" > /dev/null 2>&1; then
            DIFFERENT_FILES="$DIFFERENT_FILES$file\n"
            DIFF_COUNT=$((DIFF_COUNT + 1))
        fi
    fi
done

# Summary
echo ""
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "${BLUE}  Summary${NC}"
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""

TOTAL_ISSUES=$((MISSING_COUNT + EXTRA_COUNT + DIFF_COUNT))

if [ "$TOTAL_ISSUES" -eq 0 ]; then
    echo "${GREEN}✅ Template repository is in sync!${NC}"
    echo ""
    exit 0
fi

# Missing files
if [ "$MISSING_COUNT" -gt 0 ]; then
    echo "${RED}❌ Missing in template ($MISSING_COUNT files):${NC}"
    echo "$MISSING_IN_TEMPLATE" | sed 's/^/  - /'
    echo ""
fi

# Extra files
if [ "$EXTRA_COUNT" -gt 0 ]; then
    echo "${YELLOW}⚠️  Extra in template ($EXTRA_COUNT files):${NC}"
    echo "$EXTRA_IN_TEMPLATE" | sed 's/^/  + /'
    echo ""
fi

# Different files
if [ "$DIFF_COUNT" -gt 0 ]; then
    echo "${YELLOW}⚠️  Content differences ($DIFF_COUNT files):${NC}"
    echo -e "$DIFFERENT_FILES" | sed 's/^/  ~ /'
    echo ""
fi

# Detailed diff for different files
if [ "$DIFF_COUNT" -gt 0 ] && [ "$DIFF_COUNT" -le 5 ]; then
    echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo "${BLUE}  Detailed Differences${NC}"
    echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    for file in $(echo -e "$DIFFERENT_FILES"); do
        echo "${CYAN}File: $file${NC}"
        diff -u "$TEMPLATE_REPO/$file" "$SOURCE_OF_TRUTH/$file" || true
        echo ""
    done
fi

# Sync instructions
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "${BLUE}  To Sync${NC}"
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Run from the template repository:"
echo ""
echo "  # Copy all files from source of truth"
echo "  cp -r $SOURCE_OF_TRUTH/* ."
echo "  cp -r $SOURCE_OF_TRUTH/.* . 2>/dev/null || true"
echo ""
echo "  # Remove this sync script (it's not part of starter kit)"
echo "  rm -f sync-check.sh"
echo ""
echo "  # Review changes"
echo "  git status"
echo ""
echo "  # Commit if ready"
echo "  git add -A"
echo "  git commit -m 'sync: Update from source of truth'"
echo ""

exit 1
