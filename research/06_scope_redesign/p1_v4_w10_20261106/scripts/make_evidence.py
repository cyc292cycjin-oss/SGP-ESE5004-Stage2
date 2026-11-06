#!/usr/bin/env python3
"""V4 W10-5: EVIDENCE.json (light) from the W10 outputs: instruction, branch, registry, inventory, result sets, checks, stability,
counts, top rows, budget and the SHA256 of every delivered file. usage: python make_evidence.py <delivery dir> <base commit> [commit ...]"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

d = Path(sys.argv[1]); base = sys.argv[2]; commits = sys.argv[3:]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


meta = json.loads((d / "C_GRADE_INVENTORY_META.json").read_text())
summ = json.loads((d / "RERANK_SUMMARY.json").read_text())
chk = json.loads((d / "evidence" / "CHECKS.json").read_text())
st = json.loads((d / "evidence" / "SELFTEST.json").read_text())
imp = pd.read_csv(d / "IMPACT_FIRST_ORDER.csv")
inv = pd.read_csv(d / "C_GRADE_INVENTORY.csv", dtype=str, keep_default_na=False)
top = pd.read_csv(d / "TOP30.csv")
u = pd.read_csv(d / "UNRELIABLE_FIRST_ORDER.csv")
r = imp[imp.ranked]
files = sorted(p for p in d.rglob("*") if p.is_file() and "cache" not in p.parts and p.suffix != ".zip" and p.name != "EVIDENCE.json" and "__pycache__" not in p.parts)
ev = dict(
    schema="v4-w10-evidence-v1", step="V4 W10 phase 1 (ledger W10; decisions 201, 211)",
    instruction=dict(file="V4_W10_INSTRUCTION.md", sha256=sha(d / "V4_W10_INSTRUCTION.md"), expected="14165bf102dbfcb25fa06255a4884474691515a33eb3b86866886d8542a160ed"),
    branch="codex/v4-w10-20261106", base_commit=base, commits=commits, worktree="/home/jin/wt_v4_w10",
    registry=dict(path="research_inputs/registry_v5/DATA_REGISTRY.csv", sha256=meta["registry_sha256"], reconciliation_item_201=meta["reconciliation_item_201"],
                  common_441_rows_identical="value, unit, tier, status, sensitivity_low/high, source_sha256, description: 0 differences (VERIFIED)"),
    inventory=dict(rows=meta["rows"], by_family_201=meta["by_family_201"], by_side=meta["by_side"], by_mechanism=meta["by_mechanism"], code_paths_not_found=meta["code_paths_not_found"],
                   exclusive_classes=dict(ranked=282, demand_I2=79, inactive_in_main=54, discrete=32, duplicate_or_scenario=15)),
    result_sets={k: dict(F1=v["F1"]["run_dir"], F2=v["F2"]["run_dir"], F1_nc_sha256=v["F1"]["nc_sha256"], F2_nc_sha256=v["F2"]["nc_sha256"],
                         F1_objective=v["F1"]["objective"], F2_objective=v["F2"]["objective"], B6=v["B6"], snapshots=v["F1"]["snapshots"],
                         ship_cost_basis=v["F1"]["ship_cost_basis"], ev_mode=v["F1"]["ev_mode"]) for k, v in chk.items()},
    reference=summ["reference"],
    checks=dict(stationarity={k: dict(F1=v["F1"]["stationarity"], F2=v["F2"]["stationarity"]) for k, v in chk.items()},
                price_vs_NODAL_PRICES={k: dict(F1=v["F1"]["price_check"], F2=v["F2"]["price_check"]) for k, v in chk.items()}, selftest={k: v["result"] for k, v in st["tests"].items()}),
    stability=summ["stability"],
    impact=dict(ranked_rows=int(r.shape[0]), rows_abs_dB6_ge=dict(bn1=int((r.abs_dB6 >= 1e9).sum()), m100=int((r.abs_dB6 >= 1e8).sum()), m10=int((r.abs_dB6 >= 1e7).sum()), m1=int((r.abs_dB6 >= 1e6).sum())),
                top30_share_of_sum_abs_dB6=float(r.head(30).abs_dB6.sum() / r.abs_dB6.sum()),
                top10=[dict(rank=i + 1, param_id=x.param_id, dB6_eur=float(x.dB6), dZ_F1_eur=float(x.dZ_F1), dZ_F2_eur=float(x.dZ_F2), owen_max_country=x.owen_max_country if isinstance(x.owen_max_country, str) else "",
                            owen_max_eur=float(x.owen_max_eur) if pd.notna(x.owen_max_eur) else None) for i, x in top.head(10).reset_index(drop=True).iterrows()],
                unreliable_rows=int(len(u)), unreliable_in_top30=int((u["rank"] <= 30).sum()),
                tags="local derivatives from duals: EXACT; extrapolation to the notch: INFERENCE; proposed notches: PROPOSED; Owen by country: INFERENCE"),
    findings=dict(oil_palm_trunk_cost_zero_in_network="s2_layers.py:467 marginal_cost = 0 when the cost column is empty; ID 158.5 TWh used; proxy 9.40 EUR/MWh -> ID +1.49 bn (VERIFIED code, INFERENCE value)",
                  geothermal_knife_edge="unbuilt geothermal entry gap MY 10.8, PH 305, VN 339 EUR/MW/a vs annuity 306,946 (0.004-0.11 %); ID one node at cap, dual 102,066 (s07 V1)",
                  smr_entry_gap="ID 1.9 %, SG 2.6 % of the annuity (s07 V1)",
                  kh_co2_cap_degenerate="research_co2_storage_cap-KH binding (1.8 Mt/a used) with zero dual",
                  not_read_by_build=["share_aviation_demand_factor", "share_HVC_demand_factor", "share_bev_avail_max"], overridden=["share_bev_avail_mean (v3 E2 plug-in profile)"],
                  inactive_alternative_basis=["co2_extra_asean_storage_cost", "co2_extra_asean_offshore_storage_eur2009"],
                  feedstock_full_release_dB6_indicator_bn=dict(MY=0.96, TH=-0.62, SG=0.21, BN=0.10)),
    budget=dict(solver_calls=0, network_builds=0, downloads=0, local_compute_minutes=3, disk_added_mb=25, cache_not_committed="cache/ (22 MB, six extracts)"),
    git_hooks_note="commits 1-2 were run with -c core.hooksPath=.git/hooks; core.hooksPath unset, hooks dir holds only *.sample, pre-commit not installed -> no hook skipped; later commits without the flag",
    files={str(p.relative_to(d)): dict(sha256=sha(p), bytes=p.stat().st_size) for p in files})
(d / "EVIDENCE.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
print("EVIDENCE.json files:", len(ev["files"]))
