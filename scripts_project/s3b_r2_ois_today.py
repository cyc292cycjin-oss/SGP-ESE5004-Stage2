"""S3B R2 (decision 67): JRC-IDEES-2021 EU27 2019 carrier structure of "Other industrial sectors" (sheet OIS_fec) for the
other-bucket sensitivity research.s3.industry.other_bucket = idees_today.

The leaf rows of the slice idees["fec"][3:68] used by PyPSA-Eur v2025.07.0 other_industrial_sectors() (script lines 1455-1511)
are summed by fuel: electric end uses (lighting, air compressors, motor drives, fans and pumps, electric processing / drying /
cooling, electric machinery) -> electricity; diesel motors -> oil; fuel sub-rows of low-enthalpy heat, steam processing, thermal
processing, thermal and steam drying, steam cooling by their label; thermal cooling (no fuel split in IDEES) -> gas (grade C).
Distributed steam, solar/geothermal and ambient heat -> heat. The leaf sum reproduces the sector total row.

    python scripts_project/s3b_r2_ois_today.py
"""
from __future__ import annotations

import importlib.util
import sys
import types
from contextlib import contextmanager

import pandas as pd

from d1_common import REG_DIR, SRC_DIR, Registry, sha256, write_csv, write_json

SCRIPT = "scripts_project/s3b_r2_ois_today.py"
PE_SCRIPT = SRC_DIR / "pypsa_eur_v2025.07.0_build_industry_sector_ratios.py"
IDEES_DIR = SRC_DIR / "jrc_idees_2021"
IDEES_XLSX = IDEES_DIR / "EU27" / "JRC-IDEES-2021_Industry_EU27.xlsx"
OUT = REG_DIR / "INDUSTRY_OIS_TODAY_CARRIERS_EU27_2019.csv"
OUT_CARRIERS = ["coal", "oil", "gas", "biomass", "electricity", "hydrogen", "heat", "ammonia", "methanol"]
FUEL = {"Solids": "coal", "Derived gases": "coal", "Refinery gas": "oil", "LPG": "oil", "Diesel oil and liquid biofuels": "oil", "Fuel oil": "oil", "Other liquids": "oil",
        "Natural gas and biogas": "gas", "Biomass and waste": "biomass", "Electricity": "electricity", "Distributed steam": "heat", "Solar and geothermal": "heat",
        "Ambient heat": "heat"}
# (row position in idees["fec"], expected label, carrier); fuel blocks: (first, last+1, parent label)
SINGLE = [(4, "Lighting", "electricity"), (5, "Air compressors", "electricity"), (6, "Motor drives", "electricity"), (7, "Fans and pumps", "electricity"),
          (32, "Other Industrial sectors: Electric processing", "electricity"), (51, "Other Industries: Electric drying", "electricity"),
          (53, "Other Industries: Thermal cooling", "gas"), (65, "Other Industries: Electric cooling", "electricity"),
          (66, "Other Industrial sectors: Diesel motors (incl. biofuels)", "oil"), (67, "Other Industrial sectors: Electric machinery", "electricity")]
BLOCKS = [(9, 14, 8, "Low-enthalpy heat"), (15, 25, 14, "Other Industrial sectors: Steam processing"), (27, 32, 26, "Other Industrial sectors: Thermal processing"),
          (35, 40, 34, "Other Industries: Thermal drying"), (41, 51, 40, "Other Industries: Steam drying"), (55, 65, 54, "Other Industries: Steam cooling")]


@contextmanager
def _mute():
    yield


def load_ois():
    helpers = types.ModuleType("scripts._helpers"); helpers.configure_logging = lambda *a, **k: None; helpers.set_scenario_config = lambda *a, **k: None; helpers.mute_print = _mute
    pkg = types.ModuleType("scripts"); pkg.__path__ = []
    sys.modules["scripts"] = pkg; sys.modules["scripts._helpers"] = helpers
    spec = importlib.util.spec_from_file_location("pe_industry_sector_ratios_r2", PE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    mod.snakemake = types.SimpleNamespace(input=types.SimpleNamespace(idees=str(IDEES_DIR), ammonia_production=str(IDEES_DIR / "ammonia_production.csv")),
                                          params=types.SimpleNamespace(industry={"reference_year": 2019}, ammonia=True), output=None)
    spec.loader.exec_module(mod)
    mod.year = 2019
    return mod.load_idees_data("Other industrial sectors")["fec"], mod.toe_to_MWh


def main():
    fec, toe = load_ois()
    assert str(fec.index[3]) == "Other industrial sectors"
    total = float(fec.iloc[3])
    rows = []
    for pos, label, car in SINGLE:
        assert str(fec.index[pos]) == label, (pos, fec.index[pos])
        rows.append(dict(row=pos, end_use=label, fuel=label, carrier=car, ktoe_2019=float(fec.iloc[pos])))
    for a, b, parent, label in BLOCKS:
        assert str(fec.index[parent]) == label, (parent, fec.index[parent])
        part = 0.0
        for pos in range(a, b):
            f = str(fec.index[pos]); v = float(fec.iloc[pos]); part += v
            rows.append(dict(row=pos, end_use=label, fuel=f, carrier=FUEL[f], ktoe_2019=v))
        assert abs(part - float(fec.iloc[parent])) < 1e-6 * max(1.0, float(fec.iloc[parent])), (label, part, float(fec.iloc[parent]))
    leaf = sum(r["ktoe_2019"] for r in rows)
    assert abs(leaf - total) < 1e-6 * total, (leaf, total)
    by = {oc: sum(r["ktoe_2019"] for r in rows if r["carrier"] == oc) for oc in OUT_CARRIERS}
    shares = {oc: by[oc] / total for oc in OUT_CARRIERS}
    out = [dict(carrier=oc, ktoe_2019=by[oc], mwh_2019=by[oc] * toe * 1e3, share=shares[oc]) for oc in OUT_CARRIERS]
    write_csv(out, OUT, ["carrier", "ktoe_2019", "mwh_2019", "share"])
    write_csv(rows, REG_DIR / "INDUSTRY_OIS_TODAY_LEAF_ROWS_EU27_2019.csv", ["row", "end_use", "fuel", "carrier", "ktoe_2019"])
    x_sha, s_sha = sha256(IDEES_XLSX), sha256(PE_SCRIPT)
    reg = Registry(SCRIPT)
    reg.add("industry_other_bucket_mode", "Main other-bucket treatment (S3B R2, decision 67): pypsa_eur_2050 = UNSD sub-sectors other / construction / mining and quarrying mapped to the "
            "PyPSA-Eur 'Other industrial sectors' 2050 ratios (S3-0, unchanged); idees_today = the same energy x industry multiplier with the JRC-IDEES-2021 EU27 2019 carrier structure "
            "of that sector, no process switch, efficiency factor 1 (sensitivity, *_OTHER_IDEES_TODAY tables)", "pypsa_eur_2050", "flag", "B", "S3B instruction R2",
            "configs/research/baseline.yaml research.s3.industry.other_bucket", f"idees:{x_sha}", decision_ref="67")
    for oc in OUT_CARRIERS:
        if by[oc] > 0:
            reg.add(f"industry_ois_today_share_{oc}", f"JRC-IDEES-2021 EU27 2019 'Other industrial sectors' final energy share of {oc} ({by[oc]:.2f} of {total:.2f} ktoe; leaf rows of OIS_fec rows 3-68, "
                    "see INDUSTRY_OIS_TODAY_LEAF_ROWS_EU27_2019.csv)", shares[oc], "fraction", "B", "JRC-IDEES-2021 Industry EU27, sheet OIS_fec, 2019",
                    "rows 4-67 (slice [3:68] of PyPSA-Eur other_industrial_sectors, script lines 1455-1511)", f"idees:{x_sha}; script:{s_sha}", decision_ref="67", status="SENSITIVITY")
    reg.add("industry_ois_today_thermal_cooling_carrier", "IDEES row 'Other Industries: Thermal cooling' (113.61 ktoe) has no fuel split; assigned to gas (absorption cooling)",
            "gas", "carrier", "C", "JRC-IDEES-2021 Industry EU27, sheet OIS_fec", "row 53", f"idees:{x_sha}", decision_ref="67", status="SENSITIVITY")
    reg.add("industry_ois_today_heat_rows", "Distributed steam, solar/geothermal and ambient heat of the IDEES OIS rows are mapped to the industrial heat carrier", "heat", "carrier", "C",
            "JRC-IDEES-2021 Industry EU27, sheet OIS_fec", "rows 11, 12, 24, 50, 64", f"idees:{x_sha}", decision_ref="67", status="SENSITIVITY")
    reg.write(REG_DIR / "fragments" / "industry_other_bucket.csv")
    write_json(dict(script=SCRIPT, idees_sha256=x_sha, script_sha256=s_sha, total_ktoe_2019=total, by_carrier_ktoe=by, shares=shares), REG_DIR / "INDUSTRY_OIS_TODAY_EVIDENCE.json")
    print({oc: round(v, 4) for oc, v in shares.items() if v}, "total ktoe", round(total, 2))


if __name__ == "__main__":
    main()
