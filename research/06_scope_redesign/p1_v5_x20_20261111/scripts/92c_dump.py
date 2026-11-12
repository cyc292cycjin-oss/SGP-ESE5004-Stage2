"""只读：按时间戳从 transcript 取出 Windows-Python 命令全文，存到 cache/winpy_rerun/commands/<序号>.txt。用法：python 92c_dump.py <时间戳> ..."""
import json
import sys
from pathlib import Path

T = Path("/mnt/c/Users/20122/.claude/projects/D--ResearchWorkspaces")
O = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111/cache/winpy_rerun/commands"); O.mkdir(parents=True, exist_ok=True)
want = set(sys.argv[1:])
for fn in ("32f6eff3-3b72-4ccd-9c5e-99dd868a42db.jsonl", "b70f44c4-68a7-45c3-96fa-db9d85fdb515.jsonl"):
    for line in (T / fn).open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:   # noqa: BLE001
            continue
        if o.get("timestamp") not in want:
            continue
        for c in (o.get("message") or {}).get("content") or []:
            if isinstance(c, dict) and c.get("type") == "tool_use":
                cmd = (c.get("input") or {}).get("command", "")
                p = O / (o["timestamp"].replace(":", "") + ".txt"); p.write_text(cmd, encoding="utf-8"); print(p.name, len(cmd))
