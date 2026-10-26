"""DFX v3 P6: classify the pattern hits of the leak scan by sub-pattern (key name / ssh port / IPv4-like / host). For the environment lock files and
the registry rows (public data, no licence content) the matched substrings are printed to show what matched; licence VALUES are never involved here."""
import os
import re
import subprocess
from pathlib import Path

pats = {"keyname": r"WLSACCESSID|WLSSECRET|LICENSEID", "ssh_port": r"ssh +-p +[0-9]+", "ipv4_like": r"(^|[^0-9.])(([0-9]{1,3}\.){3}[0-9]{1,3})([^0-9.]|$)", "host": r"autodl\.com|seetacloud|region-[0-9]+\."}
WT = "/home/jin/wt_dfx_v3_20261026"
texts = {"pkg env/ENV_LOCK.txt": Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx/env/ENV_LOCK.txt").read_text(errors="ignore"),
         "pkg env/conda_explicit_linux64.txt": Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026/cloud_package_dfx/env/conda_explicit_linux64.txt").read_text(errors="ignore"),
         "commit 72083fde D1_EVIDENCE.json (diff)": subprocess.run(["git", "-C", WT, "show", "72083fde", "--", "research_inputs/registry_v5/D1_EVIDENCE.json"], capture_output=True, text=True, errors="ignore").stdout,
         "commit 72083fde DATA_REGISTRY.csv (diff)": subprocess.run(["git", "-C", WT, "show", "72083fde", "--", "research_inputs/registry_v5/DATA_REGISTRY.csv"], capture_output=True, text=True, errors="ignore").stdout,
         "commit 5405e477 hpc_preflight.sh (diff)": subprocess.run(["git", "-C", WT, "show", "5405e477", "--", "research/06_scope_redesign/p1_dfx_20261026/hpc_package_dfx/hpc_preflight.sh"], capture_output=True, text=True, errors="ignore").stdout,
         "commit 5405e477 make_hpc_package.sh (diff)": subprocess.run(["git", "-C", WT, "show", "5405e477", "--", "research/06_scope_redesign/p1_dfx_20261026/hpc_package_dfx/make_hpc_package.sh"], capture_output=True, text=True, errors="ignore").stdout}
for name, t in texts.items():
    for k, p in pats.items():
        ms = [m.group(0) if k != "ipv4_like" else m.group(2) for m in re.finditer(p, t, re.I | re.M)]
        if ms:
            show = sorted(set(ms))[:12] if k != "keyname" else [f"{len(ms)} key-name literal(s) (grep pattern text, no value)"]
            print(f"{name}: {k}: {len(ms)} -> {show}")
