---
source_url: https://platform.claude.com/docs/en/agent-sdk/python
last_fetched: 2026-04-08T23:02:10.255696+00:00
topic: 03-messages
---

### `get_session_messages()`


Retrieves messages from a past session. Synchronous; returns immediately.




```python
def get_session_messages(
    session_id: str,
    directory: str | None = None,
    limit: int | None = None,
    offset: int = 0
) -> list[SessionMessage]
```


#### Parameters




| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `session_id` | `str` | required | The session ID to retrieve messages for |
| `directory` | `str | None` | `None` | Project directory to look in. When omitted, searches all projects |
| `limit` | `int | None` | `None` | Maximum number of messages to return |
| `offset` | `int` | `0` | Number of messages to skip from the start |


#### Return type: `SessionMessage`




| Property | Type | Description |
| --- | --- | --- |
| `type` | `Literal["user", "assistant"]` | Message role |
| `uuid` | `str` | Unique message identifier |
| `session_id` | `str` | Session identifier |
| `message` | `Any` | Raw message content |
| `parent_tool_use_id` | `None` | Reserved for future use |


#### Example



```python
from claude_agent_sdk import list_sessions, get_session_messages

sessions = list_sessions(limit=1)
if sessions:
    messages = get_session_messages(sessions[0].session_id)
    for msg in messages:
        print(f"[{msg.type}] {msg.uuid}")
```

## Message Types

### `Message`


Union type of all possible messages.



```python
Message = (
    UserMessage
    | AssistantMessage
    | SystemMessage
    | ResultMessage
    | StreamEvent
    | RateLimitEvent
)
```

### `UserMessage`


User input message.



```python
@dataclass
class UserMessage:
    content: str | list[ContentBlock]
    uuid: str | None = None
    parent_tool_use_id: str | None = None
    tool_use_result: dict[str, Any] | None = None
```



| Field | Type | Description |
| --- | --- | --- |
| `content` | `str | list[ContentBlock]` | Message content as text or content blocks |
| `uuid` | `str | None` | Unique message identifier |
| `parent_tool_use_id` | `str | None` | Tool use ID if this message is a tool result response |
| `tool_use_result` | `dict[str, Any] | None` | Tool result data if applicable |

### `AssistantMessage`


Assistant response message with content blocks.



```python
@dataclass
class AssistantMessage:
    content: list[ContentBlock]
    model: str
    parent_tool_use_id: str | None = None
    error: AssistantMessageError | None = None
    usage: dict[str, Any] | None = None
    message_id: str | None = None
```



| Field | Type | Description |
| --- | --- | --- |
| `content` | `list[ContentBlock]` | List of content blocks in the response |
| `model` | `str` | Model that generated the response |
| `parent_tool_use_id` | `str | None` | Tool use ID if this is a nested response |
| `error` | [`AssistantMessageError`](#assistant-message-error)  `| None` | Error type if the response encountered an error |
| `usage` | `dict[str, Any] | None` | Per-message token usage (same keys as [`ResultMessage.usage`](#result-message)) |
| `message_id` | `str | None` | API message ID. Multiple messages from one turn share the same ID |

### `AssistantMessageError`


Possible error types for assistant messages.



```python
AssistantMessageError = Literal[
    "authentication_failed",
    "billing_error",
    "rate_limit",
    "invalid_request",
    "server_error",
    "max_output_tokens",
    "unknown",
]
```

### `SystemMessage`


System message with metadata.



```python
@dataclass
class SystemMessage:
    subtype: str
    data: dict[str, Any]
```

### `ResultMessage`


Final result message with cost and usage information.



```python
@dataclass
class ResultMessage:
    subtype: str
    duration_ms: int
    duration_api_ms: int
    is_error: bool
    num_turns: int
    session_id: str
    total_cost_usd: float | None = None
    usage: dict[str, Any] | None = None
    result: str | None = None
    stop_reason: str | None = None
    structured_output: Any = None
    model_usage: dict[str, Any] | None = None
```

The `usage` dict contains the following keys when present:




| Key | Type | Description |
| --- | --- | --- |
| `input_tokens` | `int` | Total input tokens consumed. |
| `output_tokens` | `int` | Total output tokens generated. |
| `cache_creation_input_tokens` | `int` | Tokens used to create new cache entries. |
| `cache_read_input_tokens` | `int` | Tokens read from existing cache entries. |


The `model_usage` dict maps model names to per-model usage. The inner dict keys use camelCase because the value is passed through unmodified from the underlying CLI process, matching the TypeScript [`ModelUsage`](/docs/en/agent-sdk/typescript#model-usage) type:




| Key | Type | Description |
| --- | --- | --- |
| `inputTokens` | `int` | Input tokens for this model. |
| `outputTokens` | `int` | Output tokens for this model. |
| `cacheReadInputTokens` | `int` | Cache read tokens for this model. |
| `cacheCreationInputTokens` | `int` | Cache creation tokens for this model. |
| `webSearchRequests` | `int` | Web search requests made by this model. |
| `costUSD` | `float` | Cost in USD for this model. |
| `contextWindow` | `int` | Context window size for this model. |
| `maxOutputTokens` | `int` | Maximum output token limit for this model. |

### `StreamEvent`


Stream event for partial message updates during streaming. Only received when `include_partial_messages=True` in `ClaudeAgentOptions`. Import via `from claude_agent_sdk.types import StreamEvent`.



```python
@dataclass
class StreamEvent:
    uuid: str
    session_id: str
    event: dict[str, Any]  # The raw Claude API stream event
    parent_tool_use_id: str | None = None
```



| Field | Type | Description |
| --- | --- | --- |
| `uuid` | `str` | Unique identifier for this event |
| `session_id` | `str` | Session identifier |
| `event` | `dict[str, Any]` | The raw Claude API stream event data |
| `parent_tool_use_id` | `str | None` | Parent tool use ID if this event is from a subagent |

### `RateLimitEvent`


Emitted when rate limit status changes (for example, from `"allowed"` to `"allowed_warning"`). Use this to warn users before they hit a hard limit, or to back off when status is `"rejected"`.



```python
@dataclass
class RateLimitEvent:
    rate_limit_info: RateLimitInfo
    uuid: str
    session_id: str
```



| Field | Type | Description |
| --- | --- | --- |
| `rate_limit_info` | [`RateLimitInfo`](#rate-limit-info) | Current rate limit state |
| `uuid` | `str` | Unique event identifier |
| `session_id` | `str` | Session identifier |

### `RateLimitInfo`


Rate limit state carried by [`RateLimitEvent`](#rate-limit-event).



```python
RateLimitStatus = Literal["allowed", "allowed_warning", "rejected"]
RateLimitType = Literal[
    "five_hour", "seven_day", "seven_day_opus", "seven_day_sonnet", "overage"
]


@dataclass
class RateLimitInfo:
    status: RateLimitStatus
    resets_at: int | None = None
    rate_limit_type: RateLimitType | None = None
    utilization: float | None = None
    overage_status: RateLimitStatus | None = None
    overage_resets_at: int | None = None
    overage_disabled_reason: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)
```



| Field | Type | Description |
| --- | --- | --- |
| `status` | `RateLimitStatus` | Current status. `"allowed_warning"` means approaching the limit; `"rejected"` means the limit was hit |
| `resets_at` | `int | None` | Unix timestamp when the rate limit window resets |
| `rate_limit_type` | `RateLimitType | None` | Which rate limit window applies |
| `utilization` | `float | None` | Fraction of the rate limit consumed (0.0 to 1.0) |
| `overage_status` | `RateLimitStatus | None` | Status of pay-as-you-go overage usage, if applicable |
| `overage_resets_at` | `int | None` | Unix timestamp when the overage window resets |
| `overage_disabled_reason` | `str | None` | Why overage is unavailable, if status is `"rejected"` |
| `raw` | `dict[str, Any]` | Full raw dict from the CLI, including fields not modeled above |

### `TaskStartedMessage`


Emitted when a background task starts. A background task is anything tracked outside the main turn: a backgrounded Bash command, a subagent spawned via the Agent tool, or a remote agent. The `task_type` field tells you which. This naming is unrelated to the `Task`-to-`Agent` tool rename.



```python
@dataclass
class TaskStartedMessage(SystemMessage):
    task_id: str
    description: str
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    task_type: str | None = None
```



| Field | Type | Description |
| --- | --- | --- |
| `task_id` | `str` | Unique identifier for the task |
| `description` | `str` | Description of the task |
| `uuid` | `str` | Unique message identifier |
| `session_id` | `str` | Session identifier |
| `tool_use_id` | `str | None` | Associated tool use ID |
| `task_type` | `str | None` | Which kind of background task: `"local_bash"`, `"local_agent"`, `"remote_agent"` |

### `TaskUsage`


Token and timing data for a background task.



```python
class TaskUsage(TypedDict):
    total_tokens: int
    tool_uses: int
    duration_ms: int
```

### `TaskProgressMessage`


Emitted periodically with progress updates for a running background task.



```python
@dataclass
class TaskProgressMessage(SystemMessage):
    task_id: str
    description: str
    usage: TaskUsage
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    last_tool_name: str | None = None
```



| Field | Type | Description |
| --- | --- | --- |
| `task_id` | `str` | Unique identifier for the task |
| `description` | `str` | Current status description |
| `usage` | `TaskUsage` | Token usage for this task so far |
| `uuid` | `str` | Unique message identifier |
| `session_id` | `str` | Session identifier |
| `tool_use_id` | `str | None` | Associated tool use ID |
| `last_tool_name` | `str | None` | Name of the last tool the task used |

### `TaskNotificationMessage`


Emitted when a task completes, fails, or is stopped.



```python
@dataclass
class TaskNotificationMessage(SystemMessage):
    task_id: str
    status: TaskNotificationStatus  # "completed" | "failed" | "stopped"
    output_file: str
    summary: str
    uuid: str
    session_id: str
    tool_use_id: str | None = None
    usage: TaskUsage | None = None
```



| Field | Type | Description |
| --- | --- | --- |
| `task_id` | `str` | Unique identifier for the task |
| `status` | `TaskNotificationStatus` | One of `"completed"`, `"failed"`, or `"stopped"` |
| `output_file` | `str` | Path to the task output file |
| `summary` | `str` | Summary of the task result |
| `uuid` | `str` | Unique message identifier |
| `session_id` | `str` | Session identifier |
| `tool_use_id` | `str | None` | Associated tool use ID |
| `usage` | `TaskUsage | None` | Final token usage for the task |

## Content Block Types

### `ContentBlock`


Union type of all content blocks.



```python
ContentBlock = TextBlock | ThinkingBlock | ToolUseBlock | ToolResultBlock
```

### `TextBlock`


Text content block.



```python
@dataclass
class TextBlock:
    text: str
```

### `ThinkingBlock`


Thinking content block (for models with thinking capability).



```python
@dataclass
class ThinkingBlock:
    thinking: str
    signature: str
```

### `ToolUseBlock`


Tool use request block.



```python
@dataclass
class ToolUseBlock:
    id: str
    name: str
    input: dict[str, Any]
```

### `ToolResultBlock`


Tool execution result block.



```python
@dataclass
class ToolResultBlock:
    tool_use_id: str
    content: str | list[dict[str, Any]] | None = None
    is_error: bool | None = None
```
