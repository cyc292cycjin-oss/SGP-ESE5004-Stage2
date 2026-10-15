"""S3-0.4: Cambodia transport chain check (report only, no model change).

Compares the UNSD 2019 Energy Balance (raw6/UNSD_EB_2019_KH.csv, TJ) with the D1 2019 transport base, follows the AEO8 ATS
calibration chain (country factor r_KH x sector calibration k) to the 2050 values, and compares the result with the Astar 2050
electricity load and the ASEAN-wide AEO8 transport totals.

    python scripts_project/s3_0_kh_check.py
"""
from __future__ import annotations

import pandas as pd

from d1_common import ROOT, SRC_DIR, src_sha, write_json

SCRIPT = "scripts_project/s3_0_kh_check.py"
KH = "UNSD_EB_2019_KH.csv"
DEM = ROOT / "research_inputs/demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv"
AEO8_TOT = "AEO8_2050_ASEAN_TOTALS.csv"
OUT = ROOT / "research/06_scope_redesign/p1_step3_20261015"
TJ_TO_MWH = 1000.0 / 3.6
MWH_PER_MTOE = 11.63e6
ACCOUNT_MAP = {"Road": "RoadResidualFuel", "Rail": "RailNonElectric", "Domestic aviation": "DomesticAviationFuel", "Domestic navigation": "DomesticShippingFuel"}


def num(v):
    s = str(v).replace("*", "").replace(",", "").strip()
    return float(s) if s not in ("---", "", "nan") else 0.0


def main():
    eb = pd.read_csv(SRC_DIR / KH, dtype=str, keep_default_na=False); eb_sha = src_sha(KH)
    eb = eb.set_index("Transactions(down)/Commodity(right)")
    dem = pd.read_csv(DEM, keep_default_na=False); kh = dem[dem.country == "KH"]
    tr = kh[kh.sector == "Transport"]
    rows = []
    for unsd_row, account in ACCOUNT_MAP.items():
        tj = num(eb.at[unsd_row, "Oil Products"]) if unsd_row in eb.index else 0.0
        d1 = float(pd.to_numeric(tr[tr.account == account].base_2019_mwh, errors="coerce").fillna(0).sum())
        v50 = float(pd.to_numeric(tr[tr.account == account].value_2050_mwh, errors="coerce").fillna(0).sum())
        rows.append(dict(unsd_row=unsd_row, unsd_oil_products_tj=tj, unsd_mwh=tj * TJ_TO_MWH, d1_account=account, d1_base_2019_mwh=d1, match=abs(tj * TJ_TO_MWH - d1) <= 0.001 * max(d1, 1.0), d1_value_2050_mwh=v50))
    tot_tj = num(eb.at["Transport", "Oil Products"]) if "Transport" in eb.index else 0.0
    parent = float(pd.to_numeric(tr[tr.account == "TransportEmbeddedFuelParent"].base_2019_mwh, errors="coerce").fillna(0).sum())
    mult = tr.multiplier_total.astype(float).iloc[0]; r_c = tr.country_multiplier.astype(float).iloc[0]; k = tr.sector_calibration_k.astype(float).iloc[0]
    fuel50 = sum(r["d1_value_2050_mwh"] for r in rows)
    astar = float(pd.to_numeric(kh[kh.in_existing_electricity_load.astype(str).str.lower() == "true"].existing_electricity_load_2050_mwh, errors="coerce").dropna().iloc[0])
    el19 = float(pd.to_numeric(kh[(kh.carrier == "electricity") & (kh.sector != "InternationalBunkers")].base_2019_mwh, errors="coerce").fillna(0).sum())
    el50 = float(pd.to_numeric(kh[(kh.carrier == "electricity") & (kh.sector != "InternationalBunkers")].value_2050_mwh, errors="coerce").fillna(0).sum())
    unsd_el_final = num(eb.at["Final consumption", "Electricity"]) * TJ_TO_MWH if "Final consumption" in eb.index else None
    # ASEAN-wide chain: sum of D1 transport bases vs AEO8 transport totals
    tr_all = dem[(dem.sector == "Transport") & (dem.account != "TransportEmbeddedFuelParent")]
    base_asean = float(pd.to_numeric(tr_all.base_2019_mwh, errors="coerce").fillna(0).sum()); v50_asean = float(pd.to_numeric(tr_all.value_2050_mwh, errors="coerce").fillna(0).sum())
    by_c = tr_all.assign(b=pd.to_numeric(tr_all.base_2019_mwh, errors="coerce").fillna(0), v=pd.to_numeric(tr_all.value_2050_mwh, errors="coerce").fillna(0)).groupby("country")[["b", "v"]].sum()
    by_c["multiplier"] = by_c.v / by_c.b.replace(0, float("nan"))
    aeo = pd.read_csv(SRC_DIR / AEO8_TOT, dtype=str, keep_default_na=False); aeo_sha = src_sha(AEO8_TOT)
    aeo_tr = aeo[(aeo.table == "C.3 TFEC by Sector") & (aeo.item == "Transport")]
    aeo_vals = {f"{r.scenario} {r.year}": float(r.value_as_printed) for _, r in aeo_tr.iterrows()}
    res = dict(script=SCRIPT, sources=dict(unsd_eb_kh=eb_sha, d1_table=str(DEM.relative_to(ROOT)), aeo8_totals=aeo_sha),
               unsd_vs_d1_base=rows, unsd_transport_total_tj=tot_tj, unsd_transport_total_mwh=tot_tj * TJ_TO_MWH, d1_parent_row_rail_mwh=parent,
               d1_base_sum_mwh=sum(r["d1_base_2019_mwh"] for r in rows), base_matches_unsd=all(r["match"] for r in rows),
               chain=dict(country_factor_r_KH=r_c, sector_calibration_k_transport=k, multiplier_total=mult, product_check=abs(r_c * k - mult) < 1e-6),
               kh_2050=dict(transport_fuel_mwh=fuel50, astar_electricity_2050_mwh=astar, d1_electricity_2050_sum_mwh=el50, electricity_2019_base_mwh=el19, unsd_final_electricity_2019_mwh=unsd_el_final,
                            transport_fuel_2050_over_astar=fuel50 / astar if astar else None, transport_fuel_2019_over_electricity_2019=sum(r["d1_base_2019_mwh"] for r in rows) / el19 if el19 else None,
                            d1_electricity_2050_over_astar=el50 / astar if astar else None),
               asean_chain=dict(d1_transport_base_2019_sum_mwh=base_asean, d1_transport_2050_sum_mwh=v50_asean, implied_asean_multiplier=v50_asean / base_asean if base_asean else None,
                                aeo8_transport_mtoe=aeo_vals, aeo8_ats_2050_mwh=aeo_vals.get("ATS 2050", 0) * MWH_PER_MTOE, aeo8_hist_2022_mwh=aeo_vals.get("historical (as printed in ATS panel) 2022", 0) * MWH_PER_MTOE,
                                d1_base_over_aeo8_2022=base_asean / (aeo_vals.get("historical (as printed in ATS panel) 2022", 0) * MWH_PER_MTOE) if aeo_vals.get("historical (as printed in ATS panel) 2022") else None,
                                by_country=by_c.round(4).to_dict("index")))
    write_json(res, OUT / "KH_TRANSPORT_CHAIN_CHECK.json")
    pd.set_option("display.width", 200)
    print(pd.DataFrame(rows).to_string()); print({k: v for k, v in res["chain"].items()}); print(res["kh_2050"]); print({k: v for k, v in res["asean_chain"].items() if k != "by_country"}); print(by_c.round(3).to_string())


if __name__ == "__main__":
    main()
