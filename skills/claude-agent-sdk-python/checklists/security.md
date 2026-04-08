# Security Checklist — Least Privilege and Safety

Rules for agent security and threat mitigation.

## #no-bypass
`permission_mode="bypassPermissions"` is **forbidden** without:
1. Explicit user acknowledgement ("yes, I know what bypass means")
2. A documented threat model in the generated code's docstring
3. The agent running in an isolated/sandboxed environment

Default to `"default"`, `"acceptEdits"`, or `"dontAsk"`.

## #explicit-allowlist
`allowed_tools` must be an explicit list. Never rely on defaults for production:
```python
# Good
allowed_tools=["Read", "Glob", "Grep"]

# Bad
# (nothing — lets Claude pick)
```

## #bash-denylist
If `"Bash"` is in `allowed_tools`, a `PreToolUse` hook **must** validate commands against a denylist:
```python
DANGEROUS = ["rm -rf /", "curl | sh", "wget | sh", ":(){ :|:& };:"]

async def validate_bash(input_data, tool_use_id, context):
    if input_data["tool_name"] == "Bash":
        cmd = input_data["tool_input"].get("command", "")
        if any(bad in cmd for bad in DANGEROUS):
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Blocked dangerous command: {cmd!r}",
                }
            }
    return {}
```

## #no-hardcoded-secrets
`ANTHROPIC_API_KEY`, GitHub tokens, database passwords, etc. **must** come from environment variables:
```python
# Good
api_key = os.environ["GITHUB_TOKEN"]

# Bad
api_key = "ghp_abcdef1234..."
```

## #dontask-for-unattended
Unattended agents (daemons, cron jobs, webhooks) **must** use `permission_mode="dontAsk"` with a pre-approved `allowed_tools` list. Never leave an unattended agent prompting on stdin.

## #disallowed-by-default-for-readonly
Read-only agents (analyzers, reviewers) should explicitly set:
```python
disallowed_tools=["Write", "Edit", "NotebookEdit", "Bash"]
```
Belt-and-suspenders against accidentally granting write access.

## #custom-tool-input-validation
Custom tools (`@tool`) **must** validate `args` at the top of the function. Untrusted input from Claude can contain anything:
```python
@tool("open_issue", "Open a GitHub issue", {"title": str, "body": str})
async def open_issue(args):
    title = args.get("title", "").strip()
    if not title or len(title) > 200:
        return {"content": [{"type": "text", "text": "Invalid title"}], "isError": True}
    ...
```

## #mcp-server-trust-boundary
Third-party MCP servers (via `mcp_servers={"name": {"command": ..., "args": ...}}`) run subprocesses. Pin versions and audit what you install. Don't mix untrusted MCP with `bypassPermissions`.

## #log-hook-pii-awareness
`PostToolUse` audit-log hooks capture tool inputs. Don't log raw file contents, passwords, or PII unless you have a retention policy. Redact first.

## #session-id-is-sensitive
`session_id` can be used to resume conversations — treat it like a session token. Don't log it to unprotected stderr, and don't pass it through URL query strings.
