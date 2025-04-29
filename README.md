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

This tool can be used together with the [CleverChatty CLI](https://github.com/Gelembjuk/cleverchatty-cli) to create an AI chat with memory. The server will remember the messages and return the summary of the previous conversations when requested.

## How to run the server

1. Clone the repository
```bash
git clone git@github.com:Gelembjuk/cleverchatty-memory.git
cd cleverchatty-memory
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

5. Install the dependencies
```bash
uv sync
```

6. Run the server
```bash
fastapi run mcp_server.py --port 8001
```

This will start the MCP server with SSE transport on port 8001. You can change the port by modifying the `--port` argument. It will be accessible by the URL `http://localhost:8001/mcp`. You can also use the `--host` argument to change the host. By default, it will be accessible only from localhost. You can change it to `--host 0.0.0.0` to make it accessible from any IP address. 

## Test ad debug

This tool contains also the CLI to test the server. 

```bash
python manager.py COMMAND
```

Examples:

```bash
python manager.py clear-memory
python manager.py remember "user" "Some message from user"
python manager.py remember "assistant" "Some response from assistant"
python manager.py patch-memories
python manager.py recall
python manager.py history-dump
```


