# Memory server for AI Chat with MCP interface

This is an example of the memory server for AI chat. It follows the interface supported by the tool [CleverChatty](https://github.com/Gelembjuk/cleverchatty).

The interface for the MCP server is:

```json
{
    "tools": [
    {
      "name": "remember",
      "description": "Remember a chat message to extract a context later for the memory",
      "inputSchema": {
        "properties": {
          "role": { "type": "string" },
          "message": { "type": "string" }
        },
        "required": ["role", "message"]
      }
    },
    {
      "name": "recall",
      "description": "Returns the summary of the previous conversations",
      "inputSchema": {
        "properties": {
        },
        "required": []
      }
    }
    ]
}
```

## How to run

1. Clone the repository
```bash
git clone
cd memory-server
```

2. Install uv if not already installed
```bash
curl -Ls https://astral.sh/uv/install.sh | sh
```

3. Create the virtual environment
```bash
uv venv
```

4. Activate the virtual environment on Linux/macOS (can be different on other platforms)
```bash
source .venv/bin/activate
```



