# Template System Maintenance Guide

## Overview

The Cursor Starter Kit uses a **source-of-truth** model where:
- **Source of Truth**: `cursor-starter-kit/` in the main `quant` repository
- **Template Repository**: Separate GitHub repository used as a template for new repos
- **Sync Scripts**: Tools to keep the template repo in sync with source of truth

## Repository Structure

### Source of Truth
**Location**: `/Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/`

This is the **master copy** where all changes are made. Contains:
- All starter kit files (`.cursorrules`, scripts, tests, etc.)
- `install.sh` - Installation script
- `cursorkit.zsh` - Shell helper function
- `sync-check.sh` - Compare template with source (maintenance tool)
- `sync-from-source.sh` - Sync template from source (maintenance tool)
- `create-repo-with-kit.sh` - CLI automation script

### Template Repository
**Location**: Separate GitHub repository (e.g., `cursor-starter-kit-template`)

This is the **published template** that users clone via GitHub's "Use this template" feature. Contains:
- All starter kit files (synced from source of truth)
- **Excludes**: `install.sh` (optional - depends on template design)
- **Excludes**: Sync scripts (maintenance tools, not part of starter kit)

### Dependencies

| Component | Purpose | Location | Managed By |
|-----------|---------|----------|------------|
| **Source of Truth** | Master copy of starter kit | `quant/cursor-starter-kit/` | This repo |
| **Template Repo** | GitHub template for new repos | Separate GitHub repo | Manual sync |
| **cursorkit.zsh** | Shell helper function | `cursor-starter-kit/cursorkit.zsh` | Source of truth |
| **install.sh** | Installation script | `cursor-starter-kit/install.sh` | Source of truth |
| **sync-template.sh** | Sync template from source (auto-commit) | `cursor-starter-kit/sync-template.sh` | Source of truth |
| **sync-check.sh** | Compare template vs source | `cursor-starter-kit/sync-check.sh` | Source of truth (legacy) |
| **sync-from-source.sh** | Sync template from source | `cursor-starter-kit/sync-from-source.sh` | Source of truth (legacy) |

## Scripts and Their Purposes

### 1. `install.sh`
**Purpose**: Install starter kit into an existing repository

**Usage**:
```bash
./install.sh /path/to/repo
# Or with environment variables:
INSTALL_SKIP_EXISTING=1 ./install.sh /path/to/repo
```

**Features**:
- Copies all starter kit files
- Handles existing files (skip/backup/overwrite)
- Makes scripts executable
- Creates `.env` from `.env.example`
- Non-interactive mode via env vars

**Managed in**: Source of truth only (may or may not be in template repo)

### 2. `cursorkit.zsh`
**Purpose**: Shell helper function to run `install.sh` from anywhere

**Usage**:
```bash
# Source it (via OMZ or .zshrc)
source "/path/to/cursor-starter-kit/cursorkit.zsh"

# Then use it:
cursorkit --target /path/to/repo --skip-existing
```

**Features**:
- Self-locating installer path (no hardcoded paths)
- Safe error handling (won't crash terminal)
- Supports all `install.sh` environment variables

**Managed in**: Source of truth (should be in template repo)

### 3. `sync-check.sh`
**Purpose**: Compare template repository with source of truth

**Usage**:
```bash
cd /path/to/template-repo
./sync-check.sh
```

**Features**:
- Shows missing files in template
- Shows extra files in template
- Shows content differences
- Provides detailed diffs (up to 5 files)

**Managed in**: Source of truth (copy to template repo for maintenance)

**Note**: This script is **not part of the starter kit** - it's a maintenance tool.

### 4. `sync-template.sh` ⭐ **Recommended**
**Purpose**: Sync template repository from source of truth (runs from source)

**Usage**:
```bash
cd /Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit
./sync-template.sh --dry-run  # Preview
./sync-template.sh            # Sync, commit, and push
./sync-template.sh --no-commit # Sync without committing
```

**Features**:
- Runs from source of truth (no need to navigate to template repo)
- Dry-run mode for preview
- Auto-commits and pushes (optional `--no-commit` flag)
- Excludes git files, `.env`, maintenance scripts
- Uses rsync for efficient syncing

**Managed in**: Source of truth only

**Note**: This script is **not part of the starter kit** - it's a maintenance tool.

### 5. `sync-from-source.sh` (Legacy)
**Purpose**: Sync template repository from source of truth (runs from template)

**Usage**:
```bash
cd /path/to/template-repo
./sync-from-source.sh --dry-run  # Preview
./sync-from-source.sh            # Actually sync
```

**Note**: Use `sync-template.sh` instead - it's simpler and runs from source of truth.

### 6. `create-repo-with-kit.sh`
**Purpose**: Automate GitHub repo creation + starter kit installation

**Usage**:
```bash
./create-repo-with-kit.sh my-project --private --clone
```

**Features**:
- Creates GitHub repo via `gh repo create`
- Clones locally
- Runs `install.sh` to add starter kit
- Commits and pushes

**Managed in**: Source of truth (optional - may or may not be in template repo)

## Maintenance Workflow

### When to Update Template Repository

Update the template repo when you:
- Add new files to starter kit
- Modify existing starter kit files
- Update `cursorkit.zsh` or `install.sh`
- Fix bugs or improve functionality

**Do NOT update template repo for**:
- Changes to sync scripts (they're maintenance tools)
- Changes to this maintenance guide
- Local testing/development

### Sync Process

#### Automatic Sync (Recommended) ⭐

**A git hook automatically syncs the template repo whenever you commit changes to `cursor-starter-kit/`.**

Just commit as normal:
```bash
cd /Users/ankit/Playground/_quantRepos/quant
# Make changes to cursor-starter-kit/
git add cursor-starter-kit/
git commit -m "update: Add new feature to starter kit"
git push
```

The post-commit hook will automatically:
- Detect changes to `cursor-starter-kit/`
- Run `sync-template.sh --yes`
- Sync, commit, and push to template repo

**To disable auto-sync temporarily:**
```bash
# Rename the hook
mv .git/hooks/post-commit .git/hooks/post-commit.disabled

# Re-enable later
mv .git/hooks/post-commit.disabled .git/hooks/post-commit
```

#### Manual Sync (if needed)

If you want to sync manually or preview changes:

```bash
cd /Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit

# Preview changes first
./sync-template.sh --dry-run

# Actually sync (auto-commits and pushes)
./sync-template.sh --yes

# Or sync without auto-commit (to review first)
./sync-template.sh --yes --no-commit
```

**Note:** `cursorkit.zsh` is synced but you'll need to manually update it in your OMZ config if needed.

### Initial Template Setup

If setting up the template repo for the first time:

```bash
# 1. Create template repo (via GitHub CLI or web)
gh repo create cursor-starter-kit-template --public --clone
cd cursor-starter-kit-template

# 2. Copy starter kit files
cp -r /Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/* .
cp -r /Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/.* . 2>/dev/null || true

# 3. Copy sync scripts (for maintenance)
cp /Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/sync-check.sh .
cp /Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/sync-from-source.sh .
chmod +x sync-*.sh

# 4. Optional: Remove install.sh if template should be final state
# rm install.sh

# 5. Commit and push
git add -A
git commit -m "Initial template: Cursor Starter Kit"
git push

# 6. Enable template mode on GitHub
# Go to repo Settings → Template repository → Enable
```

## What Needs to Be Managed

### Source of Truth (`quant/cursor-starter-kit/`)
✅ **Managed automatically** - Changes here are committed to `quant` repo

**Files to maintain**:
- All starter kit files (`.cursorrules`, scripts, tests, etc.)
- `install.sh` - Installation script
- `cursorkit.zsh` - Shell helper
- `sync-check.sh` - Maintenance tool
- `sync-from-source.sh` - Maintenance tool
- `create-repo-with-kit.sh` - CLI automation (optional)
- `README.md` - User documentation
- `TEMPLATE-SETUP.md` - Setup instructions
- `TEMPLATE-MAINTENANCE.md` - This file

### Template Repository
⚠️ **Manual sync required** - Must run sync scripts after source changes

**Files to maintain**:
- All starter kit files (synced from source)
- Sync scripts (for maintenance - optional)
- Template-specific README (if different from source)

**Files to exclude**:
- `.env` (user-specific)
- `.git/` (repo-specific)
- `__pycache__/`, `*.pyc` (build artifacts)
- `.DS_Store` (OS-specific)

### Shell Configuration
⚠️ **One-time setup** - Update if `cursorkit.zsh` path changes

**If using Oh-My-Zsh**:
- Symlink or copy `cursorkit.zsh` to `~/.oh-my-zsh/custom/`
- Or source it in a custom plugin

**If using `.zshrc`**:
```zsh
source "/Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/cursorkit.zsh"
```

**Update path if**: You move the `quant` repository

## Sync Script Configuration

Both sync scripts have a hardcoded path:
```zsh
SOURCE_OF_TRUTH="/Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit"
```

**If you move the `quant` repo**, update this path in:
- `sync-check.sh` (line 24)
- `sync-from-source.sh` (line 24)

## Checklist for Template Updates

When updating the template repository:

- [ ] Make changes in source of truth (`quant/cursor-starter-kit/`)
- [ ] Commit and push to `quant` repo
- [ ] Run `./sync-template.sh --dry-run` to preview
- [ ] Run `./sync-template.sh` to sync, commit, and push
- [ ] (Optional) Test template (create test repo from template)
- [ ] (Manual) Update `cursorkit.zsh` in OMZ if needed

## Troubleshooting

### Template Repo Path Changed
**Solution**: Update `TEMPLATE_REPO` in `sync-template.sh`:
```bash
# Edit cursor-starter-kit/sync-template.sh
# Update TEMPLATE_REPO variable (line ~15)
```

### Template Repo Out of Sync
**Solution**: Run sync process (Step 2-3 above)

### cursorkit Function Not Found
**Solution**: Source the file or add to OMZ:
```bash
source "/Users/ankit/Playground/_quantRepos/quant/cursor-starter-kit/cursorkit.zsh"
```

## Best Practices

1. **Always test in source of truth first** - Make changes, test locally, then sync to template
2. **Use dry-run** - Always preview sync changes before applying
3. **Review diffs** - Check `git diff` after syncing to ensure expected changes
4. **Test template** - Create a test repo from template after major updates
5. **Document changes** - Update README/TEMPLATE-SETUP.md when adding features
6. **Keep sync scripts** - Don't delete sync scripts from template repo (they're useful for maintenance)

## Related Documentation

- `README.md` - User-facing documentation
- `TEMPLATE-SETUP.md` - Setup instructions for template repository
- `install.sh` - Installation script documentation (in script comments)
- `cursorkit.zsh` - Shell helper documentation (in script comments)
