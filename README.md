# Cursor Starter Kit

A portable template for setting up Cursor CLI workflows in new repositories.

## Quick Start

1. Copy this entire directory to your new repo root
2. Copy `.env.example` to `.env` and add your API keys
3. Make scripts executable: `chmod +x cursor-scripts/*.sh`

## Contents

### Directory Structure

```
cursor-starter-kit/
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

## MCP Bypass Pattern

If you need to work around Cursor's MCP tool serialization issues, see the `mcp-bypass-skeleton/` directory (if included) for a template wrapper pattern.
