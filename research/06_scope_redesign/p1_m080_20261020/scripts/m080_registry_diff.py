"""M08-0: row-by-row diff of the registry before (S4R head cefab870) and after M08-0 (working tree); asserts that no value read by the
build changed. Output <out>/evidence/M080_REGISTRY_DIFF.csv and M080_REGISTRY_DIFF.json.

    python -I m080_registry_diff.py --repo /home/jin/wt_m080_20261020 --base cefab870 --out /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m080_20261020
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
from pathlib import Path

import pandas as pd

REG = "research_inputs/registry_v5/DATA_REGISTRY.csv"
# param_id patterns read by the build code at the screening build commit (m080 grep of s2_/s3_/s4 layer code); their values must not change
BUILD_READ_PREFIXES = ("smr_", "co2_storage_potential_", "co2_injection_cap_", "fuel_price_", "fx_", "process_emissions_", "demand_", "lng_import_price",
                       "conv_", "deflator_")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--base", default="cefab870")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    old_txt = subprocess.check_output(["git", "-C", str(a.repo), "show", f"{a.base}:{REG}"])
    old = pd.read_csv(io.BytesIO(old_txt), dtype=str, keep_default_na=False).set_index("param_id")
    new_path = a.repo / REG
    new = pd.read_csv(new_path, dtype=str, keep_default_na=False).set_index("param_id")
    rows = []
    for pid in sorted(set(new.index) - set(old.index)):
        r = new.loc[pid]
        rows.append(dict(param_id=pid, change="add", fields="", tier_old="", tier_new=r.tier, status_old="", status_new=r.status, value_old="", value_new=r.value,
                         derivation_script=r.derivation_script))
    for pid in sorted(set(old.index) - set(new.index)):
        rows.append(dict(param_id=pid, change="removed", fields="", tier_old=old.at[pid, "tier"], status_old=old.at[pid, "status"], value_old=old.at[pid, "value"]))
    for pid in sorted(set(old.index) & set(new.index)):
        diff = [c for c in old.columns if old.at[pid, c] != new.at[pid, c]]
        if diff:
            rows.append(dict(param_id=pid, change="modify", fields=";".join(diff), tier_old=old.at[pid, "tier"], tier_new=new.at[pid, "tier"],
                             status_old=old.at[pid, "status"], status_new=new.at[pid, "status"], value_old=old.at[pid, "value"], value_new=new.at[pid, "value"],
                             derivation_script=new.at[pid, "derivation_script"]))
    df = pd.DataFrame(rows)
    a.out.joinpath("evidence").mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out / "evidence/M080_REGISTRY_DIFF.csv", index=False)
    mod = df[df.change == "modify"]
    value_changed = mod[mod.fields.str.contains("value")].param_id.tolist()
    build_read_value_changed = [p for p in value_changed if p.startswith(BUILD_READ_PREFIXES)]
    summary = dict(base=a.base, base_sha256=hashlib.sha256(old_txt).hexdigest(), new_sha256=hashlib.sha256(new_path.read_bytes()).hexdigest(),
                   rows_old=int(len(old)), rows_new=int(len(new)), added=int((df.change == "add").sum()), modified=int(len(mod)), removed=int((df.change == "removed").sum()),
                   modified_fields=mod.fields.str.split(";").explode().value_counts().to_dict(), value_changed=value_changed,
                   build_read_value_changed=build_read_value_changed,
                   status_changes=mod[mod.status_old != mod.status_new].groupby(["status_old", "status_new"]).size().rename("n").reset_index().to_dict(orient="records"),
                   tier_changes=mod[mod.tier_old != mod.tier_new][["param_id", "tier_old", "tier_new"]].to_dict(orient="records"),
                   by_tier_new=new.tier.value_counts().to_dict(), by_status_new=new.status.value_counts().to_dict())
    (a.out / "evidence/M080_REGISTRY_DIFF.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1, ensure_ascii=False))
    if build_read_value_changed:
        raise SystemExit(f"values read by the build changed: {build_read_value_changed}")


if __name__ == "__main__":
    main()
