"""DFX v3 F0: aggregate the module recorder output and classify scripts_project/ (read-only; writes CODE_MAP_DATA.json + CODE_MAP_TABLE.csv).

Inputs: results_project/dfx_v3/f0_trace/modules.jsonl (sitecustomize records of the v1 build, the LP build and the 56-snapshot post-processing
chain), the batch / package shell scripts (python scripts they invoke + AST import closure), DATA_REGISTRY.csv derivation_script column, the
tests folder (imports), the data-chain script list of m08b_data.sh. Run inside the worktree:
    /home/jin/miniforge3/envs/pypsa-earth/bin/python /home/jin/dfx3/f0_codemap.py
"""
import ast
import csv
import json
import re
from pathlib import Path

WT = Path("/home/jin/wt_dfx_v3_20261026")
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model")
TR = MAIN / "results_project/dfx_v3/f0_trace/modules.jsonl"
OUT = WT / "research/06_scope_redesign/p1_dfx_20261026"
SP = WT / "scripts_project"


def rel(p: str) -> str:
    p = p.replace("\\", "/")
    i = p.find("scripts_project/")
    return p[i:] if i >= 0 else p


def closure(start: list[str]) -> set[str]:
    have = {p.relative_to(WT).as_posix(): p for p in SP.rglob("*.py")}
    byname = {}
    for k in have:
        byname.setdefault(Path(k).stem, []).append(k)
    seen, todo = set(), list(start)
    while todo:
        m = todo.pop()
        if m in seen or m not in have:
            continue
        seen.add(m)
        try:
            tree = ast.parse(have[m].read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            for n in names:
                stem = n.split(".")[0]
                for k in byname.get(stem, []):
                    todo.append(k)
    return seen


# ---- 1. dynamic traces by tag
tags = {}
for line in TR.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    r = json.loads(line)
    t = r.get("tag") or Path(r["argv"][0]).name
    tags.setdefault(t, set()).update(rel(m) for m in r["modules"])
    if r["argv"]:   # the entry script itself (sys.modules['__main__'] is recorded under its module name, not its file)
        entry = r["argv"][0] if r["argv"][0].startswith("/") else str(Path(r["cwd"]) / r["argv"][0])
        if "scripts_project" in entry.replace("\\", "/"):
            tags[t].add(rel(entry))
groups = {"build": [t for t in tags if t.startswith("build_")], "solve": [t for t in tags if t.startswith("solve_")],
          "post": [t for t in tags if t.startswith("post_")], "variants": [t for t in tags if t.startswith("variants")],
          "data_chain": [t for t in tags if t.startswith("data_chain_")]}
dyn = {g: sorted(set().union(*[tags[t] for t in ts])) if ts else [] for g, ts in groups.items()}
# ---- 2. batch / package scripts: python scripts invoked by the shell scripts + import closure
SH = {"run_batch3.sh": WT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package/run_batch3.sh", "run_batch4.sh": WT / "research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/run_batch4.sh",
      "preflight_b3.sh": WT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package/preflight.sh", "preflight_b4.sh": WT / "research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/preflight.sh",
      "pack_results.sh": WT / "research/06_scope_redesign/p1_m10p_20261022/cloud_package/pack_results.sh", "make_package_b4.sh": WT / "research/06_scope_redesign/p1_b4p_20261026/cloud_package_b4/make_package.sh",
      "m08a_run_batch.sh": SP / "m08a_run_batch.sh"}
batch_refs = {}
for name, p in SH.items():
    if not p.exists():
        batch_refs[name] = ["MISSING"]; continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    refs = sorted(set(re.findall(r"scripts_project/([A-Za-z0-9_/]+\.py)", txt)))
    batch_refs[name] = [f"scripts_project/{r}" for r in refs]
batch_start = sorted({r for v in batch_refs.values() for r in v if r != "MISSING"})
batch_closure = sorted(closure(batch_start))
# data chain (M08b m08b_data.sh / m08b_registry.sh + DFX)
data_chain_start = [f"scripts_project/{s}" for s in ("m08b_demand.py", "m08b_heat_bands.py", "s3_0_industry.py", "s2b_feedstock.py", "s2_0_process_emissions.py", "m08b_data.py", "d1_registry.py")]
data_chain_closure = sorted(closure(data_chain_start))
# ---- 3. registry derivation scripts, tests imports, docstrings
reg_scripts = {}
with open(WT / "research_inputs/registry_v5/DATA_REGISTRY.csv", newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        for s in re.findall(r"scripts_project/[A-Za-z0-9_/]+\.py", r.get("derivation_script", "") + " " + r.get("source_locator", "")):
            reg_scripts.setdefault(s, 0)
            reg_scripts[s] += 1
test_imports = {}
for t in sorted((WT / "tests").rglob("test_*.py")):
    txt = t.read_text(encoding="utf-8", errors="replace")
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
        for n in names:
            stem = n.split(".")[0]
            for cand in (SP / f"{stem}.py", SP / "v5" / f"{stem}.py"):
                if cand.exists():
                    test_imports.setdefault(cand.relative_to(WT).as_posix(), set()).add(t.relative_to(WT).as_posix())
    for s in re.findall(r"scripts_project/[A-Za-z0-9_/]+\.(?:py|sh)", txt):
        test_imports.setdefault(s, set()).add(t.relative_to(WT).as_posix())
rows = []
for p in sorted(SP.rglob("*")):
    if not p.is_file() or p.suffix not in (".py", ".sh") or "__pycache__" in p.parts:
        continue
    k = p.relative_to(WT).as_posix()
    txt = p.read_text(encoding="utf-8", errors="replace")
    doc = ""
    if p.suffix == ".py":
        try:
            doc = (ast.get_docstring(ast.parse(txt)) or "").strip().splitlines()[0] if ast.get_docstring(ast.parse(txt)) else ""
        except SyntaxError:
            doc = "(syntax error)"
    else:
        for line in txt.splitlines()[1:6]:
            if line.startswith("#") and len(line) > 3:
                doc = line.lstrip("# ").strip(); break
    rows.append(dict(path=k, bytes=p.stat().st_size, lines=txt.count("\n") + 1, doc=doc[:220],
                     in_build=k in dyn["build"], in_solve=k in dyn["solve"], in_post=k in dyn["post"], in_variants=k in dyn["variants"], in_data_chain_executed=k in dyn["data_chain"],
                     in_batch_shell=k in batch_start, in_batch_closure=k in batch_closure, in_data_chain=k in data_chain_closure,
                     registry_rows=reg_scripts.get(k, 0), tests=";".join(sorted(test_imports.get(k, [])))))
with open(OUT / "CODE_MAP_TABLE.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
json.dump(dict(dynamic_by_tag={t: sorted(v) for t, v in tags.items()}, dynamic=dyn, batch_shell_refs=batch_refs, batch_closure=batch_closure,
               data_chain_start=data_chain_start, data_chain_closure=data_chain_closure, counts=dict(scripts=len(rows), build=len(dyn["build"]), solve=len(dyn["solve"]),
               post=len(dyn["post"]), data_chain_executed=len(dyn["data_chain"]), batch_closure=len(batch_closure), data_chain=len(data_chain_closure)),
               executed_union=sorted(set(dyn["build"]) | set(dyn["solve"]) | set(dyn["post"]) | set(dyn["variants"]) | set(dyn["data_chain"]) | set(batch_closure))),
          open(OUT / "CODE_MAP_DATA.json", "w"), indent=1)
print(json.dumps({k: len(v) for k, v in dyn.items()}), "batch", len(batch_closure), "data_chain", len(data_chain_closure), "scripts", len(rows))
print("build:", dyn["build"])
print("solve:", dyn["solve"])
print("post:", dyn["post"])
print("batch_shell:", batch_start)
