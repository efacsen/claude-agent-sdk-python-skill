---
source_url: https://platform.claude.com/docs/en/agent-sdk/python
last_fetched: 2026-04-08T23:02:10.255696+00:00
topic: 05-mcp-tools
---

### `tool()`


Decorator for defining MCP tools with type safety.




```python
def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any],
    annotations: ToolAnnotations | None = None
) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]
```


#### Parameters




| Parameter | Type | Description |
| --- | --- | --- |
| `name` | `str` | Unique identifier for the tool |
| `description` | `str` | Human-readable description of what the tool does |
| `input_schema` | `type | dict[str, Any]` | Schema defining the tool's input parameters (see below) |
| `annotations` | [`ToolAnnotations`](#tool-annotations) `| None` | Optional MCP tool annotations providing behavioral hints to clients |


#### Input schema options


1. **Simple type mapping** (recommended):



```python
{"text": str, "count": int, "enabled": bool}
```
2. **JSON Schema format** (for complex validation):



```python
{
    "type": "object",
    "properties": {
        "text": {"type": "string"},
        "count": {"type": "integer", "minimum": 0},
    },
    "required": ["text"],
}
```


#### Returns


A decorator function that wraps the tool implementation and returns an `SdkMcpTool` instance.


#### Example



```python
from claude_agent_sdk import tool
from typing import Any


@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"Hello, {args['name']}!"}]}
```

#### `ToolAnnotations`


Re-exported from `mcp.types` (also available as `from claude_agent_sdk import ToolAnnotations`). All fields are optional hints; clients should not rely on them for security decisions.




| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `title` | `str | None` | `None` | Human-readable title for the tool |
| `readOnlyHint` | `bool | None` | `False` | If `True`, the tool does not modify its environment |
| `destructiveHint` | `bool | None` | `True` | If `True`, the tool may perform destructive updates (only meaningful when `readOnlyHint` is `False`) |
| `idempotentHint` | `bool | None` | `False` | If `True`, repeated calls with the same arguments have no additional effect (only meaningful when `readOnlyHint` is `False`) |
| `openWorldHint` | `bool | None` | `True` | If `True`, the tool interacts with external entities (for example, web search). If `False`, the tool's domain is closed (for example, a memory tool) |



```python
from claude_agent_sdk import tool, ToolAnnotations
from typing import Any


@tool(
    "search",
    "Search the web",
    {"query": str},
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
)
async def search(args: dict[str, Any]) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": f"Results for: {args['query']}"}]}
```

### `create_sdk_mcp_server()`


Create an in-process MCP server that runs within your Python application.




```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```


#### Parameters




| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `name` | `str` | - | Unique identifier for the server |
| `version` | `str` | `"1.0.0"` | Server version string |
| `tools` | `list[SdkMcpTool[Any]] | None` | `None` | List of tool functions created with `@tool` decorator |


#### Returns


Returns an `McpSdkServerConfig` object that can be passed to `ClaudeAgentOptions.mcp_servers`.


#### Example



```python
from claude_agent_sdk import tool, create_sdk_mcp_server


@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {"content": [{"type": "text", "text": f"Sum: {args['a'] + args['b']}"}]}


@tool("multiply", "Multiply two numbers", {"a": float, "b": float})
async def multiply(args):
    return {"content": [{"type": "text", "text": f"Product: {args['a'] * args['b']}"}]}


calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add, multiply],  # Pass decorated functions
)

# Use with Claude
options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add", "mcp__calc__multiply"],
)
```

### `SdkMcpTool`


Definition for an SDK MCP tool created with the `@tool` decorator.



```python
@dataclass
class SdkMcpTool(Generic[T]):
    name: str
    description: str
    input_schema: type[T] | dict[str, Any]
    handler: Callable[[T], Awaitable[dict[str, Any]]]
    annotations: ToolAnnotations | None = None
```



| Property | Type | Description |
| --- | --- | --- |
| `name` | `str` | Unique identifier for the tool |
| `description` | `str` | Human-readable description |
| `input_schema` | `type[T] | dict[str, Any]` | Schema for input validation |
| `handler` | `Callable[[T], Awaitable[dict[str, Any]]]` | Async function that handles tool execution |
| `annotations` | `ToolAnnotations | None` | Optional MCP tool annotations (e.g., `readOnlyHint`, `destructiveHint`, `openWorldHint`). From `mcp.types` |

### `McpSdkServerConfig`


Configuration for SDK MCP servers created with `create_sdk_mcp_server()`.



```python
class McpSdkServerConfig(TypedDict):
    type: Literal["sdk"]
    name: str
    instance: Any  # MCP Server instance
```

### `McpServerConfig`


Union type for MCP server configurations.



```python
McpServerConfig = (
    McpStdioServerConfig | McpSSEServerConfig | McpHttpServerConfig | McpSdkServerConfig
)
```

#### `McpStdioServerConfig`



```python
class McpStdioServerConfig(TypedDict):
    type: NotRequired[Literal["stdio"]]  # Optional for backwards compatibility
    command: str
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]
```

#### `McpSSEServerConfig`



```python
class McpSSEServerConfig(TypedDict):
    type: Literal["sse"]
    url: str
    headers: NotRequired[dict[str, str]]
```

#### `McpHttpServerConfig`



```python
class McpHttpServerConfig(TypedDict):
    type: Literal["http"]
    url: str
    headers: NotRequired[dict[str, str]]
```

### Using custom tools with ClaudeSDKClient



```python
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    tool,
    create_sdk_mcp_server,
    AssistantMessage,
    TextBlock,
)
import asyncio
from typing import Any


# Define custom tools with @tool decorator
@tool("calculate", "Perform mathematical calculations", {"expression": str})
async def calculate(args: dict[str, Any]) -> dict[str, Any]:
    try:
        result = eval(args["expression"], {"__builtins__": {}})
        return {"content": [{"type": "text", "text": f"Result: {result}"}]}
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "is_error": True,
        }


@tool("get_time", "Get current time", {})
async def get_time(args: dict[str, Any]) -> dict[str, Any]:
    from datetime import datetime

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return {"content": [{"type": "text", "text": f"Current time: {current_time}"}]}


async def main():
    # Create SDK MCP server with custom tools
    my_server = create_sdk_mcp_server(
        name="utilities", version="1.0.0", tools=[calculate, get_time]
    )

    # Configure options with the server
    options = ClaudeAgentOptions(
        mcp_servers={"utils": my_server},
        allowed_tools=["mcp__utils__calculate", "mcp__utils__get_time"],
    )

    # Use ClaudeSDKClient for interactive tool usage
    async with ClaudeSDKClient(options=options) as client:
        await client.query("What's 123 * 456?")

        # Process calculation response
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Calculation: {block.text}")

        # Follow up with time query
        await client.query("What time is it now?")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(f"Time: {block.text}")


asyncio.run(main())
```
