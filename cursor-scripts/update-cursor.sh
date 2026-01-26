#!/bin/zsh

# Update Cursor CLI using the official installer
set -euo pipefail

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
fi

echo "Installing latest version..."
curl -fsS https://cursor.com/install | bash

# Verify new version
NEW_VERSION=$(agent --version 2>/dev/null || cursor-agent --version 2>/dev/null || echo "")
if [ -n "$NEW_VERSION" ]; then
    echo "✅ Cursor CLI updated to version: $NEW_VERSION"
else
    echo "⚠️  Update completed, but could not verify version"
fi
