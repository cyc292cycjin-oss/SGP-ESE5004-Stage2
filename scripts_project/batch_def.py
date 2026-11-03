"""V3 supplement 01 (review decision 8): registered batch definition of the two runners (run_dfx.sh with dfx_batch.py, run_batch4.sh with b4_batch4.py).

Without a definition the runners keep their own tables (the v2 networks of DFX and of the HPR package). With a package file BATCH_DEF.json, exported by the runner as BATCH_DEF, the run table, the registered
SHA256 / bytes and the build commit come from that file; it is listed in SHA256SUMS like every other package file. A run whose scenario differs from its cost table is a variant derived from the network of
that cost scenario (V3: no_new_xb from integrated): its network is checked through <base>_VARIANT_RECEIPT.json, whose base SHA256 must be the network of the build receipt.
"""
from __future__ import annotations

import json
import os
from pathlib import Path


def load_def() -> dict | None:
    p = os.environ.get("BATCH_DEF")
    return json.loads(Path(p).read_text(encoding="utf-8")) if p else None


def _jl(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def build_stem(run: dict) -> str:
    """<stem> of the build receipt <stem>_BUILD_RECEIPT.json of a run's network. A built network (scenario = cost scenario) has its own receipt under the name of its base (bridges;
    V3 HPC F3 'integrated_ev05'); a variant uses the receipt of its parent build: 'parent' when the run names one (V3 HPC F4, derived from F3), else its cost scenario."""
    if run["scenario"] == run["costs"]:
        return run["base"].rsplit("_", 2)[0]
    return run.get("parent") or run["costs"]


def input_receipt(nets: Path, run: dict, key: str, build_commit: str) -> dict:
    """Receipt of a run's network. key: the entry of the build receipt (daily_network | network). chain_ok: the build receipt has the build commit and, for a variant, the variant was derived from that network."""
    stem = build_stem(run)   # a bridge network has its own build receipt under the name of its base, with the cost table of its scenario
    build = _jl(nets / f"{stem}_BUILD_RECEIPT.json"); net = build.get(key) or {}; ok = build.get("code_sha") == build_commit
    if run["scenario"] == run["costs"]:
        return dict(sha256=net.get("sha256"), snapshots=net.get("snapshots"), code_sha=build.get("code_sha"), chain_ok=ok)
    var = _jl(nets / f"{run['base']}_VARIANT_RECEIPT.json")
    return dict(sha256=(var.get("output") or {}).get("sha256"), snapshots=net.get("snapshots"), code_sha=build.get("code_sha"), chain_ok=ok and bool(net.get("sha256")) and (var.get("base") or {}).get("sha256") == net.get("sha256"))
