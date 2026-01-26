#!/bin/zsh
#
# Cursor Starter Kit Installer
#
# Adds the Cursor Starter Kit to a repository that doesn't have it.
#
# Usage:
#   ./install.sh [target-repo-path]
#
# If no path provided, installs to current directory.
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory (starter kit location)
STARTER_KIT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Target repository (default: current directory)
TARGET_REPO="${1:-$(pwd)}"
TARGET_REPO="$(cd "$TARGET_REPO" && pwd)"

echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "${BLUE}  Cursor Starter Kit Installer${NC}"
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Starter Kit: $STARTER_KIT_DIR"
echo "Target Repo: $TARGET_REPO"
echo ""

# Check if starter kit is already installed
STARTER_KIT_MARKERS=(
    ".cursorrules"
    "cursor-scripts/cursor_usage.py"
    "cursor-scripts/export-chat.sh"
)

ALREADY_INSTALLED=false
for marker in "${STARTER_KIT_MARKERS[@]}"; do
    if [ -e "$TARGET_REPO/$marker" ]; then
        # Check if it looks like our starter kit (not just any .cursorrules)
        if [ "$marker" = ".cursorrules" ]; then
            if grep -q "Session Continuity" "$TARGET_REPO/$marker" 2>/dev/null; then
                ALREADY_INSTALLED=true
                break
            fi
        else
            ALREADY_INSTALLED=true
            break
        fi
    fi
done

if [ "$ALREADY_INSTALLED" = true ]; then
    echo "${YELLOW}⚠️  Cursor Starter Kit appears to already be installed${NC}"
    echo ""
    echo "Found starter kit files in: $TARGET_REPO"
    echo ""
    echo "Options:"
    echo "  1) Reinstall anyway (will handle existing files)"
    echo "  2) Cancel"
    echo ""
    read -p "Choose option (1-2): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            echo "Proceeding with reinstallation..."
            ;;
        2|*)
            echo "Installation cancelled."
            exit 0
            ;;
    esac
fi

# Check if target is a git repo
if [ ! -d "$TARGET_REPO/.git" ]; then
    echo "${YELLOW}⚠️  Warning: Target directory doesn't appear to be a git repository${NC}"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Installation cancelled."
        exit 1
    fi
fi

# Files to copy (excluding install.sh and git files)
FILES_TO_COPY=(
    ".cursorrules"
    ".cursorignore"
    ".gitignore"
    ".env.example"
    "README.md"
    "cursor-scripts/"
    "cursor-chats/"
    "cursor-usage/"
    "cursor-web-search/"
    "mcp-bypass-skeleton/"
    "tests/"
)

# Check for existing files
EXISTING_FILES=()
for item in "${FILES_TO_COPY[@]}"; do
    if [ -e "$TARGET_REPO/$item" ]; then
        EXISTING_FILES+=("$item")
    fi
done

if [ ${#EXISTING_FILES[@]} -gt 0 ]; then
    echo "${YELLOW}⚠️  The following files/directories already exist:${NC}"
    for file in "${EXISTING_FILES[@]}"; do
        echo "   - $file"
    done
    echo ""
    echo "Options:"
    echo "  1) Skip existing files (recommended)"
    echo "  2) Backup and overwrite"
    echo "  3) Cancel"
    echo ""
    read -p "Choose option (1-3): " -n 1 -r
    echo
    
    case $REPLY in
        1)
            SKIP_EXISTING=true
            ;;
        2)
            SKIP_EXISTING=false
            BACKUP_DIR="$TARGET_REPO/.cursor-starter-kit-backup-$(date +%Y%m%d-%H%M%S)"
            echo "Creating backup in: $BACKUP_DIR"
            mkdir -p "$BACKUP_DIR"
            for file in "${EXISTING_FILES[@]}"; do
                if [ -e "$TARGET_REPO/$file" ]; then
                    cp -r "$TARGET_REPO/$file" "$BACKUP_DIR/" 2>/dev/null || true
                fi
            done
            echo "${GREEN}✅ Backup created${NC}"
            ;;
        3)
            echo "Installation cancelled."
            exit 1
            ;;
        *)
            echo "Invalid option. Installation cancelled."
            exit 1
            ;;
    esac
else
    SKIP_EXISTING=false
fi

echo ""
echo "${BLUE}Installing files...${NC}"

# Copy files
COPIED=0
SKIPPED=0

for item in "${FILES_TO_COPY[@]}"; do
    source="$STARTER_KIT_DIR/$item"
    target="$TARGET_REPO/$item"
    
    if [ "$SKIP_EXISTING" = true ] && [ -e "$target" ]; then
        echo "   ⏭️  Skipping existing: $item"
        ((SKIPPED++))
        continue
    fi
    
    if [ -d "$source" ]; then
        # Copy directory
        mkdir -p "$(dirname "$target")"
        cp -r "$source" "$target" 2>/dev/null || {
            echo "   ${RED}❌ Failed to copy: $item${NC}"
            continue
        }
        echo "   ${GREEN}✅ Copied directory: $item${NC}"
    elif [ -f "$source" ]; then
        # Copy file
        mkdir -p "$(dirname "$target")"
        cp "$source" "$target" 2>/dev/null || {
            echo "   ${RED}❌ Failed to copy: $item${NC}"
            continue
        }
        echo "   ${GREEN}✅ Copied file: $item${NC}"
    else
        echo "   ${YELLOW}⚠️  Source not found: $item${NC}"
        continue
    fi
    
    ((COPIED++))
done

# Make scripts executable
echo ""
echo "${BLUE}Making scripts executable...${NC}"
if [ -d "$TARGET_REPO/cursor-scripts" ]; then
    find "$TARGET_REPO/cursor-scripts" -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
    echo "   ${GREEN}✅ Made shell scripts executable${NC}"
fi

if [ -d "$TARGET_REPO/tests" ]; then
    find "$TARGET_REPO/tests" -type f -name "*.py" -exec chmod +x {} \; 2>/dev/null || true
    echo "   ${GREEN}✅ Made test scripts executable${NC}"
fi

# Create .env from .env.example if .env doesn't exist
if [ -f "$TARGET_REPO/.env.example" ] && [ ! -f "$TARGET_REPO/.env" ]; then
    echo ""
    echo "${BLUE}Creating .env from .env.example...${NC}"
    cp "$TARGET_REPO/.env.example" "$TARGET_REPO/.env"
    echo "   ${GREEN}✅ Created .env${NC}"
    echo "   ${YELLOW}⚠️  Remember to add your API keys to .env${NC}"
fi

# Summary
echo ""
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo "${GREEN}✅ Installation Complete!${NC}"
echo "${BLUE}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Files copied: $COPIED"
if [ $SKIPPED -gt 0 ]; then
    echo "Files skipped: $SKIPPED"
fi
echo ""

# Next steps
echo "${BLUE}Next Steps:${NC}"
echo ""
echo "1. ${YELLOW}Add API keys${NC}:"
echo "   Edit $TARGET_REPO/.env and add your API keys"
echo ""
echo "2. ${YELLOW}Run tests${NC}:"
echo "   cd $TARGET_REPO"
echo "   python tests/run_all.py"
echo ""
echo "3. ${YELLOW}Customize${NC}:"
echo "   - Edit .cursorrules for project-specific protocols"
echo "   - Update .cursorignore for your file patterns"
echo ""
echo "4. ${YELLOW}Review${NC}:"
echo "   - Check README.md for usage instructions"
echo "   - Review cursor-scripts/ for available tools"
echo ""

if [ -n "${BACKUP_DIR:-}" ]; then
    echo "${YELLOW}Backup location: $BACKUP_DIR${NC}"
    echo ""
fi

echo "${GREEN}Happy coding! 🚀${NC}"
