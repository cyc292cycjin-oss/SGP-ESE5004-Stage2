"""V4 W08 checklist section 8 (decision 209 F3 / F4 / F7; decision 210 item 4 a): 2050 solid-biomass potential after the bagasse NCV reading R2 and
the in-mill self-use of the residues removed from demand (rules moved from work/p1_v4_w07_20261106/I2/scripts/i2_biomass.py without change).

    PYTHONHASHSEED=0 python scripts_project/v4_biomass_potential.py

  F3   sugarcane_residues: minus the W12 R2 over-estimate of the bagasse part (W12_BAGASSE_SUPPLY_OVERESTIMATE.csv); KH / BN / SG unchanged.
  F4a  oil_palm_fibre: in-mill share of the country (V4 D1 T03: research_inputs/biomass_v5/PALM_MILL_SELF_USE.csv, mid = 1.00 in every country) -> deducted.
  F4b  oil_palm_pks: in-mill share of the country (PALM_MILL_SELF_USE.csv, mid = 0.50; TH flagged contradictory, grade D); the W08 constants
       FIBRE_IN_MILL_SHARE 1.0 / PKS_IN_MILL_SHARE 0.5 are the fallback (adjust(source="constant")); low / high of the table = sensitivities.
  F4c  bagasse: UNSD 2019 industry final consumption / production (W12_UNSD_BAGASSE_2019.csv) on the bagasse part after F3.
  F4d  other vegetal residues used in food / n.e.s. rows (removed from demand): the part not covered by the palm deductions -> rice / coconut
       residues pro rata, 2019 energy x category growth; the paper-row 5150 and (decision 211 item 2) the ID paper-row fuelwood have no supply
       category (bark is not in the potential) -> no deduction.
  F4e  wood_processing_residues: the wood-row 5150 removed from demand (TH 1.38 TWh 2019).
  F7   cap of the overflow rule = 0.99 x potential (research.demand.v4.bio_cap_share; s3_0_industry.py --biomass-cap-share, s2_layers).
  F5   V4 D2a (T04, decision 220; research.demand.v4.biomass_potential = v4_adjusted_t04, the v4 main set): palm-residue energy basis - EFB and mesocarp
       fibre energy = wet mass x (1 - moisture_ar) x LHV_dry (PALM_RESIDUE_BASIS_T04.csv: EFB 0.60 / 18.0 GJ/t -> 7.2 GJ per wet t, fibre 0.37 / 18.1 ->
       11.4) instead of wet mass x 15 GJ/t; PKS consistent (kept); trunk undetermined (kept, reviewer). Applied before F3 / F4.
Writes research_inputs/biomass_v5/BIOMASS_POTENTIAL_2050_V4.csv (format of BIOMASS_POTENTIAL_2050.csv, potential_main_mwh adjusted; W08 basis, the switch
alternative v4_adjusted) and BIOMASS_POTENTIAL_ADJ_V4.csv (country x category with the rule); BIOMASS_POTENTIAL_2050_V4_T04.csv / BIOMASS_POTENTIAL_ADJ_V4_T04.csv
(T04 basis, v4 main). Nothing is solved.
  V4 D2b: BIOMASS_POTENTIAL_2050_V4_T05.csv / BIOMASS_POTENTIAL_ADJ_V4_T05.csv (T05: every category audited; trunk fresh mass x 15 GJ/t -> dry matter x LHV_dry).
  V4 D2c (decision 223): BIOMASS_POTENTIAL_2050_V4_T06.csv / BIOMASS_POTENTIAL_ADJ_V4_T06.csv (T06 = v4 main: T05 with the trunk on the measured trunk dry mass
  per palm, BIOMASS_BASIS_T06.csv); T05 stays as the high-sensitivity switch value, T04 / W08 / v3 as alternatives (their files unchanged).
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

PKS_IN_MILL_SHARE = 0.5     # W08 constant (I2 central, grade D); V4 D1: fallback of the table (source="constant")
FIBRE_IN_MILL_SHARE = 1.0   # W08 constant; V4 D1: fallback of the table
OUT = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4.csv"
ADJ = BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4.csv"
OUT_T04 = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4_T04.csv"   # V4 D2a (T04, decision 220): research.demand.v4.biomass_potential = v4_adjusted_t04 (v4 main)
ADJ_T04 = BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4_T04.csv"
BASIS_T04 = BIOMASS_DIR / "PALM_RESIDUE_BASIS_T04.csv"   # V4 D2a: moisture / LHV basis of the palm residues (evidence/T04_LITERATURE.json of the D2a delivery)
OUT_T05 = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4_T05.csv"   # V4 D2b (T05, decision 221): research.demand.v4.biomass_potential = v4_adjusted_t05 (high-sensitivity switch value since D2c)
ADJ_T05 = BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4_T05.csv"
BASIS_T05 = BIOMASS_DIR / "BIOMASS_BASIS_T05.csv"   # V4 D2b: mass / heating-value basis audit of every category (BIOMASS_BASIS_AUDIT.csv of the D2b delivery)
OUT_T06 = BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4_T06.csv"   # V4 D2c (T06, decision 223): research.demand.v4.biomass_potential = v4_adjusted_t06 (v4 main)
ADJ_T06 = BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4_T06.csv"
BASIS_T06 = BIOMASS_DIR / "BIOMASS_BASIS_T06.csv"   # V4 D2c: T05 with the oil palm trunk row on the measured trunk dry mass per palm (TRUNK_DRY_MASS.csv of the D2c delivery)
BASES = ("w08", "t04", "t05", "t06")
SELF_USE = BIOMASS_DIR / "PALM_MILL_SELF_USE.csv"   # V4 D1 (decision 214 (a), T03): per country fibre / PKS low / mid / high, grades, verdicts, sources


def self_use(source: str = "table", level: str = "mid") -> dict:
    """In-mill self-use shares {country: dict(fibre, pks, grade_fibre, grade_pks, src_fibre, src_pks)}: source table (PALM_MILL_SELF_USE.csv, level low | mid | high) or
    constant (the W08 values 1.0 / 0.5, grades C / D). Countries missing from the table get the constants."""
    const = lambda cc: dict(fibre=FIBRE_IN_MILL_SHARE, pks=PKS_IN_MILL_SHARE, grade_fibre="C", grade_pks="D", src_fibre="W08 constant", src_pks="W08 constant")   # noqa: E731
    if source == "constant":
        return {cc: const(cc) for cc in ASEAN}
    if source != "table" or level not in ("low", "mid", "high"):
        raise ValueError(f"self_use source {source} / level {level}")
    t = pd.read_csv(SELF_USE).set_index("country")
    out = {cc: const(cc) for cc in ASEAN}
    for cc in t.index:
        out[cc] = dict(fibre=float(t.at[cc, f"fibre_{level}"]), pks=float(t.at[cc, f"pks_{level}"]), grade_fibre=str(t.at[cc, "grade_fibre"]),
                       grade_pks=str(t.at[cc, "grade_pks"]), src_fibre=f"PALM_MILL_SELF_USE.csv {level}, {t.at[cc, 'verdict_fibre'].lower()} (V4 D1 T03)",
                       src_pks=f"PALM_MILL_SELF_USE.csv {level}, {t.at[cc, 'verdict_pks'].lower()} (V4 D1 T03)")
    return out


def basis_factors(basis: str = "w08") -> dict:
    """V4 D2a (T04) / D2b (T05): {category: (factor on the W08 energy, GJ per reported tonne, rule text, low rule)} of the energy-basis correction; empty for W08.
    T04: factor = (1 - moisture_ar) x LHV_dry / 15 for the rows of PALM_RESIDUE_BASIS_T04.csv whose verdict is INCONSISTENT (applied True).
    T05: the rows of BIOMASS_BASIS_T05.csv with applied True; factor = dry_matter_per_reported_t x LHV_dry / lhv_table (dry_matter = 1 - moisture of the
    reported mass, lhv_table = the GJ/t of the table row, 15 or 9.14 GJ/m3); the T04 palm rows are carried over unchanged (same factors). low_rule:
    scale (the table's low / high variants are collection or residue-factor variants: x factor) | basis (the table's low variant is itself an energy-basis
    variant, e.g. the trunk 'dry matter 0.2': low = main x factor_low, high x factor_mid).
    T06 (V4 D2c, decision 223): the rows of BIOMASS_BASIS_T06.csv, same rule as T05; only the oil_palm_trunk row differs from T05 (dry matter per reported t =
    measured trunk dry mass per palm / 2 t per palm)."""
    if basis not in BASES:
        raise ValueError(f"biomass energy basis {basis} not in {BASES}")
    if basis == "w08":
        return {}
    if basis == "t04":
        t = pd.read_csv(BASIS_T04, keep_default_na=False)
        out = {}
        for r in t.itertuples():
            if str(r.applied) != "True":
                continue
            f = (1.0 - float(r.moisture_ar_mid)) * float(r.lhv_dry_gj_t_mid) / 15.0
            if abs(f - float(r.factor_mid)) > 1e-9:
                raise ValueError(f"PALM_RESIDUE_BASIS_T04.csv {r.category}: factor_mid {r.factor_mid} != (1 - {r.moisture_ar_mid}) x {r.lhv_dry_gj_t_mid} / 15 = {f}")
            out[r.category] = (f, 15.0 * f, f"F5 T04 basis: (1 - {float(r.moisture_ar_mid):.2f}) x {float(r.lhv_dry_gj_t_mid):g} GJ/t dry = {15.0 * f:.3f} GJ per wet t instead of 15 (x {f:.4f})", "scale", None)
        return out
    path = BASIS_T05 if basis == "t05" else BASIS_T06
    new6 = t06_changed() if basis == "t06" else set()
    t = pd.read_csv(path, keep_default_na=False)
    out = {}
    for r in t.itertuples():
        if str(r.applied) != "True":
            continue
        tag = "T06" if r.category in new6 else "T05"   # V4 D2c: rows carried over unchanged from T05 keep the T05 text (the T06 file = T05 except the trunk rows)
        dm, lhv, tab = float(r.dry_matter_mid), float(r.lhv_dry_gj_t_mid), float(r.lhv_table_gj_t)
        f = dm * lhv / tab
        if abs(f - float(r.factor_mid)) > 1e-9:
            raise ValueError(f"{path.name} {r.category}: factor_mid {r.factor_mid} != {dm} x {lhv} / {tab} = {f}")
        out[r.category] = (f, tab * f, f"F5 {tag} basis: {dm:.3f} dry matter per reported t x {lhv:g} GJ/t dry = {tab * f:.3f} GJ per reported t instead of {tab:g} (x {f:.4f})",
                           str(r.low_rule), float(r.factor_low))
    return out


def t06_changed() -> set:
    """V4 D2c: categories whose BIOMASS_BASIS_T06.csv row differs from BIOMASS_BASIS_T05.csv (decision 223: only the oil palm trunk); every other row is the T05 row."""
    a = pd.read_csv(BASIS_T05, dtype=str, keep_default_na=False).set_index("category")
    b = pd.read_csv(BASIS_T06, dtype=str, keep_default_na=False).set_index("category")
    if set(a.index) != set(b.index) or list(a.columns) != list(b.columns):
        raise ValueError("BIOMASS_BASIS_T06.csv must hold the categories and columns of BIOMASS_BASIS_T05.csv")
    return {k for k in b.index if not a.loc[k].equals(b.loc[k])}


def adjust(pks_share: float | None = None, source: str = "table", level: str = "mid", basis: str = "w08") -> tuple[pd.DataFrame, pd.DataFrame]:
    """pks_share (W08 interface): one PKS share for every country (sensitivity) instead of the table / constant value.
    basis (V4 D2a, T04): w08 = the W08 energy basis (15 GJ/t on the wet residue mass) | t04 = the palm-residue basis correction of PALM_RESIDUE_BASIS_T04.csv
    applied to the v3 potential before the F3 / F4 deductions (EFB, fibre; PKS kept; trunk undetermined, kept)."""
    su = self_use(source, level)
    bf = basis_factors(basis)
    new6 = t06_changed() if basis == "t06" else set()
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
        d = {k: dict(F3=0.0, F4=0.0, F5=0.0, rule=[]) for k in pot}
        for k, (f, gj, txt, low_rule, f_low) in bf.items():   # V4 D2a (T04) / D2b (T05): basis correction before the deductions (the shares of F4 act on the corrected energy)
            if k in pot:
                d[k]["F5"] = pot[k] * (f - 1.0); d[k]["rule"].append(txt)
                m = (adj.country == cc) & (adj.category == k)
                if low_rule == "basis":   # the table's low variant was an energy-basis variant: low = main x factor_low; high (a mass variant) x factor
                    adj.loc[m, "potential_low_mwh"] = pot[k] * f_low
                    adj.loc[m, "potential_high_mwh"] = pd.to_numeric(adj.loc[m, "potential_high_mwh"], errors="coerce") * f
                else:
                    for col in ("potential_low_mwh", "potential_high_mwh"):
                        adj.loc[m, col] = pd.to_numeric(adj.loc[m, col], errors="coerce") * f
                pot[k] = pot[k] * f
                adj.loc[m, "lhv_gj_per_t"] = gj
                if basis == "t04":
                    tag, tab = ("V4 D2a T04", "PALM_RESIDUE_BASIS_T04.csv")
                elif basis == "t06" and k in new6:   # V4 D2c: only the rows that differ from T05 cite T06; the rest stay byte-identical to the T05 output
                    tag, tab = ("V4 D2c T06", "BIOMASS_BASIS_T06.csv")
                else:
                    tag, tab = ("V4 D2b T05", "BIOMASS_BASIS_T05.csv")
                adj.loc[m, "potential_method"] = adj.loc[m, "potential_method"].astype(str) + f" | {tag}: {txt} ({tab})"
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
        u = su[cc]; grades = {}
        if "oil_palm_fibre" in pot:
            x = u["fibre"] * pot["oil_palm_fibre"]; d["oil_palm_fibre"]["F4"] -= x; palm_ded += x
            d["oil_palm_fibre"]["rule"].append(f"F4a fibre in-mill share {u['fibre']:.0%} ({u['src_fibre']})"); grades["oil_palm_fibre"] = u["grade_fibre"]
        if "oil_palm_pks" in pot:
            s = u["pks"] if pks_share is None else float(pks_share)
            x = s * pot["oil_palm_pks"]; d["oil_palm_pks"]["F4"] -= x; palm_ded += x
            d["oil_palm_pks"]["rule"].append(f"F4b PKS in-mill share {s:.0%} ({u['src_pks'] if pks_share is None else 'sensitivity'})"); grades["oil_palm_pks"] = u["grade_pks"] if pks_share is None else "D"
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
            row = dict(country=cc, category=k, potential_v3_TWh=(v - d[k]["F5"]) / 1e6, F3_bagasse_R2_TWh=d[k]["F3"] / 1e6, F4_self_use_TWh=d[k]["F4"] / 1e6,
                       potential_adjusted_TWh=a / 1e6, F7_cap_99pct_TWh=0.99 * a / 1e6, rule="; ".join(d[k]["rule"]),
                       status="PROPOSED (quantified)" if d[k]["rule"] else "VERIFIED (unchanged)",
                       grade=(grades[k] if k in grades else ("D" if any("PKS" in s or "KH" in s for s in d[k]["rule"]) else ("C" if d[k]["rule"] else "B"))))
            if bf:
                row["F5_basis_TWh"] = d[k]["F5"] / 1e6
            rows.append(row)
            m = (adj.country == cc) & (adj.category == k)
            adj.loc[m, "potential_main_mwh"] = a
        T0 = sum(pot[k] - d[k]["F5"] for k in pot); T1 = sum(max(0.0, pot[k] + d[k]["F3"] + d[k]["F4"]) for k in pot)
        tot.append(dict(country=cc, category="TOTAL solid", potential_v3_TWh=T0 / 1e6, F3_bagasse_R2_TWh=sum(x["F3"] for x in d.values()) / 1e6,
                        F4_self_use_TWh=sum(x["F4"] for x in d.values()) / 1e6, potential_adjusted_TWh=T1 / 1e6, F7_cap_99pct_TWh=0.99 * T1 / 1e6,
                        rule="country total", status="PROPOSED (quantified)", grade="C", **({"F5_basis_TWh": sum(x["F5"] for x in d.values()) / 1e6} if bf else {})))
    asean = pd.DataFrame(tot).sum(numeric_only=True).to_dict()
    tot.append(dict(country="ASEAN11", category="TOTAL solid", **{k: v for k, v in asean.items()}, rule="sum", status="PROPOSED (quantified)", grade="C"))
    return adj, pd.DataFrame(rows + tot)


def main():
    adj, tab = adjust()
    adj.to_csv(OUT, index=False, lineterminator="\n")
    tab.to_csv(ADJ, index=False, float_format="%.6f", lineterminator="\n")
    print(tab[tab.category == "TOTAL solid"].round(2).to_string())
    adj4, tab4 = adjust(basis="t04")   # V4 D2a (T04): switch alternative since D2b
    adj4.to_csv(OUT_T04, index=False, lineterminator="\n")
    tab4.to_csv(ADJ_T04, index=False, float_format="%.6f", lineterminator="\n")
    print(tab4[tab4.category == "TOTAL solid"].round(2).to_string())
    adj5, tab5 = adjust(basis="t05")   # V4 D2b (T05, decision 221): high-sensitivity switch value since D2c (decision 223)
    adj5.to_csv(OUT_T05, index=False, lineterminator="\n")
    tab5.to_csv(ADJ_T05, index=False, float_format="%.6f", lineterminator="\n")
    print(tab5[tab5.category == "TOTAL solid"].round(2).to_string())
    adj6, tab6 = adjust(basis="t06")   # V4 D2c (T06, decision 223): the v4 main potential (measured trunk dry mass)
    adj6.to_csv(OUT_T06, index=False, lineterminator="\n")
    tab6.to_csv(ADJ_T06, index=False, float_format="%.6f", lineterminator="\n")
    print(tab6[tab6.category == "TOTAL solid"].round(2).to_string())


if __name__ == "__main__":
    main()
