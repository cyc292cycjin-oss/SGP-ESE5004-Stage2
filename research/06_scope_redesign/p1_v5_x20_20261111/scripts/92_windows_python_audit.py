"""环境一致性核查（用户 11-12 要求）：从本会话的两份 transcript（压缩前 32f6eff3…、压缩后 b70f44c4…）中列出所有调用 Windows 侧 Python
（miniconda3 的 python.exe，含 envs\\calliope07）的命令，并按命令文本找出它写的文件（to_csv / write_text / json.dump / open(…, "w") / to_netcdf 等）。
只读 transcript；输出 evidence/WINDOWS_PYTHON_COMMANDS.csv（逐条：会话、时间、工具、解释器、是否写文件、写的文件、命令前 400 字）。
用法：python 92_windows_python_audit.py"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

T = Path("/mnt/c/Users/20122/.claude/projects/D--ResearchWorkspaces")
FILES = ["32f6eff3-3b72-4ccd-9c5e-99dd868a42db.jsonl", "b70f44c4-68a7-45c3-96fa-db9d85fdb515.jsonl"]
D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v5_x20_20261111")
PY = re.compile(r"miniconda3[/\\]+(envs[/\\]+[A-Za-z0-9_]+[/\\]+)?python(\.exe)?", re.I)
WRITES = re.compile(r"""(to_csv|to_netcdf|write_text|write_bytes|json\.dump|to_parquet|savefig|open\()\s*\(?\s*(?:[A-Za-z_]+\s*/\s*)?(f?["'][^"']+["'])""")


def commands(fn: Path):
    for line in fn.open(encoding="utf-8", errors="replace"):
        try:
            o = json.loads(line)
        except Exception:   # noqa: BLE001
            continue
        msg = o.get("message") or {}
        for c in (msg.get("content") or []) if isinstance(msg.get("content"), list) else []:
            if c.get("type") == "tool_use" and c.get("name") in ("Bash", "PowerShell"):
                cmd = (c.get("input") or {}).get("command", "")
                if PY.search(cmd):
                    yield o.get("timestamp"), c.get("name"), cmd


rows = []
for f in FILES:
    for ts, tool, cmd in commands(T / f):
        interp = sorted(set(m.group(0) for m in PY.finditer(cmd)))
        w = [m.group(2).strip("f").strip("'\"") for m in WRITES.finditer(cmd) if m.group(1) != "open(" or re.search(r"""open\([^)]*["']w""", cmd)]
        w = [x for x in w if not x.startswith(("/c/Users", "C:")) or True]
        rows.append(dict(session=f[:8], timestamp=ts, tool=tool, interpreter=";".join(interp), writes_files=bool(w), written=";".join(sorted(set(w))), command=cmd[:400].replace("\n", " | ")))
t = pd.DataFrame(rows)
t.to_csv(D / "evidence/WINDOWS_PYTHON_COMMANDS.csv", index=False, lineterminator="\n")
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 120)
print("commands", len(t), "with writes", int(t.writes_files.sum()))
print(t[["session", "timestamp", "interpreter", "written"]].to_string())
