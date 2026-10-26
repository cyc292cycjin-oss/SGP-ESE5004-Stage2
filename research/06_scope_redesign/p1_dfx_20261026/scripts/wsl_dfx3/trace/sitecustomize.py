"""DFX v3 F0 module recorder: at interpreter exit, append the scripts_project modules found in sys.modules to DFX_TRACE_OUT (JSON lines).

Activated through PYTHONPATH=/home/jin/dfx3/trace (sitecustomize is imported by every interpreter start, child processes included). Read-only:
it never changes the behaviour of the traced program.
"""
import atexit
import json
import os
import sys
import time


def _dump():
    out = os.environ.get("DFX_TRACE_OUT")
    if not out:
        return
    mods = []
    for name, m in list(sys.modules.items()):
        f = getattr(m, "__file__", None)
        if f and "scripts_project" in f.replace("\\", "/"):
            mods.append(dict(module=name, file=f))
    rec = dict(argv=sys.argv, pid=os.getpid(), ppid=os.getppid(), cwd=os.getcwd(), t=time.time(), tag=os.environ.get("DFX_TRACE_TAG", ""),
               modules=sorted({m["file"] for m in mods}))
    try:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")
    except OSError:
        pass


atexit.register(_dump)
