# Cursor Starter Kit

A portable template for setting up Cursor CLI workflows in new repositories.

> **Note:** Changes to this directory are automatically synced to the template repository via git hook.

## Quick Start

### Option 1: GitHub Template Repository (Easiest)

Create a template repository with the starter kit, then use GitHub's "Use this template" button for new repos.

See `TEMPLATE-SETUP.md` for detailed instructions.

### Option 2: Automated CLI Script

Automatically create a new GitHub repo with the starter kit:

```bash
./create-repo-with-kit.sh my-project --private --clone
```

This script:
- Creates the GitHub repository
- Clones it locally
- Installs the starter kit
- Commits and pushes everything

See `TEMPLATE-SETUP.md` for full documentation.

### Option 3: Manual Installation (Use the Installer Script)

```bash
# From the starter kit directory
./install.sh /path/to/your/repo

# Or install to current directory
cd /path/to/your/repo
/path/to/cursor-starter-kit/install.sh
```

The installer will:
- Copy all starter kit files
- Handle existing files (skip, backup, or overwrite)
- Make scripts executable
- Create `.env` from `.env.example`
- Provide next steps

### Option 2: Manual Installation

1. Copy this entire directory to your new repo root
2. Copy `.env.example` to `.env` and add your API keys
3. Make scripts executable: `chmod +x cursor-scripts/*.sh`
4. Run tests to verify installation: `python tests/run_all.py`

## Contents

### Directory Structure

```
cursor-starter-kit/
├── install.sh          # Installation script
├── .cursorrules        # AI behavior rules
├── .cursorignore       # Files to exclude from Cursor indexing
├── .gitignore          # Git ignore patterns
├── .env.example        # Environment variable template
├── cursor-scripts/     # Cursor workflow tools
│   ├── cursor_usage.py # Usage tracking & quota management
│   ├── export-chat.sh  # Chat export to markdown
│   ├── web_search.py   # Gemini web search with logging
│   ├── search_script.py# Minimal web search
│   └── update-cursor.sh# Update Cursor CLI
├── tests/              # Test suite
│   ├── README.md       # Test documentation
│   ├── run_all.py      # Test runner
│   └── test_*.py       # Individual test files
├── cursor-chats/       # Exported conversations
├── cursor-usage/       # Usage CSV imports
└── cursor-web-search/  # Web search logs
```

### Tools

| Tool | Purpose | Requirements |
|------|---------|--------------|
| `cursor_usage.py` | Track usage, quota, budget, alerts | None (uses local CSVs) |
| `export-chat.sh` | Export chat from Cursor SQLite | Access to `~/.cursor/chats` |
| `web_search.py` | Web search with logging | `GEMINI_API_KEY` |
| `search_script.py` | Quick web search | `GEMINI_API_KEY` |
| `update-cursor.sh` | Update Cursor CLI | Internet access |

### Key Features

- **Session continuity**: Auto-summarizes recent work at conversation start
- **Usage tracking**: Import Cursor usage CSVs, track quota, set budgets
- **Chat export**: One command (`/e`) to export conversation to markdown
- **Web search**: Gemini-powered search with automatic logging
- **Daily reminders**: Prompts to export yesterday's usage data

## Customization

After copying to your repo:

1. Edit `.cursorrules` to add project-specific protocols
2. Update `.cursorignore` for your file patterns
3. Add project-specific API keys to `.env`

## Testing

After installation, verify everything works:

```bash
# Run all tests
python tests/run_all.py

# Run specific test
python tests/test_cursor_usage.py
```

See `tests/README.md` for full test documentation.

## MCP Bypass Pattern

If you need to work around Cursor's MCP tool serialization issues, see the `mcp-bypass-skeleton/` directory (if included) for a template wrapper pattern.

## Template Repository Maintenance

If you're maintaining a GitHub template repository, see **[TEMPLATE-MAINTENANCE.md](TEMPLATE-MAINTENANCE.md)** for complete documentation.

**Quick sync (from source of truth):**

```bash
cd cursor-starter-kit
./sync-template.sh --dry-run  # Preview
./sync-template.sh            # Sync, commit, and push
```

**Note:** Maintenance scripts (`sync-template.sh`, `sync-check.sh`, etc.) are not part of the starter kit - they're tools for managing the template repository.
