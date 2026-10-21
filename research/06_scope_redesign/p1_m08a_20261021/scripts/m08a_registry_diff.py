"""M08a A10: row-by-row diff of the registry before M08a (M08-0 head 30d281b8) and after M08a (working tree / branch head); lists the added,
modified and removed rows, status / tier changes, rows marked historical ('历史：已被 X 替代'), values read by the build that changed (intended
in M08a, listed - not refused as in M08-0), and the coverage of REGISTRY_ROWS_PROPOSED_v2.csv. No build, no solve.

    python m08a_registry_diff.py --repo /home/jin/wt_m08a_20261021 --base 30d281b8 \
        --proposed /mnt/d/ResearchWorkspaces/ASEAN/work/p1_m080_20261020/REGISTRY_ROWS_PROPOSED_v2.csv --out <work dir>
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
BUILD_READ_PREFIXES = ("smr_", "co2_storage_potential_", "co2_injection_cap_", "fuel_price_", "fx_", "process_emissions_", "demand_", "lng_import_price",
                       "conv_", "deflator_")   # = M08-0 m080_registry_diff.py
LATER_STEPS = {"M08b": ("demand_", "industry_", "biomass_overflow_rule")}   # instruction section 3: demand anchors, industry, biomass overflow


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True); ap.add_argument("--base", default="30d281b8")
    ap.add_argument("--proposed", type=Path, required=True); ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    old_txt = subprocess.check_output(["git", "-C", str(a.repo), "show", f"{a.base}:{REG}"])
    old = pd.read_csv(io.BytesIO(old_txt), dtype=str, keep_default_na=False).set_index("param_id")
    new_path = a.repo / REG
    new = pd.read_csv(new_path, dtype=str, keep_default_na=False).set_index("param_id")
    rows = []
    for pid in sorted(set(new.index) - set(old.index)):
        r = new.loc[pid]
        rows.append(dict(param_id=pid, change="add", fields="", tier_old="", tier_new=r.tier, status_old="", status_new=r.status, value_old="", value_new=r.value,
                         derivation_script=r.derivation_script, historical=False))
    for pid in sorted(set(old.index) - set(new.index)):
        rows.append(dict(param_id=pid, change="removed", fields="", tier_old=old.at[pid, "tier"], status_old=old.at[pid, "status"], value_old=old.at[pid, "value"]))
    for pid in sorted(set(old.index) & set(new.index)):
        diff = [c for c in old.columns if old.at[pid, c] != new.at[pid, c]]
        if diff:
            hist = "历史：已被" in new.at[pid, "description"] and "历史：已被" not in old.at[pid, "description"]
            rows.append(dict(param_id=pid, change="historical" if hist else "modify", fields=";".join(diff), tier_old=old.at[pid, "tier"], tier_new=new.at[pid, "tier"],
                             status_old=old.at[pid, "status"], status_new=new.at[pid, "status"], value_old=old.at[pid, "value"], value_new=new.at[pid, "value"],
                             derivation_script=new.at[pid, "derivation_script"], historical=hist))
    df = pd.DataFrame(rows)
    ch = df[df.change.isin(["modify", "historical"])]
    value_changed = ch[ch.fields.str.contains("value")].param_id.tolist()
    prop = pd.read_csv(a.proposed, dtype=str, keep_default_na=False)
    cover = []
    for _, x in prop.iterrows():
        later = next((s for s, pre in LATER_STEPS.items() if x.param_id.startswith(pre)), "")
        cover.append(dict(param_id=x.param_id, action=x.action, in_registry=x.param_id in new.index, status=(new.at[x.param_id, "status"] if x.param_id in new.index else ""),
                          written_in_m08a=bool(x.param_id in new.index and (x.param_id not in old.index or x.param_id in set(ch.param_id))), later_step=later))
    cv = pd.DataFrame(cover)
    missing_m08a = cv[(~cv.written_in_m08a) & (cv.later_step == "")].param_id.tolist()
    summary = dict(base=a.base, base_sha256=hashlib.sha256(old_txt).hexdigest(), new_sha256=hashlib.sha256(new_path.read_bytes()).hexdigest(),
                   rows_old=int(len(old)), rows_new=int(len(new)), added=int((df.change == "add").sum()), modified=int((df.change == "modify").sum()),
                   historical=int((df.change == "historical").sum()), removed=int((df.change == "removed").sum()),
                   modified_fields=ch.fields.str.split(";").explode().value_counts().to_dict(), value_changed=value_changed,
                   build_read_value_changed=[p for p in value_changed if p.startswith(BUILD_READ_PREFIXES)],
                   status_changes=ch[ch.status_old != ch.status_new].groupby(["status_old", "status_new"]).size().rename("n").reset_index().to_dict(orient="records"),
                   tier_changes=ch[ch.tier_old != ch.tier_new][["param_id", "tier_old", "tier_new"]].to_dict(orient="records"),
                   historical_rows=df[df.change == "historical"].param_id.tolist(),
                   data_pending_old=int((old.status == "DATA_PENDING").sum()), data_pending_new=int((new.status == "DATA_PENDING").sum()),
                   by_tier_new=new.tier.value_counts().to_dict(), by_status_new=new.status.value_counts().to_dict(),
                   proposed_v2=dict(rows=int(len(cv)), written_or_present_m08a=int(cv.written_in_m08a.sum()), later_steps=cv[cv.later_step != ""].groupby("later_step").param_id.apply(list).to_dict(),
                                    missing_for_m08a=missing_m08a, present_unchanged=cv[cv.in_registry & ~cv.written_in_m08a].param_id.tolist()))
    a.out.joinpath("evidence").mkdir(parents=True, exist_ok=True)
    df.to_csv(a.out / "evidence" / "M08A_REGISTRY_DIFF.csv", index=False)
    cv.to_csv(a.out / "evidence" / "M08A_REGISTRY_PROPOSED_V2_COVERAGE.csv", index=False)
    (a.out / "evidence" / "M08A_REGISTRY_DIFF.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("value_changed", "historical_rows")}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
