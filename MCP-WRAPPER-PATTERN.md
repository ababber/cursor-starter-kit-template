# MCP Wrapper Pattern

**When to use:** If an MCP server's tools fail through Cursor's client (serialization bugs, permission issues, etc.), create a wrapper to bypass the problematic layer.

## The Problem

MCP servers expose tools that Cursor's AI should be able to call directly. Sometimes this fails due to:
- **Serialization bugs** - Cursor's MCP client mangles complex JSON
- **Permission issues** - Docker/filesystem access from Cursor's subprocess
- **Transport issues** - SSE/stdio connection problems
- **Credential handling** - Environment variables not passed correctly

## The Solution Pattern

Create a Python wrapper that:
1. Connects directly to the MCP server (bypassing Cursor's client)
2. Accepts tool calls via CLI arguments
3. Returns results to JSON files
4. Provides shell aliases for easy invocation

## Implementation Steps

### Step 1: Identify the Bug

Test the MCP tool through Cursor's client:

```python
# In Cursor, this fails:
mcp_ServerName_tool_name({"arg": "value"})
```

If it fails, note:
- Error message
- Expected input/output format
- Which tools are affected

### Step 2: Create Wrapper Script

**File: `mcp-wrapper/wrapper.py`**

```python
#!/usr/bin/env python3
import json
import sys
import subprocess
import os
from datetime import datetime

# MCP server connection details
MCP_SERVER_CMD = ["docker", "exec", "mcp-container", "command"]  # Or stdio command
RESULTS_DIR = "mcp-wrapper/results"

def call_mcp_tool(tool_name, args_json):
    """Call MCP server directly via stdio/docker."""
    # Build MCP protocol request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": json.loads(args_json) if isinstance(args_json, str) else args_json
        }
    }
    
    # Send to MCP server
    proc = subprocess.run(
        MCP_SERVER_CMD,
        input=json.dumps(request),
        capture_output=True,
        text=True
    )
    
    # Parse response
    if proc.returncode != 0:
        return {"success": False, "error": proc.stderr}
    
    try:
        response = json.loads(proc.stdout)
        return {"success": True, "response": response.get("result", {})}
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}"}

def save_result(request_id, result):
    """Save result to file for AI to read."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    output = {
        "request_id": request_id,
        "timestamp": datetime.now().isoformat(),
        "result": result
    }
    
    filepath = os.path.join(RESULTS_DIR, f"{request_id}.json")
    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"RESULT_FILE:{os.path.abspath(filepath)}")
    print("SUCCESS" if result.get("success") else "ERROR")
    return filepath

def main():
    if len(sys.argv) < 3:
        print("Usage: python wrapper.py <request_id> <tool_name> '<json_args>'")
        sys.exit(1)
    
    request_id = sys.argv[1]
    tool_name = sys.argv[2]
    args_json = sys.argv[3] if len(sys.argv) > 3 else "{}"
    
    # Call MCP tool
    result = call_mcp_tool(tool_name, args_json)
    
    # Save result
    save_result(request_id, result)
    
    # Print result for immediate use
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
```

### Step 3: Create Shell Aliases

**Add to `~/.zshrc` or create Oh My Zsh plugin:**

```bash
# MCP Wrapper Functions
export MCP_WRAPPER_ROOT="/path/to/your/project"

# Quick command runner
mcp-run() {
    local request_id="req_$(date +%s)"
    local tool_name="$1"
    shift
    local args="$*"
    
    cd "$MCP_WRAPPER_ROOT" && \
    python3 mcp-wrapper/wrapper.py "$request_id" "$tool_name" "$args"
}

# Auto-generated request ID
mcp-ai-run() {
    local request_id="$1"
    local tool_name="$2"
    shift 2
    local args="$*"
    
    cd "$MCP_WRAPPER_ROOT" && \
    python3 mcp-wrapper/wrapper.py "$request_id" "$tool_name" "$args"
}
```

### Step 4: Update .cursorrules

Instruct the AI to use the wrapper:

```markdown
### 🔧 MCP Server Wrapper

**Problem:** MCP tools fail through Cursor's client (serialization bug).

**Solution:** Use wrapper via Shell tool.

**Command pattern:**
```bash
mcp-ai-run <request_id> <tool_name> '<json_args>'
```

**Workflow:**
1. Generate unique request_id (e.g., `req_001`)
2. Run wrapper command via Shell
3. Read result from `mcp-wrapper/results/<request_id>.json`

**Example:**
```bash
# Get data
mcp-ai-run req_001 get_user_info '{}'

# Parse result
import json
result = json.loads(read_file('mcp-wrapper/results/req_001.json'))
data = result["result"]["response"]
```

**Status:**
✅ Wrapper bypasses Cursor's bug
✅ All tools accessible
⚠️ Must use wrapper (don't call `mcp_ServerName_*` directly)
```

### Step 5: Test the Wrapper

```bash
# Test basic call
python3 mcp-wrapper/wrapper.py test_001 tool_name '{}'

# Check result file
cat mcp-wrapper/results/test_001.json

# Test via alias
mcp-run tool_name '{}'
```

## AI Usage Pattern

When AI needs MCP data:

1. **Generate request ID:**
   ```python
   request_id = f"req_{uuid.uuid4().hex[:8]}"
   ```

2. **Call wrapper:**
   ```bash
   mcp-ai-run req_abc123 tool_name '{"arg": "value"}'
   ```

3. **Read result:**
   ```python
   result = json.loads(read_file(f'mcp-wrapper/results/req_abc123.json'))
   if result["result"]["success"]:
       data = result["result"]["response"]
   ```

## Environment Detection

Add to session continuity checks:

```bash
# Check if wrapper is available
if command -v mcp-run &> /dev/null; then
    echo "✅ MCP Wrapper: Available"
else
    echo "⚠️ MCP Wrapper: Not installed (reload shell)"
fi
```

## File Structure

```
project/
├── mcp-wrapper/
│   ├── wrapper.py           # Core wrapper script
│   ├── results/             # Result files (JSON)
│   │   ├── req_001.json
│   │   └── req_002.json
│   └── README.md            # Usage docs
├── .cursorrules             # Instructions for AI
└── ~/.zshrc                 # Shell aliases
```

## Advantages

✅ **Bypasses client bugs** - Direct MCP server access  
✅ **Traceable** - Every call has unique ID  
✅ **Debuggable** - Results saved to files  
✅ **Parallel calls** - AI can batch requests  
✅ **Environment isolation** - Uses your shell's env vars  

## Real Example: QuantConnect MCP

The QuantConnect MCP server had a serialization bug where 59/64 tools failed through Cursor's client.

**Solution:**
- Created `qc_mcp_wrapper.py` that connects to Docker container
- Added `qc-ai-run` shell function
- Saved results to `cursor-qc-env/results/`
- Updated `.cursorrules` with usage pattern

**Result:** 100% of tools now work through wrapper.

See `cursor-qc-env/WRAPPER-USAGE-FOR-AI.md` for full implementation.

## Customization

Adapt this pattern to your MCP server:

1. **Connection method:**
   - Docker exec: `docker exec container command`
   - Stdio: `npx mcp-server-name`
   - HTTP: `requests.post(mcp_url, json=request)`

2. **Authentication:**
   - Environment vars: `os.environ.get("API_KEY")`
   - Config file: `json.load(open(".env.json"))`
   - Credential store: `keyring.get_password("service", "user")`

3. **Result format:**
   - Simple JSON: `{"success": true, "data": {...}}`
   - Full MCP response: Include entire `result` object
   - Streaming: Write chunks to file as they arrive

## When NOT to Use

Don't create a wrapper if:
- MCP tools work fine through Cursor's client
- Issue is with MCP server itself (not client)
- Problem can be fixed with better error handling

Try fixing the underlying issue first. Wrappers add complexity.

## Troubleshooting

**"Command not found"**
- Reload shell: `source ~/.zshrc`
- Check alias: `type mcp-run`

**"Docker permission denied"**
- Run in CLI mode (Docker running)
- Or provide commands for user to run manually

**"Result file empty"**
- Check MCP server logs
- Verify JSON arguments are valid
- Test MCP tool outside wrapper

## Further Reading

- MCP Protocol Spec: https://modelcontextprotocol.io/docs/
- Cursor MCP Integration: https://docs.cursor.com/context/model-context-protocol
- Example Implementation: See `cursor-qc-env/` in this repo
