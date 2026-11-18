#!/usr/bin/env python3
"""Fast opencode usage record for the omarchy agents panel.

The stock collector parses the JSON body of every message ever written
(across both stores) to rebuild usage stats from scratch — minutes of CPU
on a 100 GB database. This replacement is incremental: a watermark file
remembers the last processed time_created, and the time_created index
makes each run cost milliseconds. Only today's stats and recentDays are
maintained; limits are left untouched (the stock record's limits data is
preserved verbatim).
"""
import datetime
import json
import os
import sqlite3

DB = os.path.expanduser("~/.local/share/opencode/opencode.db")
USAGE_DIR = os.path.expanduser("~/.local/state/omarchy/agents/usage")
REC = os.path.join(USAGE_DIR, "opencode.json")
WM = os.path.join(USAGE_DIR, ".opencode-fast-watermark")
WINDOW_DAYS = 30

try:
    now_ms = int(datetime.datetime.now().timestamp() * 1000)
    wm = None
    if os.path.exists(WM):
        try:
            wm = int(open(WM).read().strip())
        except ValueError:
            wm = None
    if wm is None or wm > now_ms:
        wm = now_ms - WINDOW_DAYS * 86400_000

    rec = {}
    if os.path.exists(REC):
        try:
            rec = json.load(open(REC))
        except Exception:
            rec = {}

    conn = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=5)

    # Subagent sessions' prompts are the model's, not typed — exclude like
    # the stock scanner does.
    try:
        children = {r[0] for r in conn.execute(
            "SELECT id FROM session_v2 WHERE parent_id IS NOT NULL")}
    except sqlite3.Error:
        children = set()

    per_day, prompts_by_day = {}, {}
    today_sessions, today_models = set(), {}
    today = datetime.date.today().isoformat()

    for sid, typ, tc, data in conn.execute(
        "SELECT session_id, type, time_created, data FROM session_message "
        "WHERE time_created > ? AND time_created <= ? ORDER BY time_created",
        (wm, now_ms),
    ):
        d = datetime.datetime.fromtimestamp(tc / 1000).date().isoformat()
        per_day[d] = per_day.get(d, 0) + 1
        if sid not in children and typ == "user":
            prompts_by_day[d] = prompts_by_day.get(d, 0) + 1
        if d == today:
            today_sessions.add(sid)
            if typ == "assistant" and data:
                try:
                    m = json.loads(data).get("model", {}).get("providerID")
                    if m:
                        today_models[m] = today_models.get(m, 0) + 1
                except Exception:
                    pass

    # Tokens live in step-finish parts. The part table has no time index,
    # so bound the scan by the sessions active since the watermark via the
    # session_id index (parts of a few recent sessions, not the whole table).
    today_tokens = 0
    try:
        for (data,) in conn.execute(
            "SELECT p.data FROM part p WHERE p.session_id IN ("
            "  SELECT DISTINCT session_id FROM session_message"
            "  WHERE time_created > ? AND time_created <= ?"
            ") AND json_extract(p.data,'$.type')='step-finish'",
            (wm, now_ms),
        ):
            try:
                t = json.loads(data).get("tokens") or {}
                today_tokens += sum(
                    t.get(k) or 0 for k in ("input", "output", "reasoning")
                )
            except Exception:
                pass
    except sqlite3.Error:
        pass
    conn.close()

    rec.update({
        "schemaVersion": rec.get("schemaVersion", 1),
        "id": "opencode",
        "name": "OpenCode",
        "updatedAt": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "ready": True,
        "hasLocalStats": True,
        "hasPromptStats": True,
        "todayPrompts": prompts_by_day.get(today, rec.get("todayPrompts", 0) if today not in prompts_by_day else 0) if today not in per_day else prompts_by_day.get(today, 0),
        "todaySessions": len(today_sessions) if per_day.get(today) else rec.get("todaySessions", 0),
        "todayTotalTokens": today_tokens if per_day.get(today) else rec.get("todayTotalTokens", 0),
        "todayTokensByModel": today_models if per_day.get(today) else rec.get("todayTokensByModel", {}),
    })
    # On days with new rows, prompts are fresh counts of today's typed prompts.
    if today in prompts_by_day or today in per_day:
        rec["todayPrompts"] = prompts_by_day.get(today, 0)
        rec["todaySessions"] = len(today_sessions)
        rec["todayTotalTokens"] = today_tokens
        rec["todayTokensByModel"] = today_models

    # recentDays: watermark guarantees each row is counted exactly once, so
    # new counts ADD onto whatever earlier runs recorded for those dates.
    rd = {e.get("date"): e for e in rec.get("recentDays", []) if e.get("date")}
    for d, c in per_day.items():
        e = rd.setdefault(d, {"date": d, "messageCount": 0})
        e["messageCount"] = e.get("messageCount", 0) + c
    rec["recentDays"] = sorted(rd.values(), key=lambda e: e["date"])[-WINDOW_DAYS:]

    os.makedirs(USAGE_DIR, exist_ok=True)
    json.dump(rec, open(REC, "w"), indent=2)
    open(WM, "w").write(str(now_ms))
except Exception:
    # Never break the panel: a failed fast path must stay silent.
    pass
