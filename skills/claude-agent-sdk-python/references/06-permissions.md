---
source_url: https://code.claude.com/docs/en/agent-sdk/python
last_fetched: 2026-04-08T23:13:02.414543+00:00
topic: 06-permissions
---

### `PermissionMode`


Permission modes for controlling tool execution.



```python
PermissionMode = Literal[
    "default",  # Standard permission behavior
    "acceptEdits",  # Auto-accept file edits
    "plan",  # Planning mode - read-only tools only
    "dontAsk",  # Deny anything not pre-approved instead of prompting
    "bypassPermissions",  # Bypass all permission checks (use with caution)
]
```

### `CanUseTool`


Type alias for tool permission callback functions.



```python
CanUseTool = Callable[
    [str, dict[str, Any], ToolPermissionContext], Awaitable[PermissionResult]
]
```

The callback receives:


* `tool_name`: Name of the tool being called
* `input_data`: The tool's input parameters
* `context`: A `ToolPermissionContext` with additional information


Returns a `PermissionResult` (either `PermissionResultAllow` or `PermissionResultDeny`).

### `ToolPermissionContext`


Context information passed to tool permission callbacks.



```python
@dataclass
class ToolPermissionContext:
    signal: Any | None = None  # Future: abort signal support
    suggestions: list[PermissionUpdate] = field(default_factory=list)
```



| Field | Type | Description |
| --- | --- | --- |
| `signal` | `Any | None` | Reserved for future abort signal support |
| `suggestions` | `list[PermissionUpdate]` | Permission update suggestions from the CLI |

### `PermissionResult`


Union type for permission callback results.



```python
PermissionResult = PermissionResultAllow | PermissionResultDeny
```

### `PermissionResultAllow`


Result indicating the tool call should be allowed.



```python
@dataclass
class PermissionResultAllow:
    behavior: Literal["allow"] = "allow"
    updated_input: dict[str, Any] | None = None
    updated_permissions: list[PermissionUpdate] | None = None
```



| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `behavior` | `Literal["allow"]` | `"allow"` | Must be "allow" |
| `updated_input` | `dict[str, Any] | None` | `None` | Modified input to use instead of original |
| `updated_permissions` | `list[PermissionUpdate] | None` | `None` | Permission updates to apply |

### `PermissionResultDeny`


Result indicating the tool call should be denied.



```python
@dataclass
class PermissionResultDeny:
    behavior: Literal["deny"] = "deny"
    message: str = ""
    interrupt: bool = False
```



| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `behavior` | `Literal["deny"]` | `"deny"` | Must be "deny" |
| `message` | `str` | `""` | Message explaining why the tool was denied |
| `interrupt` | `bool` | `False` | Whether to interrupt the current execution |

### `PermissionUpdate`


Configuration for updating permissions programmatically.



```python
@dataclass
class PermissionUpdate:
    type: Literal[
        "addRules",
        "replaceRules",
        "removeRules",
        "setMode",
        "addDirectories",
        "removeDirectories",
    ]
    rules: list[PermissionRuleValue] | None = None
    behavior: Literal["allow", "deny", "ask"] | None = None
    mode: PermissionMode | None = None
    directories: list[str] | None = None
    destination: (
        Literal["userSettings", "projectSettings", "localSettings", "session"] | None
    ) = None
```



| Field | Type | Description |
| --- | --- | --- |
| `type` | `Literal[...]` | The type of permission update operation |
| `rules` | `list[PermissionRuleValue] | None` | Rules for add/replace/remove operations |
| `behavior` | `Literal["allow", "deny", "ask"] | None` | Behavior for rule-based operations |
| `mode` | `PermissionMode | None` | Mode for setMode operation |
| `directories` |  |

### `PermissionRuleValue`


A rule to add, replace, or remove in a permission update.



```python
@dataclass
class PermissionRuleValue:
    tool_name: str
    rule_content: str | None = None
```

### Permissions Fallback for Unsandboxed Commands


When `allowUnsandboxedCommands` is enabled, the model can request to run commands outside the sandbox by setting `dangerouslyDisableSandbox: True` in the tool input. These requests fall back to the existing permissions system, meaning your `can_use_tool` handler will be invoked, allowing you to implement custom authorization logic.


**`excludedCommands` vs `allowUnsandboxedCommands`:**

* `excludedCommands`: A static list of commands that always bypass the sandbox automatically (e.g., `["docker"]`). The model has no control over this.
* `allowUnsandboxedCommands`: Lets the model decide at runtime whether to request unsandboxed execution by setting `dangerouslyDisableSandbox: True` in the tool input.


```python
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    HookMatcher,
    PermissionResultAllow,
    PermissionResultDeny,
    ToolPermissionContext,
)


async def can_use_tool(
    tool: str, input: dict, context: ToolPermissionContext
) -> PermissionResultAllow | PermissionResultDeny:
    # Check if the model is requesting to bypass the sandbox
    if tool == "Bash" and input.get("dangerouslyDisableSandbox"):
        # The model is requesting to run this command outside the sandbox
        print(f"Unsandboxed command requested: {input.get('command')}")

        if is_command_authorized(input.get("command")):
            return PermissionResultAllow()
        return PermissionResultDeny(
            message="Command not authorized for unsandboxed execution"
        )
    return PermissionResultAllow()


# Required: dummy hook keeps the stream open for can_use_tool
async def dummy_hook(input_data, tool_use_id, context):
    return {"continue_": True}


async def prompt_stream():
    yield {
        "type": "user",
        "message": {"role": "user", "content": "Deploy my application"},
    }


async def main():
    async for message in query(
        prompt=prompt_stream(),
        options=ClaudeAgentOptions(
            sandbox={
                "enabled": True,
                "allowUnsandboxedCommands": True,  # Model can request unsandboxed execution
            },
            permission_mode="default",
            can_use_tool=can_use_tool,
            hooks={"PreToolUse": [HookMatcher(matcher=None, hooks=[dummy_hook])]},
        ),
    ):
        print(message)
```

This pattern enables you to:


* **Audit model requests**: Log when the model requests unsandboxed execution
* **Implement allowlists**: Only permit specific commands to run unsandboxed
* **Add approval workflows**: Require explicit authorization for privileged operations


Commands running with `dangerouslyDisableSandbox: True` have full system access. Ensure your `can_use_tool` handler validates these requests carefully.

If `permission_mode` is set to `bypassPermissions` and `allow_unsandboxed_commands` is enabled, the model can autonomously execute commands outside the sandbox without any approval prompts. This combination effectively allows the model to escape sandbox isolation silently.
