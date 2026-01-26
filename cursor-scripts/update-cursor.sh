#!/bin/zsh

# Update Cursor CLI using the official installer
set -euo pipefail

# Function to check for feature overlaps
check_feature_overlaps() {
    SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
    REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    CURSOR_SCRIPTS="$REPO_ROOT/cursor-scripts"
    
    if [ ! -d "$CURSOR_SCRIPTS" ]; then
        return 0  # No cursor-scripts to check
    fi
    
    # Get CLI help/commands
    CLI_HELP=$(agent --help 2>/dev/null || cursor-agent --help 2>/dev/null || echo "")
    CLI_ABOUT=$(agent about 2>/dev/null || cursor-agent about 2>/dev/null || echo "")
    
    # Map our scripts to potential CLI features
    declare -A SCRIPT_FEATURES=(
        ["cursor_usage.py"]="usage|quota|budget|tracking"
        ["export-chat.sh"]="export|chat|conversation"
        ["web_search.py"]="search|web|internet"
        ["search_script.py"]="search|web|internet"
    )
    
    OVERLAPS_FOUND=0
    
    for script in "${!SCRIPT_FEATURES[@]}"; do
        if [ ! -f "$CURSOR_SCRIPTS/$script" ]; then
            continue
        fi
        
        features="${SCRIPT_FEATURES[$script]}"
        script_name=$(basename "$script")
        
        # Check if CLI help mentions similar features
        if echo "$CLI_HELP" | grep -qiE "$features" || echo "$CLI_ABOUT" | grep -qiE "$features"; then
            echo ""
            echo "⚠️  Potential overlap detected:"
            echo "   Script: $script_name"
            echo "   Features: $features"
            echo "   CLI may have built-in functionality for this"
            
            OVERLAPS_FOUND=1
            
            # Suggest testing
            echo ""
            echo "   Recommendation: Test both implementations:"
            echo "   1. Test cursor-script: Check $CURSOR_SCRIPTS/$script"
            echo "   2. Test CLI built-in: Check 'agent --help' for similar commands"
            echo "   3. Compare results and choose the better option"
        fi
    done
    
    if [ $OVERLAPS_FOUND -eq 0 ]; then
        echo "   ✅ No obvious feature overlaps detected"
    else
        echo ""
        echo "📝 Note: Keep cursor-scripts if they provide:"
        echo "   - More features than CLI built-in"
        echo "   - Better customization"
        echo "   - Repo-specific functionality"
        echo ""
        echo "   Consider removing cursor-scripts if CLI built-in:"
        echo "   - Has all needed features"
        echo "   - Is more reliable/maintained"
        echo "   - Reduces maintenance burden"
    fi
}

# Check current installed version
INSTALLED_VERSION=$(agent --version 2>/dev/null || cursor-agent --version 2>/dev/null || echo "")

# Get latest version from installer script (source of truth)
LATEST_VERSION=$(curl -fsS https://cursor.com/install | grep -oE "2026\.[0-9]{2}\.[0-9]{2}-[a-f0-9]+" | head -1)

if [ -z "$INSTALLED_VERSION" ]; then
    echo "⚠️  Cursor CLI not found. Installing..."
elif [ "$INSTALLED_VERSION" = "$LATEST_VERSION" ]; then
    echo "✅ Cursor CLI is up to date (version: $INSTALLED_VERSION)"
    exit 0
else
    echo "📦 Updating Cursor CLI..."
    echo "   Current: $INSTALLED_VERSION"
    echo "   Latest:  $LATEST_VERSION"
    
    # Check if CLI is currently running
    if pgrep -f "cursor-agent|agent.*--resume" > /dev/null; then
        echo ""
        echo "⚠️  WARNING: Cursor CLI is currently running."
        echo "   It's recommended to exit the CLI session before updating."
        echo "   Type 'exit' or press Ctrl+C to cancel, then run this script again."
        echo ""
        read -t 5 -p "Continue anyway? (y/N) " -n 1 -r || REPLY="n"
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Update cancelled."
            exit 1
        fi
    fi
fi

echo "Installing latest version..."
curl -fsS https://cursor.com/install | bash

# Verify new version
NEW_VERSION=$(agent --version 2>/dev/null || cursor-agent --version 2>/dev/null || echo "")
if [ -n "$NEW_VERSION" ]; then
    echo "✅ Cursor CLI updated to version: $NEW_VERSION"
    
    # Check for feature overlaps with cursor-scripts
    if [ -n "$INSTALLED_VERSION" ] && [ "$INSTALLED_VERSION" != "$NEW_VERSION" ]; then
        echo ""
        echo "🔍 Checking for feature overlaps with cursor-scripts..."
        check_feature_overlaps
    fi
else
    echo "⚠️  Update completed, but could not verify version"
fi
