"""V4 W08 checklist section 8 (decision 209 F3 / F4 / F7; decision 210 item 4 a): 2050 solid-biomass potential after the bagasse NCV reading R2 and
the in-mill self-use of the residues removed from demand (rules moved from work/p1_v4_w07_20261106/I2/scripts/i2_biomass.py without change).

    PYTHONHASHSEED=0 python scripts_project/v4_biomass_potential.py

  F3   sugarcane_residues: minus the W12 R2 over-estimate of the bagasse part (W12_BAGASSE_SUPPLY_OVERESTIMATE.csv); KH / BN / SG unchanged.
  F4a  oil_palm_fibre: 100 % burned in the mill boilers -> deducted.
  F4b  oil_palm_pks: in-mill share PKS_IN_MILL_SHARE (0.5 central, D; MISSING T03 - to replace), 0 / 1 sensitivities.
  F4c  bagasse: UNSD 2019 industry final consumption / production (W12_UNSD_BAGASSE_2019.csv) on the bagasse part after F3.
  F4d  other vegetal residues used in food / n.e.s. rows (removed from demand): the part not covered by the palm deductions -> rice / coconut
       residues pro rata, 2019 energy x category growth; the paper-row 5150 and (decision 211 item 2) the ID paper-row fuelwood have no supply
       category (bark is not in the potential) -> no deduction.
  F4e  wood_processing_residues: the wood-row 5150 removed from demand (TH 1.38 TWh 2019).
  F7   cap of the overflow rule = 0.99 x potential (research.demand.v4.bio_cap_share; s3_0_industry.py --biomass-cap-share, s2_layers).
Writes research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv (format of BIOMASS_POTENTIAL_2050.csv, potential_main_mwh adjusted) and
BIOMASS_POTENTIAL_ADJ_V4.csv (country x category with the rule). Nothing is solved.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import v4_industry_cache as VC   # noqa: E402
from v4_common import ASEAN, BIOMASS_DIR   # noqa: E402

PKS_IN_MILL_SHARE = 0.5   # D: MISSING T03 (GAPKI / MPOB steam balance), 0 / 1 sensitivities
OUT = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4.csv"
ADJ = BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4.csv"


def adjust(pks_share: float = PKS_IN_MILL_SHARE) -> tuple[pd.DataFrame, pd.DataFrame]:
    bp = pd.read_csv(BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv")
    sol = bp[bp.feedstock_group != "biogas"].copy()
    over = pd.read_csv(BIOMASS_DIR / "W12_BAGASSE_SUPPLY_OVERESTIMATE.csv").set_index("country")
    ub = pd.read_csv(BIOMASS_DIR / "W12_UNSD_BAGASSE_2019.csv").set_index("country")
    res = VC.residues(VC.load_cells())
    r5150 = res[(res.code == "5150") & (res.cls == "a")]
    rows, tot = [], []
    adj = bp.copy()
    for cc in ASEAN:
        z = sol[sol.country == cc].set_index("category")
        if z.empty:
            continue
        pot = {k: float(v) for k, v in z.potential_main_mwh.items()}
        g = {}
        for k, m in z.potential_method.items():
            mm = re.search(r"x ([0-9.]+) growth", str(m)); g[k] = float(mm.group(1)) if mm else 1.0
        d = {k: dict(F3=0.0, F4=0.0, rule=[]) for k in pot}
        if "sugarcane_residues" in pot:
            o = over.loc[cc] if cc in over.index else None
            r2 = float(o.overestimate_mwh_R2) if (o is not None and pd.notna(o.overestimate_mwh_R2)) else 0.0
            bag15 = float(o.bagasse_mwh_15) if o is not None else 0.0
            d["sugarcane_residues"]["F3"] = -r2
            d["sugarcane_residues"]["rule"].append(f"F3 R2 bagasse over-estimate {r2 / 1e6:.3f} TWh (W12)" if r2 else "F3: no UNSD bagasse -> unchanged")
            share = 1.0
            if cc in ub.index and float(ub.at[cc, "kt_production"]) > 0:
                share = float(ub.at[cc, "kt_final_consumption"]) / float(ub.at[cc, "kt_production"])
            bag_after = max(0.0, bag15 - r2)
            d["sugarcane_residues"]["F4"] -= share * bag_after
            d["sugarcane_residues"]["rule"].append(f"F4c bagasse self-use share {share:.3f} x bagasse part after F3 {bag_after / 1e6:.3f} TWh")
        palm_ded = 0.0
        if "oil_palm_fibre" in pot:
            d["oil_palm_fibre"]["F4"] -= pot["oil_palm_fibre"]; palm_ded += pot["oil_palm_fibre"]; d["oil_palm_fibre"]["rule"].append("F4a fibre 100 % in-mill")
        if "oil_palm_pks" in pot:
            x = pks_share * pot["oil_palm_pks"]; d["oil_palm_pks"]["F4"] -= x; palm_ded += x; d["oil_palm_pks"]["rule"].append(f"F4b PKS in-mill share {pks_share:.0%} (central, INFERENCE)")
        fz = float(r5150[(r5150.country == cc) & r5150.tx.isin(["1214F", "1214O"])].mwh.sum())
        palm19 = palm_ded / g.get("oil_palm_fibre", 1.0) if palm_ded > 0 else 0.0
        resid19 = max(0.0, fz - palm19)
        cats = [k for k in ("rice_residues", "coconut_residues") if pot.get(k, 0.0) > 0]
        if resid19 > 0 and cats:
            ws = sum(pot[k] for k in cats)
            for k in cats:
                x = min(pot[k], resid19 * pot[k] / ws * g.get(k, 1.0))
                d[k]["F4"] -= x; d[k]["rule"].append(f"F4d food / n.e.s. 5150 self-use {resid19 / 1e6:.3f} TWh (2019) pro rata x growth {g.get(k, 1.0):.4f}")
        wz = float(r5150[(r5150.country == cc) & (r5150.tx == "1214H")].mwh.sum())
        if wz > 0 and "wood_processing_residues" in pot:
            x = min(pot["wood_processing_residues"], wz); d["wood_processing_residues"]["F4"] -= x
            d["wood_processing_residues"]["rule"].append(f"F4e wood-row 5150 {wz / 1e6:.3f} TWh (2019)")
        for k, v in pot.items():
            a = max(0.0, v + d[k]["F3"] + d[k]["F4"])
            rows.append(dict(country=cc, category=k, potential_v3_TWh=v / 1e6, F3_bagasse_R2_TWh=d[k]["F3"] / 1e6, F4_self_use_TWh=d[k]["F4"] / 1e6,
                             potential_adjusted_TWh=a / 1e6, F7_cap_99pct_TWh=0.99 * a / 1e6, rule="; ".join(d[k]["rule"]),
                             status="PROPOSED (quantified)" if d[k]["rule"] else "VERIFIED (unchanged)",
                             grade=("D" if any("PKS" in s or "KH" in s for s in d[k]["rule"]) else ("C" if d[k]["rule"] else "B"))))
            m = (adj.country == cc) & (adj.category == k)
            adj.loc[m, "potential_main_mwh"] = a
        T0 = sum(pot.values()); T1 = sum(max(0.0, pot[k] + d[k]["F3"] + d[k]["F4"]) for k in pot)
        tot.append(dict(country=cc, category="TOTAL solid", potential_v3_TWh=T0 / 1e6, F3_bagasse_R2_TWh=sum(x["F3"] for x in d.values()) / 1e6,
                        F4_self_use_TWh=sum(x["F4"] for x in d.values()) / 1e6, potential_adjusted_TWh=T1 / 1e6, F7_cap_99pct_TWh=0.99 * T1 / 1e6,
                        rule="country total", status="PROPOSED (quantified)", grade="C"))
    asean = pd.DataFrame(tot).sum(numeric_only=True).to_dict()
    tot.append(dict(country="ASEAN11", category="TOTAL solid", **{k: v for k, v in asean.items()}, rule="sum", status="PROPOSED (quantified)", grade="C"))
    return adj, pd.DataFrame(rows + tot)


def main():
    adj, tab = adjust()
    adj.to_csv(OUT, index=False, lineterminator="\n")
    tab.to_csv(ADJ, index=False, float_format="%.6f", lineterminator="\n")
    print(tab[tab.category == "TOTAL solid"].round(2).to_string())


if __name__ == "__main__":
    main()
