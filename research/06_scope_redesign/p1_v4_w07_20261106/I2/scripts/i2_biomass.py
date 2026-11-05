"""I2 section 2 item 4: 2050 solid-biomass potential by country after W12 F3 (one bagasse NCV, reading R2), F4 / decision 210 item 4 (a)
(self-produced residues out of the potential as well as out of demand) and F7 (the s3_0 cap at 99 % of the potential).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_biomass.py

Rules (PROPOSED; quantities EXACT given the rule, grades in the table):
  F3   sugarcane_residues: minus the W12 R2 over-estimate of the bagasse part (IRENA 15 GJ/t on the IRENA mass vs the UNSD 2019 energy per t cane;
       W12 tables/W12_3_BAGASSE_SUPPLY_OVERESTIMATE.csv); KH / BN / SG: no UNSD bagasse -> no R2 value, unchanged.
  F4a  oil_palm_fibre: 100 % burned in the mill boilers (S2 2.4, IRENA 2022 p.39, d1_biomass note 'competing use') -> deducted.
  F4b  oil_palm_pks: in-mill share unknown (PKS is also sold / exported; MISSING) -> 50 % central (INFERENCE, D), 0 % / 100 % as sensitivities.
  F4c  bagasse: self-use share = UNSD 2019 industry final consumption / production (W12_3_UNSD_BAGASSE_2019.csv; the transformation part feeds
       power and stays in the pool); KH (no UNSD bagasse) 1.0 (INFERENCE); applied to the bagasse part after F3.
  F4d  other vegetal residues used in food / n.e.s. rows (demand side removed in S2 of the chain): the part not already covered by the palm
       deductions (ID, MY, TH, PH, KH) is deducted from rice / coconut residues pro rata, 2019 energy x the category growth of d1_biomass
       (rice husk at rice mills, coconut shell; INFERENCE, C); paper-row 5150 has no supply category (bark not in the potential).
  F4e  wood_processing_residues: the wood-row 5150 removed from demand (TH 1.38 TWh 2019) deducted at its 2019 value (INFERENCE).
  F7   cap used by the overflow rule = 0.99 x the adjusted potential (decision 209 F7).
Writes BIOMASS_POTENTIAL_ADJ.csv (country x category, plus country totals), /home/jin/v4i2/BIOMASS_POTENTIAL_2050_I2.csv (repository format,
potential_main_mwh adjusted; used by S7 of i2_chain.py), evidence/I2_biomass.json.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402
import i2_items as IT    # noqa: E402

PKS_CENTRAL = 0.5
PALM = ("oil_palm_fibre", "oil_palm_pks")


def main():
    ev = cm.Evidence("I2_biomass")
    bp = pd.read_csv(cm.BIO / "BIOMASS_POTENTIAL_2050.csv")
    sol = bp[bp.feedstock_group != "biogas"].copy()
    W = cm.G["W12"] / "tables"
    over = pd.read_csv(W / "W12_3_BAGASSE_SUPPLY_OVERESTIMATE.csv").set_index("country")
    ub = pd.read_csv(W / "W12_3_UNSD_BAGASSE_2019.csv").set_index("country")
    cells = IT.sdmx_industry_cells(); res = IT.residues(cells)
    r5150 = res[(res.code == "5150") & (res.cls == "a")]
    rows, tot = [], []
    adj = bp.copy()
    for cc in cm.ASEAN:
        z = sol[sol.country == cc].set_index("category")
        if z.empty:
            continue
        pot = {k: float(v) for k, v in z.potential_main_mwh.items()}
        g = {}
        for k, m in z.potential_method.items():
            mm = re.search(r"x ([0-9.]+) growth", str(m)); g[k] = float(mm.group(1)) if mm else 1.0
        d = {k: dict(F3=0.0, F4=0.0, rule=[]) for k in pot}
        # F3 bagasse R2
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
            ev.add(f"{cc}.bagasse_selfuse_share", share, "-", "VERIFIED" if cc in ub.index else "INFERENCE", "A" if cc in ub.index else "D",
                   "W12_3_UNSD_BAGASSE_2019.csv (industry final consumption / production)")
        # F4a / F4b palm
        palm_ded = 0.0
        if "oil_palm_fibre" in pot:
            d["oil_palm_fibre"]["F4"] -= pot["oil_palm_fibre"]; palm_ded += pot["oil_palm_fibre"]; d["oil_palm_fibre"]["rule"].append("F4a fibre 100 % in-mill")
        if "oil_palm_pks" in pot:
            x = PKS_CENTRAL * pot["oil_palm_pks"]; d["oil_palm_pks"]["F4"] -= x; palm_ded += x; d["oil_palm_pks"]["rule"].append(f"F4b PKS in-mill share {PKS_CENTRAL:.0%} (central, INFERENCE)")
        # F4d food / n.e.s. 5150 not covered by the palm deduction -> rice / coconut residues (2019 energy x category growth)
        fz = float(r5150[(r5150.country == cc) & r5150.tx.isin(["1214F", "1214O"])].mwh.sum())
        palm19 = palm_ded / g.get("oil_palm_fibre", 1.0) if palm_ded > 0 else 0.0     # palm deduction in 2019 terms (FFB growth of d1_biomass)
        resid19 = max(0.0, fz - palm19)
        cats = [k for k in ("rice_residues", "coconut_residues") if pot.get(k, 0.0) > 0]
        if resid19 > 0 and cats:
            ws = sum(pot[k] for k in cats)
            for k in cats:
                x = min(pot[k], resid19 * pot[k] / ws * g.get(k, 1.0))
                d[k]["F4"] -= x; d[k]["rule"].append(f"F4d food / n.e.s. 5150 self-use {resid19 / 1e6:.3f} TWh (2019) pro rata x growth {g.get(k, 1.0):.4f}")
        # F4e wood-row 5150
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
        # sensitivities: PKS 0 % / 100 %
        if "oil_palm_pks" in pot:
            for s_ in (0.0, 1.0):
                ev.add(f"{cc}.sens.pks_{int(s_ * 100)}pct.total_adjusted_twh", (T1 + (PKS_CENTRAL - s_) * pot["oil_palm_pks"]) / 1e6, "TWh", "PROPOSED", "D",
                       "BIOMASS_POTENTIAL_ADJ.csv", "solid potential with the PKS in-mill share at this value")
    asean = pd.DataFrame(tot).sum(numeric_only=True).to_dict()
    tot.append(dict(country="ASEAN11", category="TOTAL solid", **{k: v for k, v in asean.items()}, rule="sum", status="PROPOSED (quantified)", grade="C"))
    out = pd.DataFrame(rows + tot)
    out.to_csv(cm.I2 / "BIOMASS_POTENTIAL_ADJ.csv", index=False, float_format="%.6f", lineterminator="\n")
    adj.to_csv(cm.SCRATCH / "BIOMASS_POTENTIAL_2050_I2.csv", index=False, lineterminator="\n")
    for r in tot:
        ev.add(f"{r['country']}.total", dict(v3=r["potential_v3_TWh"], F3=r["F3_bagasse_R2_TWh"], F4=r["F4_self_use_TWh"], adjusted=r["potential_adjusted_TWh"], cap99=r["F7_cap_99pct_TWh"]),
               "TWh", "PROPOSED", "C", "BIOMASS_POTENTIAL_ADJ.csv")
    ev.add("scratch_potential_file_sha256", cm.sha256(cm.SCRATCH / "BIOMASS_POTENTIAL_2050_I2.csv"), "sha256", "EXACT", "-", "/home/jin/v4i2/BIOMASS_POTENTIAL_2050_I2.csv")
    ev.write()
    pd.set_option("display.width", 220)
    print(pd.DataFrame(tot).round(2).to_string())


if __name__ == "__main__":
    main()
