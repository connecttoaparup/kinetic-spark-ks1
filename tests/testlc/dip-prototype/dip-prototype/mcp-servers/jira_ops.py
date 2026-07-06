#!/usr/bin/env python3
"""jira-ops MCP server (local stdio transport).

Same tool contract as the production Cloud Run deployment:
  - get_issue(story_id)                  -> full story JSON (incl. state)
  - update_issue(story_id, state)        -> replace the story's state object
  - set_subtask_status(story_id, subtask_id, status, pr_url?) -> targeted update

In production this server fronts real Jira; locally it is backed by
mcp-servers/data/<STORY>.json. The supervisor agent does not know or care
which - the MCP tool surface is identical (dev stdio vs prod HTTP transport,
exactly as documented in the platform guide).

Protocol: MCP over stdio - newline-delimited JSON-RPC 2.0.
Zero dependencies (Python 3.9+ stdlib).
"""
import json
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent / "data"
PROTOCOL_FALLBACK = "2024-11-05"

TOOLS = [
    {
        "name": "get_issue",
        "description": "Fetch a Jira story by id, including its durable state "
                       "(plan_approved + subtasks with status/pr_url).",
        "inputSchema": {
            "type": "object",
            "properties": {"story_id": {"type": "string"}},
            "required": ["story_id"],
        },
    },
    {
        "name": "update_issue",
        "description": "Replace the story's entire state object "
                       "(plan_approved + subtasks). Use after plan approval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "story_id": {"type": "string"},
                "state": {"type": "object"},
            },
            "required": ["story_id", "state"],
        },
    },
    {
        "name": "set_subtask_status",
        "description": "Update one subtask's status (pending|in_review|merged) "
                       "and optionally its pr_url. Preferred for single updates.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "story_id": {"type": "string"},
                "subtask_id": {"type": "string"},
                "status": {"type": "string",
                           "enum": ["pending", "in_review", "merged"]},
                "pr_url": {"type": "string"},
            },
            "required": ["story_id", "subtask_id", "status"],
        },
    },
]


def _story_path(story_id: str) -> Path:
    p = DATA / f"{story_id}.json"
    if not p.exists():
        raise ValueError(f"story '{story_id}' not found in {DATA}")
    return p


def tool_get_issue(args):
    return json.loads(_story_path(args["story_id"]).read_text(encoding="utf-8"))


def tool_update_issue(args):
    p = _story_path(args["story_id"])
    story = json.loads(p.read_text(encoding="utf-8"))
    story["state"] = args["state"]
    p.write_text(json.dumps(story, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "story_id": args["story_id"]}


def tool_set_subtask_status(args):
    p = _story_path(args["story_id"])
    story = json.loads(p.read_text(encoding="utf-8"))
    for s in story["state"].get("subtasks", []):
        if s["id"] == args["subtask_id"]:
            s["status"] = args["status"]
            if args.get("pr_url"):
                s["pr_url"] = args["pr_url"]
            p.write_text(json.dumps(story, indent=2) + "\n", encoding="utf-8")
            return {"ok": True, "subtask": s}
    raise ValueError(f"subtask '{args['subtask_id']}' not found")


DISPATCH = {
    "get_issue": tool_get_issue,
    "update_issue": tool_update_issue,
    "set_subtask_status": tool_set_subtask_status,
}


# ---------------------------------------------------------------- MCP plumbing
def reply(id_, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        msg["error"] = error
    else:
        msg["result"] = result
    sys.stdout.write(json.dumps(msg) + "\n")
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, id_, params = req.get("method"), req.get("id"), req.get("params") or {}

        if method == "initialize":
            reply(id_, {
                "protocolVersion": params.get("protocolVersion", PROTOCOL_FALLBACK),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "jira-ops", "version": "1.0.0"},
            })
        elif method in ("notifications/initialized", "initialized"):
            continue  # notification - no response
        elif method == "ping":
            reply(id_, {})
        elif method == "tools/list":
            reply(id_, {"tools": TOOLS})
        elif method == "tools/call":
            name, args = params.get("name"), params.get("arguments") or {}
            try:
                out = DISPATCH[name](args)
                reply(id_, {"content": [{"type": "text",
                                         "text": json.dumps(out, indent=2)}]})
            except Exception as ex:  # noqa: BLE001
                reply(id_, {"content": [{"type": "text", "text": f"ERROR: {ex}"}],
                            "isError": True})
        elif id_ is not None:
            reply(id_, error={"code": -32601, "message": f"unknown method {method}"})


if __name__ == "__main__":
    main()
