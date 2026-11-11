#!/usr/bin/env python3
"""Devin's session (sessions.db) as a Claude-Code-style JSONL log, so Shepherdr's chat can read it.

Usage: devin-chat.py <session-id>
Writes $HERDR_APP_HOME/data/devin-chat/<session-id>.jsonl (only when it changed; earlier lines never change,
the chat reads it by byte offset) and prints its path, or "pending" when the session has no messages yet.
"""
import json, os, sqlite3, sys

DB = os.environ.get("DEVIN_DATA_HOME", os.path.expanduser("~/.local/share/devin")) + "/cli/sessions.db"
APP = os.environ.get("HERDR_APP_HOME", os.path.expanduser("~/.config/herdr-app"))
OUT = os.path.join(APP, "data", "devin-chat")

def first(a, *keys):
    for k in keys:
        if isinstance(a, dict) and a.get(k) not in (None, ""):
            return a[k]
    return None

# Devin tool -> the Claude Code tool the chat already knows how to word.
def tool(name, a):
    a = a if isinstance(a, dict) else {}
    path = first(a, "file_path", "path", "file", "filename")
    if name in ("exec", "shell_command"):
        return "Bash", {**a, "command": first(a, "command", "cmd") or "", "description": a.get("description")}
    if name == "read": return "Read", {**a, "file_path": path}
    if name in ("edit", "apply_patch", "notebook_edit"): return "Edit", {**a, "file_path": path}
    if name == "write": return "Write", {**a, "file_path": path}
    if name == "grep": return "Grep", {**a, "pattern": first(a, "pattern", "query", "regex")}
    if name == "find_file_by_name": return "Glob", {**a, "pattern": first(a, "pattern", "name", "query")}
    if name == "web_search": return "WebSearch", {**a, "query": first(a, "query", "q")}
    if name == "webfetch": return "WebFetch", {**a, "url": first(a, "url")}
    if name == "run_subagent":
        return "Task", {**a, "description": first(a, "description", "task", "prompt", "profile") or "a helper"}
    if name in ("todo_write", "update_plan"): return "TodoWrite", {**a, "todos": a.get("todos") or []}
    return name, a

def lines(con, sid):
    seen = set()
    for (raw,) in con.execute("select chat_message from message_nodes where session_id=? order by node_id", (sid,)):
        try:
            m = json.loads(raw)
        except ValueError:
            continue
        mid = m.get("message_id")
        if mid in seen or m.get("role") not in ("user", "assistant", "tool"):
            continue
        seen.add(mid)
        meta = m.get("metadata") or {}
        base = {"isSidechain": False, "timestamp": meta.get("created_at"), "sessionId": sid}
        role, content = m["role"], m.get("content")
        if role == "user":
            if not isinstance(content, str) or not content.strip():
                continue
            yield {**base, "type": "user", "message": {"role": "user", "content": content}, "uuid": mid}
        elif role == "tool":
            yield {**base, "type": "user", "uuid": mid, "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": m.get("tool_call_id"), "content": content if isinstance(content, str) else json.dumps(content)}]}}
        else:
            blocks = []
            think = (m.get("thinking") or {}).get("thinking")
            if think: blocks.append({"type": "thinking", "thinking": think, "signature": ""})
            if isinstance(content, str) and content.strip(): blocks.append({"type": "text", "text": content})
            for c in m.get("tool_calls") or []:
                n, inp = tool(c.get("name", ""), c.get("arguments"))
                blocks.append({"type": "tool_use", "id": c.get("id"), "name": n, "input": inp})
            if not blocks:
                continue
            met = meta.get("metrics") or {}
            yield {**base, "type": "assistant", "uuid": mid, "message": {
                "id": meta.get("request_id") or mid, "role": "assistant", "model": meta.get("generation_model") or "devin",
                "content": blocks, "usage": {"input_tokens": met.get("input_tokens") or 0, "output_tokens": met.get("output_tokens") or 0}}}

def main():
    sid = sys.argv[1]
    if "/" in sid or not sid:
        sys.exit("bad session id")
    try:
        con = sqlite3.connect("file:%s?mode=ro" % DB, uri=True, timeout=2)
        # key order matters: the chat's reader looks for "isSidechain":false then "type":"user","message" / "type":"assistant","uuid"
        out = "".join(json.dumps({k: l[k] for k in ("isSidechain", "type", "uuid", "message", "timestamp", "sessionId") if k in l} if l["type"] == "assistant"
                                 else {k: l[k] for k in ("isSidechain", "type", "message", "uuid", "timestamp", "sessionId") if k in l},
                                 ensure_ascii=False, separators=(",", ":")) + "\n" for l in lines(con, sid))
    except sqlite3.Error:
        out = ""
    if not out:
        print("pending"); return
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, sid + ".jsonl")
    try:
        if open(path, encoding="utf-8").read() == out:
            print(path); return
    except OSError:
        pass
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: f.write(out)
    os.replace(tmp, path)
    print(path)

main()
