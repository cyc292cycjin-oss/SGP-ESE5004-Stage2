"""M10P supplement 01 item 5 (dynamic part; dry run only, never part of the package): with PYTHONPATH pointing here, every Python process of the
dry run records each attempt to open, list or stat a path
  RESEARCH  under <M10P_TRACE_REPO>/research/ (the folder left out of the code archive) - the question of item 5;
  LOCAL     under /mnt/ or /home/jin/ outside M10P_TRACE_ROOT (the dry-run folder) and the Python environment - for information: local files
            that would not exist on the instance.
One line per access, appended to M10P_TRACE_LOG: tag, kind (open / os.listdir / os.scandir / glob.glob / os.stat / os.lstat), absolute path, script.
Only records; changes no behaviour (os.stat / os.lstat are wrapped and call the originals)."""
import os
import sys

_repo, _log, _root = os.environ.get("M10P_TRACE_REPO"), os.environ.get("M10P_TRACE_LOG"), os.environ.get("M10P_TRACE_ROOT", "")
if _repo and _log:
    _abspath, _fspath, _open, _write, _close = os.path.abspath, os.fspath, os.open, os.write, os.close
    _research = {p.rstrip("/") + "/research" for p in (_abspath(_repo), os.path.realpath(_repo))}
    _skip = tuple(sorted({p.rstrip("/") + "/" for p in (_abspath(sys.prefix), _abspath(sys.base_prefix), _abspath(_root) if _root else "") if p not in ("", "/")}))
    _busy = [False]

    def _note(kind, p):
        if _busy[0] or isinstance(p, int):
            return
        try:
            s = _fspath(p)
            a = _abspath(os.fsdecode(s) if isinstance(s, bytes) else s)
        except Exception:
            return
        if any(a == r or a.startswith(r + "/") for r in _research):
            tag = "RESEARCH"
        elif a.startswith(("/mnt/", "/home/jin/")) and not (a + "/").startswith(_skip):
            tag = "LOCAL"
        else:
            return
        _busy[0] = True
        try:
            fd = _open(_log, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
            _write(fd, f"{tag}\t{kind}\t{a}\t{(getattr(sys, 'argv', None) or [''])[0]}\n".encode())
            _close(fd)
        except OSError:
            pass
        finally:
            _busy[0] = False

    def _hook(event, args):
        if event in ("open", "os.listdir", "os.scandir", "glob.glob") and args:
            _note(event, args[0])

    sys.addaudithook(_hook)
    _stat, _lstat = os.stat, os.lstat

    def stat(path, *a, **k):
        _note("os.stat", path)
        return _stat(path, *a, **k)

    def lstat(path, *a, **k):
        _note("os.lstat", path)
        return _lstat(path, *a, **k)

    os.stat, os.lstat = stat, lstat
