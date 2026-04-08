---
source_url: https://platform.claude.com/docs/en/agent-sdk/python
last_fetched: 2026-04-08T21:21:24.875141+00:00
topic: 02-options
---

### `ClaudeAgentOptions`


Configuration dataclass for Claude Code queries.




```python
@dataclass
class ClaudeAgentOptions:
    tools: list[str] | ToolsPreset | None = None
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    max_budget_usd: float | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    model: str | None = None
    fallback_model: str | None = None
    betas: list[SdkBeta] = field(default_factory=list)
    output_format: dict[str, Any] | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    cli_path: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    max_buffer_size: int | None = None
    debug_stderr: Any = sys.stderr  # Deprecated
    stderr: Callable[[str], None] | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    user: str | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    setting_sources: list[SettingSource] | None = None
    sandbox: SandboxSettings | None = None
    plugins: list[SdkPluginConfig] = field(default_factory=list)
    max_thinking_tokens: int | None = None  # Deprecated: use thinking instead
    thinking: ThinkingConfig | None = None
    effort: Literal["low", "medium", "high", "max"] | None = None
    enable_file_checkpointing: bool = False
```




| Property | Type | Default | Description |
| --- | --- | --- | --- |
| `tools` | `list[str] | ToolsPreset | None` | `None` | Tools configuration. Use `{"type": "preset", "preset": "claude_code"}` for Claude Code's default tools |
| `allowed_tools` | `list[str]` | `[]` | Tools to auto-approve without prompting. This does not restrict Claude to only these tools; unlisted tools fall through to `permission_mode` and `can_use_tool`. Use `disallowed_tools` to block tools. See [Permissions](/docs/en/agent-sdk/permissions#allow-and-deny-rules) |
|  |

### `OutputFormat`


Configuration for structured output validation. Pass this as a `dict` to the `output_format` field on `ClaudeAgentOptions`:



```python
# Expected dict shape for output_format
{
    "type": "json_schema",
    "schema": {...},  # Your JSON Schema definition
}
```



| Field | Required | Description |
| --- | --- | --- |
| `type` | Yes | Must be `"json_schema"` for JSON Schema validation |
| `schema` | Yes | JSON Schema definition for output validation |

### `SystemPromptPreset`


Configuration for using Claude Code's preset system prompt with optional additions.



```python
class SystemPromptPreset(TypedDict):
    type: Literal["preset"]
    preset: Literal["claude_code"]
    append: NotRequired[str]
```



| Field | Required | Description |
| --- | --- | --- |
| `type` | Yes | Must be `"preset"` to use a preset system prompt |
| `preset` | Yes | Must be `"claude_code"` to use Claude Code's system prompt |
| `append` | No | Additional instructions to append to the preset system prompt |

### `SettingSource`


Controls which filesystem-based configuration sources the SDK loads settings from.



```python
SettingSource = Literal["user", "project", "local"]
```



| Value | Description | Location |
| --- | --- | --- |
| `"user"` | Global user settings | `~/.claude/settings.json` |
| `"project"` | Shared project settings (version controlled) | `.claude/settings.json` |
| `"local"` | Local project settings (gitignored) | `.claude/settings.local.json` |


#### Default behavior


When `setting_sources` is **omitted** or **`None`**, the SDK does **not** load any filesystem settings. This provides isolation for SDK applications.


#### Why use setting\_sources


**Load all filesystem settings (legacy behavior):**



```python
# Load all settings like SDK v0.0.x did
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt="Analyze this code",
    options=ClaudeAgentOptions(
        setting_sources=["user", "project", "local"]  # Load all settings
    ),
):
    print(message)
```

**Load only specific setting sources:**



```python
# Load only project settings, ignore user and local
async for message in query(
    prompt="Run CI checks",
    options=ClaudeAgentOptions(
        setting_sources=["project"]  # Only .claude/settings.json
    ),
):
    print(message)
```

**Testing and CI environments:**



```python
# Ensure consistent behavior in CI by excluding local settings
async for message in query(
    prompt="Run tests",
    options=ClaudeAgentOptions(
        setting_sources=["project"],  # Only team-shared settings
        permission_mode="bypassPermissions",
    ),
):
    print(message)
```

**SDK-only applications:**



```python
# Define everything programmatically (default behavior)
# No filesystem dependencies - setting_sources defaults to None
async for message in query(
    prompt="Review this PR",
    options=ClaudeAgentOptions(
        # setting_sources=None is the default, no need to specify
        agents={...},
        mcp_servers={...},
        allowed_tools=["Read", "Grep", "Glob"],
    ),
):
    print(message)
```

**Loading CLAUDE.md project instructions:**



```python
# Load project settings to include CLAUDE.md files
async for message in query(
    prompt="Add a new feature following project conventions",
    options=ClaudeAgentOptions(
        system_prompt={
            "type": "preset",
            "preset": "claude_code",  # Use Claude Code's system prompt
        },
        setting_sources=["project"],  # Required to load CLAUDE.md from project
        allowed_tools=["Read", "Write", "Edit"],
    ),
):
    print(message)
```

#### Settings precedence


When multiple sources are loaded, settings are merged with this precedence (highest to lowest):


1. Local settings (`.claude/settings.local.json`)
2. Project settings (`.claude/settings.json`)
3. User settings (`~/.claude/settings.json`)


Programmatic options (like `agents`, `allowed_tools`) always override filesystem settings.

### `AgentDefinition`


Configuration for a subagent defined programmatically.



```python
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
    skills: list[str] | None = None
    memory: Literal["user", "project", "local"] | None = None
    mcpServers: list[str | dict[str, Any]] | None = None
```



| Field | Required | Description |
| --- | --- | --- |
| `description` | Yes | Natural language description of when to use this agent |
| `prompt` | Yes | The agent's system prompt |
| `tools` | No | Array of allowed tool names. If omitted, inherits all tools |
| `model` | No | Model override for this agent. If omitted, uses the main model |
| `skills` | No | List of skill names available to this agent |
| `memory` | No | Memory source for this agent: , , or |
