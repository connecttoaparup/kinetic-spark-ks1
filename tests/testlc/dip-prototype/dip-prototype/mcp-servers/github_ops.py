#!/usr/bin/env python3
"""github MCP server (local stdio transport).

Same tool contract as the production deployment (which fronts github.com):
  - create_pull_request(repo, head_branch, title, body?)  -> PR number
  - get_pull_request(repo, number)                         -> status open|merged
  - merge_pull_request(repo, number)                       -> real `git merge --no-ff` into main
  - list_pull_requests(repo)

Locally it operates on the REAL git repositories under repos/ - branches and
merges are genuine git operations, and PR metadata lives in
mcp-servers/data/prs.json. The supervisor/engineer agents use the identical
tool surface in production; only the transport (dev stdio vs prod HTTP)
differs, exactly as documented in the platform guide.

Protocol: MCP over stdio - newline-delimited JSON-RPC 2.0. Stdlib only.
"""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
REPOS = ROOT / "repos"
PR_DB = HERE / "data" / "prs.json"
PROTOCOL_FALLBACK = "2024-11-05"
GIT_ID = ["-c", "user.name=dip-github-mcp", "-c", "user.email=dip@local"]

TOOLS = [
    {"name": "create_pull_request",
     "description": "Open a PR from head_branch into main for a repo under repos/. "
                    "The branch must already exist with commits.",
     "inputSchema": {"type": "object", "properties": {
         "repo": {"type": "string"}, "head_branch": {"type": "string"},
         "title": {"type": "string"}, "body": {"type": "string"}},
         "required": ["repo", "head_branch", "title"]}},
    {"name": "get_pull_request",
     "description": "Get a PR's status (open|merged), title, and branch.",
     "inputSchema": {"type": "object", "properties": {
         "repo": {"type": "string"}, "number": {"type": "integer"}},
         "required": ["repo", "number"]}},
    {"name": "merge_pull_request",
     "description": "Merge an open PR: real `git merge --no-ff` of head_branch "
                    "into main. Call only after human (CODEOWNERS) approval.",
     "inputSchema": {"type": "object", "properties": {
         "repo": {"type": "string"}, "number": {"type": "integer"}},
         "required": ["repo", "number"]}},
    {"name": "list_pull_requests",
     "description": "List all PRs for a repo with statuses.",
     "inputSchema": {"type": "object", "properties": {
         "repo": {"type": "string"}}, "required": ["repo"]}},
]


def _db():
    return json.loads(PR_DB.read_text(encoding="utf-8"))


def _save(db):
    PR_DB.write_text(json.dumps(db, indent=2) + "\n", encoding="utf-8")


def _git(repo: str, *args, check=True):
    cwd = REPOS / repo
    if not cwd.exists():
        raise ValueError(f"repo '{repo}' not found under repos/")
    p = subprocess.run(["git", *GIT_ID, *args], cwd=cwd,
                       capture_output=True, text=True)
    if check and p.returncode != 0:
        raise ValueError(f"git {' '.join(args)} failed: {p.stderr.strip()}")
    return p.stdout.strip()


def tool_create_pr(args):
    repo, branch = args["repo"], args["head_branch"]
    branches = _git(repo, "branch", "--list", branch)
    if not branches:
        raise ValueError(f"branch '{branch}' does not exist in {repo} - "
                         f"commit your changes on it first")
    db = _db()
    rec = db.setdefault(repo, {"next": 1, "prs": {}})
    n = rec["next"]
    rec["next"] += 1
    rec["prs"][str(n)] = {"number": n, "title": args["title"],
                          "body": args.get("body", ""), "head_branch": branch,
                          "base": "main", "status": "open"}
    _save(db)
    return {"number": n, "url": f"{repo}#{n}", "status": "open"}


def tool_get_pr(args):
    pr = _db().get(args["repo"], {}).get("prs", {}).get(str(args["number"]))
    if not pr:
        raise ValueError(f"PR {args['repo']}#{args['number']} not found")
    return pr


def tool_merge_pr(args):
    repo, n = args["repo"], str(args["number"])
    db = _db()
    pr = db.get(repo, {}).get("prs", {}).get(n)
    if not pr:
        raise ValueError(f"PR {repo}#{n} not found")
    if pr["status"] == "merged":
        return pr
    _git(repo, "checkout", "main")
    _git(repo, "merge", "--no-ff", pr["head_branch"],
         "-m", f"Merge PR #{n}: {pr['title']}")
    pr["status"] = "merged"
    _save(db)
    return pr


def tool_list_prs(args):
    return list(_db().get(args["repo"], {}).get("prs", {}).values())


DISPATCH = {"create_pull_request": tool_create_pr,
            "get_pull_request": tool_get_pr,
            "merge_pull_request": tool_merge_pr,
            "list_pull_requests": tool_list_prs}


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
            reply(id_, {"protocolVersion": params.get("protocolVersion",
                                                      PROTOCOL_FALLBACK),
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "github", "version": "1.0.0"}})
        elif method in ("notifications/initialized", "initialized"):
            continue
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
