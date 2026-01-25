#!/bin/zsh

# Update Cursor CLI using the official installer
set -euo pipefail

echo "Updating Cursor CLI..."
curl -fsS https://cursor.com/install | bash
echo "Cursor CLI update complete."
