"""V4 S0: numbers quoted in V4_DATA_SCOPE.md, computed from the evidence files (no hand arithmetic) -> V4_S0_EVIDENCE.json.

    python scripts/v4s0_summary.py --work <work dir>
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    ev = a.work / "evidence"
    ob = pd.read_csv(ev / "V3_OTHER_BUCKET_BY_COUNTRY.csv").set_index("country")
    u = pd.read_csv(ev / "V3_OTHER_BUCKET_UNSD_ROWS.csv")
    u["scale"] = u.country.map(ob.other_scale_v3)
    u["y2019_v3eq_twh"] = u.y2019_total_twh * u.scale
    rows19 = u.groupby("unsd_row")[["y2019_v3eq_twh", "y2050_v3_total_twh"]].sum()
    rows19_c = u.pivot_table(index="country", columns="unsd_row", values=["y2019_v3eq_twh", "y2050_v3_total_twh"], aggfunc="sum")
    sub = pd.read_csv(ev / "V3_SUBSECTOR_2050_BY_COUNTRY.csv")
    s_tot = sub.groupby("subsector").twh_2050.sum()
    disp = pd.read_csv(ev / "V3_DISPERSED_BY_UNSD_ROW.csv")
    d_row = disp.groupby("unsd_row").twh_2050.sum()
    d_cty = disp.groupby("country").twh_2050.sum()
    d_v3 = sub[sub.subsector == "dispersed"].set_index("country").twh_2050
    st = json.loads((ev / "V3_STATUS_EVIDENCE.json").read_text(encoding="utf-8"))
    cov = json.loads((ev / "COVERAGE_SUMMARY.json").read_text(encoding="utf-8"))
    cur = json.loads((ev / "CURVES_AND_CALLIOPE.json").read_text(encoding="utf-8"))
    red = pd.read_csv(ev / "S1_OTHER_REDUCTION_PREVIEW_BY_COUNTRY.csv").set_index("country")
    A = ob.loc["ASEAN11"]
    carriers = {k.replace("other_2050_v3_", "").replace("_twh", ""): float(A[k]) for k in ob.columns if k.startswith("other_2050_v3_") and k != "other_2050_v3_twh" and k.endswith("_twh")}
    reg = pd.read_csv(a.work / "DATA_REGISTRY_V4_DOWNLOADS.csv")
    out = dict(
        instruction_sha256=hashlib.sha256((a.work / "V4_S0_INSTRUCTION.md").read_bytes()).hexdigest(),
        registry=dict(files=int(len(reg)), bytes=int(reg.bytes.sum()), extracted_members=int(len(pd.read_csv(ev / "EXTRACTED_MEMBERS.csv"))),
                      extracted_bytes=int(pd.read_csv(ev / "EXTRACTED_MEMBERS.csv").bytes.sum())),
        other_bucket_asean11=dict(industry_2019_twh=float(A.industry_2019_twh), other_2019_v2_twh=float(A.other_2019_v2_twh), other_2019_v2_share=float(A.other_2019_v2_share),
                                  other_2019_v3_twh=float(A.other_2019_v3_twh), other_2019_v3_share=float(A.other_2019_v3_share), industry_2050_bound_twh=float(A.industry_2050_bound_twh),
                                  other_2050_v2_twh=float(A.other_2050_v2_twh), other_2050_v2_share=float(A.other_2050_v2_share), other_2050_v3_twh=float(A.other_2050_v3_twh),
                                  other_2050_v3_share=float(A.other_2050_v3_share), carriers_2050_v3_twh=carriers,
                                  useful_heat_2050_v3_twh=sum(v for k, v in carriers.items() if k.startswith("heat"))),
        unsd_rows_in_other=dict(asean11=rows19.round(6).to_dict(), by_country=json.loads(rows19_c.round(6).to_json())),
        subsectors_2050_twh=s_tot.round(6).to_dict(), non_facility_share_2050=float((s_tot["other"] + s_tot["dispersed"]) / s_tot.sum()),
        dispersed_by_unsd_row_2050_twh=d_row.round(6).to_dict(), dispersed_detail_minus_v3_by_country_twh=(d_cty - d_v3.reindex(d_cty.index)).round(6).to_dict(),
        reproduction=st["reproduction"], network_check=st["network_check"],
        coverage={k: {kk: vv for kk, vv in v.items() if kk not in ("columns",)} for k, v in cov.items()},
        curves=dict(ffe=cur["ffe"], nrel={k: v for k, v in cur["nrel"].items() if k != "csv"}, calliope=cur["calliope"]),
        other_reduction_preview=dict(by_country=red.round(4).to_dict(orient="index"), asean_from_other_twh=float(red.from_other_twh.sum()),
                                     asean_from_other_excl_bn_overflow_twh=float(red.from_other_twh.sum() - max(0.0, red.at["BN", "from_other_twh"] - red.at["BN", "other_2050_v3_twh"]))),
    )
    (a.work / "V4_S0_EVIDENCE.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    print(rows19.round(3)); print(d_row.round(3), d_row.sum()); print((d_cty - d_v3.reindex(d_cty.index)).round(3))
    print("non-facility share", round(out["non_facility_share_2050"], 4), "useful heat", round(out["other_bucket_asean11"]["useful_heat_2050_v3_twh"], 3))
    print("reduction", round(out["other_reduction_preview"]["asean_from_other_twh"], 3), round(out["other_reduction_preview"]["asean_from_other_excl_bn_overflow_twh"], 3))


if __name__ == "__main__":
    main()
