# Quick Guide: Testing MCP Servers with @modelcontextprotocol/inspector

This guide provides a brief overview of how to test Model Context Protocol (MCP) servers using the `@modelcontextprotocol/inspector` CLI.

## 1. Installation

First, ensure you have the inspector installed globally via npm:

```sh
npm install -g @modelcontextprotocol/inspector
```

## 2. Identify Server Transport

Before testing, you need to know how your MCP server communicates. Check its startup logs for the `Transport` type. The two common types are:
- **STDIO:** The server communicates over standard input/output (the console).
- **HTTP:** The server listens on a specific network port (e.g., `http://localhost:8080`).

Our `AgentEnforcer` server uses **STDIO**.

## 3. Testing with STDIO Transport

When the server uses STDIO, you point the `inspector` CLI directly to the command that runs the server.

### List Available Tools

This command launches your server as a subprocess and asks it to list its tools.

```sh
npx @modelcontextprotocol/inspector --cli [command_to_run_server] --method tools/list
```

**Example for `AgentEnforcer`:**
```sh
# Ensure you are in the project root directory
npx @modelcontextprotocol/inspector --cli ".\venv\Scripts\python.exe" -m "enforcer.mcp_server" --method tools/list
```

### Call a Specific Tool

To call a tool, use the `tools/call` method and provide the tool's name and arguments.

```sh
npx @modelcontextprotocol/inspector --cli [command_to_run_server] --method tools/call --tool-name [tool_name] --tool-arg [arg_name]=[arg_value]
```

**Example for `AgentEnforcer`:**
```sh
# Calls the 'checker' tool with the 'check_git_modified_files' argument
npx @modelcontextprotocol/inspector --cli ".\venv\Scripts\python.exe" -m "enforcer.mcp_server" --method tools/call --tool-name checker --tool-arg check_git_modified_files=true
```

## 4. Testing with HTTP Transport

If your server runs on HTTP, you provide the `inspector` with the server's URL.

### List Available Tools
```sh
npx @modelcontextprotocol/inspector --cli --uri [server_url] --method tools/list
```
**Example:**
```sh
npx @modelcontextprotocol/inspector --cli --uri http://127.0.0.1:8080 --method tools/list
```

### Call a Specific Tool
```sh
npx @modelcontextprotocol/inspector --cli --uri [server_url] --method tools/call --tool-name [tool_name] --tool-arg [arg_name]=[arg_value]
```
**Example:**
```sh
npx @modelcontextprotocol/inspector --cli --uri http://127.0.0.1:8080 --method tools/call --tool-name my_tool --tool-arg param1=value1
```

---
*This guide covers the basic CLI functionality. For visual testing and more advanced features, refer to the official [inspector documentation](https://github.com/modelcontextprotocol/inspector).* 