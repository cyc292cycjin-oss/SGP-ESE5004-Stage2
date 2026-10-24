"""M10P supplement 01 item 5 (static part): does any code that runs on the instance read the top-level research/ folder of the repository?

Runtime = the Python modules the package scripts start on the instance (run_batch3.sh, preflight.sh, pack_results.sh, env/env_check.py), and
every module of scripts_project/ they import (import closure over scripts_project/ and scripts_project/v5/, imports inside functions included).
For every module of the closure the script lists
  * path literals that start with research/ (relative to the repository root; configs/research/, tests/research/, research_inputs/ excluded);
  * path joins with the segment "research" (ROOT / "research", os.path.join(..., "research", ...), joinpath);
  * absolute paths (they do not exist on the instance either);
  * dynamic imports / exec (importlib, __import__, runpy, exec) that the closure cannot follow;
  * references to configs/ files and the research/ path values inside configs/ (a config value could point into research/).
Every hit is then classified by hand in the evidence JSON (how the value is used: opened at run time or only written as a label).
    python m10p_s01_static_research.py <repo> <package scripts dir> <out json>
Reads files only; no solve."""
import ast
import json
import re
import sys
from pathlib import Path

ENTRIES = ["s2_solve", "l23_violation_analysis", "s4o_c1_precision", "m12_allocation", "m12_rhs_audit", "m08a_variants", "v5/gates_v6", "m10_batch3_summary"]
REL = re.compile(r"(?:^|[\s\"'=:(,])research/")          # research/... relative to the repository root
ABS = re.compile(r"^(/home/|/mnt/|/root/|[A-Za-z]:[\\/]|~/)")
DYN = ("importlib", "__import__", "runpy", "exec(", "import_module")


def resolve(sp: Path, name: str, here: Path) -> Path | None:
    parts = name.split(".")
    for root in (sp, sp / "v5", here.parent):
        for cand in (root.joinpath(*parts).with_suffix(".py"), root.joinpath(*parts) / "__init__.py"):
            if cand.exists():
                return cand
    return None


def closure(sp: Path) -> dict:
    seen, todo = {}, [sp / (e + ".py") for e in ENTRIES]
    while todo:
        f = todo.pop()
        if f in seen or not f.exists():
            continue
        tree = ast.parse(f.read_text(encoding="utf-8"))
        deps = []
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:   # relative import inside a package folder
                    base = f.parent
                    names = [(node.module or "")] if node.module else [a.name for a in node.names]
                    for n in names:
                        c = base.joinpath(*n.split(".")).with_suffix(".py") if n else None
                        if c and c.exists():
                            deps.append(c)
                    continue
                if node.module:
                    names = [node.module] + [node.module + "." + a.name for a in node.names]
            for n in names:
                c = resolve(sp, n, f)
                if c is not None:
                    deps.append(c)
        seen[f] = sorted(set(deps))
        todo += [d for d in deps if d not in seen]
    return seen


def strings(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            yield node.lineno, node.value


def joins(tree):
    """Path joins with a literal segment research / research/...: a / "research", os.path.join(.., "research"), .joinpath("research")."""
    def seg(x):
        return isinstance(x, ast.Constant) and isinstance(x.value, str) and (x.value.strip("/") == "research" or x.value.startswith("research/"))
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div) and (seg(node.left) or seg(node.right)):
            yield node.lineno, ast.unparse(node)
        elif isinstance(node, ast.Call) and any(seg(a) for a in node.args):
            fn = ast.unparse(node.func)
            if fn.endswith(("join", "joinpath", "Path")):
                yield node.lineno, ast.unparse(node)[:200]


def main(repo: Path, pkg: Path, out: Path):
    sp = repo / "scripts_project"
    cl = closure(sp)
    mods = sorted(str(p.relative_to(repo)) for p in cl)
    hits = []
    for f in sorted(cl):
        src = f.read_text(encoding="utf-8"); lines = src.splitlines(); tree = ast.parse(src); rel = str(f.relative_to(repo))
        for ln, s in strings(tree):
            if REL.search(s) and not re.search(r"(configs|tests)/research/", s.split("research/")[0] + "research/"):
                hits.append(dict(module=rel, line=ln, kind="literal_research_path", value=s[:240], source=lines[ln - 1].strip()[:240]))
            elif ABS.match(s):
                hits.append(dict(module=rel, line=ln, kind="absolute_path", value=s[:240], source=lines[ln - 1].strip()[:240]))
        for ln, expr in joins(tree):
            hits.append(dict(module=rel, line=ln, kind="path_join_research", value=expr, source=lines[ln - 1].strip()[:240]))
        for i, ln in enumerate(lines, 1):
            if any(k in ln for k in DYN) and not ln.lstrip().startswith("#"):
                hits.append(dict(module=rel, line=i, kind="dynamic_import_or_exec", value=ln.strip()[:240], source=ln.strip()[:240]))
    cfg = []
    for f in sorted((repo / "configs").rglob("*")):
        if f.is_file() and f.suffix in (".yaml", ".yml", ".json"):
            for i, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if REL.search(ln) and not re.search(r"(configs|tests)/research/", ln):
                    cfg.append(dict(file=str(f.relative_to(repo)), line=i, text=ln.strip()[:240]))
    cfg_names = sorted({c["file"] for c in cfg})
    cfg_refs = [dict(config=c, used_by=[m for m in mods if Path(c).name in (repo / m).read_text(encoding="utf-8")]) for c in cfg_names]
    shell = []
    for f in sorted(list(pkg.glob("*.sh")) + list((pkg / "env").glob("*"))):
        if f.is_file():
            for i, ln in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if re.search(r"(REPO|repo)/research|\bresearch/0", ln):
                    shell.append(dict(file=f.name, line=i, text=ln.strip()[:240]))
    res = dict(script="research/06_scope_redesign/p1_m10p_20261022/scripts/m10p_s01_static_research.py", repo=str(repo),
               entries=[f"scripts_project/{e}.py" for e in ENTRIES], closure_modules=mods, closure_size=len(mods), hits=hits,
               hit_counts={k: sum(h["kind"] == k for h in hits) for k in ("literal_research_path", "path_join_research", "absolute_path", "dynamic_import_or_exec")},
               config_research_values=cfg, config_files_with_research_values_used_by_closure=cfg_refs, package_shell_hits=shell, solver_runs=0)
    out.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(dict(closure=len(mods), hit_counts=res["hit_counts"], config_values=len(cfg), config_used=[c for c in cfg_refs if c["used_by"]], shell=len(shell))))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]))
