# Cursor Starter Kit Test Suite

Tests for verifying the starter kit scripts work correctly after installation.

## Quick Start

```bash
# Run all tests
python tests/run_all.py

# Run specific test
python tests/test_cursor_usage.py
python tests/test_export_chat.py
python tests/test_web_search.py
```

## Test Coverage

| Script | Test File | Status |
|--------|-----------|--------|
| `cursor_usage.py` | `test_cursor_usage.py` | ✅ |
| `export-chat.sh` | `test_export_chat.py` | ✅ |
| `web_search.py` | `test_web_search.py` | ⚠️ (requires API key) |
| `search_script.py` | `test_search_script.py` | ⚠️ (requires API key) |
| `update-cursor.sh` | `test_update_cursor.py` | ⚠️ (dry-run only) |

## Requirements

- Python 3.8+
- Access to `~/.cursor/chats` (for export-chat tests)
- `GEMINI_API_KEY` in `.env` (for web search tests, optional)

## Running Tests

### All Tests
```bash
python tests/run_all.py
```

### Individual Tests
```bash
python tests/test_cursor_usage.py
python tests/test_export_chat.py
python tests/test_web_search.py --skip-api  # Skip API-required tests
```

### With Coverage
```bash
pip install pytest pytest-cov
pytest tests/ --cov=cursor-scripts --cov-report=html
```

## Test Structure

```
tests/
├── README.md              # This file
├── run_all.py            # Test runner
├── test_cursor_usage.py  # Usage tracking tests
├── test_export_chat.py    # Chat export tests
├── test_web_search.py     # Web search tests
├── test_search_script.py  # Minimal search tests
├── test_update_cursor.py  # Update script tests
└── fixtures/              # Test data
    └── sample_usage.csv   # Sample CSV for import tests
```

## Notes

- **API Tests**: Web search tests require `GEMINI_API_KEY`. Use `--skip-api` to skip.
- **Export Tests**: Require access to `~/.cursor/chats`. Will skip if not available.
- **Update Tests**: Only test script syntax, not actual updates (dry-run).
