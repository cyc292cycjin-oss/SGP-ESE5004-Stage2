"""S4O-4 package checks (run by make_package.sh from the repository root; read only except the files it writes into the dist folder).

  build-inputs <build_sha> <head_sha>
      Every change under scripts_project / configs / scripts / research_inputs between the network build commit and HEAD must leave the built
      networks unchanged. Allowed, each with its check:
        * summary / evidence / comparison / C1 scripts and tests (path rule, as in S4M plus s4o_* and l23_*);
        * scripts_project/s2_solve.py - the solve driver; no build module imports it (checked: none of the modules imported by the build entry
          scripts_project/s2_network.py, transitively within scripts_project, imports s2_solve);
        * configs/research/baseline.yaml - only research.solver may differ (parsed YAML of both commits with research.solver removed are equal);
        * research_inputs/registry_v5 DATA_REGISTRY.csv / DATA_PENDING_LIST.csv / D1_EVIDENCE.json / fragments/*.csv and scripts_project/d1_registry.py
          - the registry may only GAIN rows (every row of the build commit unchanged; the build reads rows by param_id);
      anything else -> refuse (rebuild the networks at HEAD first). Prints the classification as JSON.
  compare-networks <dist> <reference SHA256SUMS>
      The files under networks/ of the new package must have the same SHA256 as in the reference package (S4M f50c8850); exit 1 otherwise.
  delta <dist> <reference SHA256SUMS> <reference commit>
      PACKAGE_DELTA.json: changed / added / removed / unchanged files against the reference package, with bytes; the upload list = changed + added.
"""
from __future__ import annotations

import ast
import csv
import io
import json
import os
import re
import subprocess
import sys

ALLOW = re.compile(r"^scripts_project/(s4k_[3-5]_[a-z_]+|s4l_[0-9]_[a-z_]+|s4m_[2-9]_[a-z_]+|s4n_[a-z0-9_]+|s4o_[a-z0-9_]+|l23_[a-z0-9_]+)\.py$|^tests/")
REGISTRY = re.compile(r"^research_inputs/registry_v5/(DATA_REGISTRY\.csv|DATA_PENDING_LIST\.csv|D1_EVIDENCE\.json|fragments/[a-z0-9_]+\.csv)$|^scripts_project/d1_registry\.py$")


def git(*a) -> str:
    return subprocess.run(["git", *a], check=True, capture_output=True, text=True).stdout


def build_imports(sha: str, entry: str = "scripts_project/s2_network.py") -> set[str]:
    """module names (scripts_project/*.py) reachable from the build entry by import statements at commit sha."""
    have = {p[len("scripts_project/"):-3] for p in git("ls-tree", "-r", "--name-only", sha, "scripts_project").split() if p.endswith(".py") and p.count("/") == 1}
    seen, todo = set(), [entry[len("scripts_project/"):-3]]
    while todo:
        mod = todo.pop()
        if mod in seen or mod not in have:
            continue
        seen.add(mod)
        for node in ast.walk(ast.parse(git("show", f"{sha}:scripts_project/{mod}.py"))):
            names = [a.name for a in node.names] if isinstance(node, ast.Import) else ([node.module] if isinstance(node, ast.ImportFrom) and node.module else [])
            todo += [n.split(".")[0] for n in names]
    return seen


def registry_additive(b: str, h: str, path: str) -> bool:
    if path.endswith(".csv") and "fragments/" not in path:
        old = list(csv.reader(io.StringIO(git("show", f"{b}:{path}"))))
        new = {tuple(r) for r in csv.reader(io.StringIO(git("show", f"{h}:{path}")))}
        return all(tuple(r) in new for r in old)
    return True   # fragments, D1_EVIDENCE.json, d1_registry.py: covered by the DATA_REGISTRY.csv check (the assembled file the build reads)


def build_inputs(b: str, h: str) -> int:
    import yaml
    changed = [p for p in git("diff", "--name-only", b, h, "--", "scripts_project", "configs", "scripts", "research_inputs").split() if p]
    out = dict(build_commit=b, head=h, allowed_by_path=[], solve_driver=[], config_solver_only=[], registry_additive=[], refused=[])
    imports = build_imports(h)
    reg_ok = registry_additive(b, h, "research_inputs/registry_v5/DATA_REGISTRY.csv")
    for p in changed:
        if ALLOW.match(p):
            out["allowed_by_path"].append(p)
        elif p == "scripts_project/s2_solve.py" and "s2_solve" not in imports:
            out["solve_driver"].append(p)
        elif p == "configs/research/baseline.yaml":
            cb, ch = yaml.safe_load(git("show", f"{b}:{p}")), yaml.safe_load(git("show", f"{h}:{p}"))
            cb["research"].pop("solver", None); ch["research"].pop("solver", None)
            (out["config_solver_only"] if cb == ch else out["refused"]).append(p)
        elif REGISTRY.match(p) and reg_ok and registry_additive(b, h, p):
            out["registry_additive"].append(p)
        else:
            out["refused"].append(p)
    out["build_modules_checked"] = sorted(imports)
    print(json.dumps(out, indent=1))
    return 1 if out["refused"] else 0


def sums(path: str) -> dict:
    d = {}
    for line in open(path):
        s, p = line.split(maxsplit=1); d[p.strip()] = s
    return d


def compare_networks(dist: str, ref: str) -> int:
    new, old = sums(os.path.join(dist, "SHA256SUMS")), sums(ref)
    nets = sorted(p for p in set(new) | set(old) if p.startswith("networks/"))
    rows = [dict(path=p, new=new.get(p), reference=old.get(p), same=(new.get(p) == old.get(p) and new.get(p) is not None)) for p in nets]
    res = dict(reference=ref, files=rows, all_same=all(r["same"] for r in rows))
    json.dump(res, open(os.path.join(dist, "NETWORKS_VS_REFERENCE.json"), "w"), indent=1)
    print(json.dumps(dict(all_same=res["all_same"], files=len(rows), differing=[r["path"] for r in rows if not r["same"]])))
    return 0 if res["all_same"] else 1


def delta(dist: str, ref: str, ref_commit: str) -> int:
    new, old = sums(os.path.join(dist, "SHA256SUMS")), sums(ref)
    size = lambda p: os.path.getsize(os.path.join(dist, p))
    changed = sorted(p for p in new if p in old and new[p] != old[p]); added = sorted(p for p in new if p not in old)
    removed = sorted(p for p in old if p not in new); same = sorted(p for p in new if p in old and new[p] == old[p])
    upload = changed + added + ["SHA256SUMS", "PACKAGE_MANIFEST.json"]
    res = dict(reference_package=dict(commit=ref_commit, sha256sums=ref), new_commit=open(os.path.join(dist, "COMMIT")).read().strip(),
               changed=[dict(path=p, bytes=size(p), sha256=new[p], reference_sha256=old[p]) for p in changed],
               added=[dict(path=p, bytes=size(p), sha256=new[p]) for p in added], removed=removed,
               unchanged=[dict(path=p, bytes=size(p), sha256=new[p]) for p in same],
               upload=dict(files=upload + ["PACKAGE_DELTA.json"], bytes=sum(size(p) for p in upload), note="upload the listed files with ONE rsync stream into the existing package "
                           "folder (no parallel streams, never interrupt a --partial transfer); the files under 'removed' stay on the instance (no deletion; they are not in the new "
                           "SHA256SUMS); then the full sha256sum -c SHA256SUMS (every file) and COMMIT; preflight.sh unpacks code_<COMMIT8>.tar.gz and moves an older ./repo aside "
                           "(repo_prev_<commit8>) instead of reusing it"),
               unchanged_bytes=sum(size(p) for p in same))
    json.dump(res, open(os.path.join(dist, "PACKAGE_DELTA.json"), "w"), indent=1)
    print(json.dumps(dict(changed=changed, added=added, removed=removed, unchanged=len(same), upload_bytes=res["upload"]["bytes"], unchanged_bytes=res["unchanged_bytes"])))
    return 0


if __name__ == "__main__":
    cmd, *args = sys.argv[1:]
    sys.exit(dict(**{"build-inputs": build_inputs, "compare-networks": compare_networks, "delta": delta})[cmd](*args))
