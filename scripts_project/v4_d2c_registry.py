"""V4 D2c (decision 223; V4_D2C_INSTRUCTION.md section 2.3): registry rows of the trunk dry-mass step, assembled into DATA_REGISTRY.csv by scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v4_d2c_registry.py && python scripts_project/d1_registry.py

  fragments/v4_d2c.csv              new rows: BIOMASS_BASIS_T06.csv and the T06 potential tables (file rows); the measured oil palm trunk dry mass per palm
                                    (centre = median of Khalid 1999 / Chow 2008 / Henson 2006, each per-hectare value over the source's own planting density;
                                    range = min / max); the trunk energy per reported tonne of the T06 chain; the replanting rate with its low end 2.2 %/yr
                                    (SENSITIVITY; the main 4 %/yr is unchanged).
  fragments/v4_d2c_corrections.csv  full-row replacements of the five biomass_potential_<country>_oil_palm_trunk rows: range = v3 value x the T06 low factor
                                    (minimum measured dry mass) ... v3 value x the T05 factor (high-sensitivity switch value v4_adjusted_t05); value (v3) unchanged;
                                    written against the registry assembled with the corrections before this one (idempotent).
Evidence: research/06_scope_redesign/p1_v4_d2c_20261109/ (TRUNK_DRY_MASS.csv, evidence/D2C_TRUNK_*.json) and the D2b evidence/TRUNK_LITERATURE.json. Deterministic.
Nothing is solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import d1_registry as DR   # noqa: E402
from d1_common import REG_DIR, Registry, fmt   # noqa: E402
from v4_common import BIOMASS_DIR, ROOT, sha256   # noqa: E402

SCRIPT = "scripts_project/v4_d2c_registry.py"
D2C = "research/06_scope_redesign/p1_v4_d2c_20261109"
D2B = "research/06_scope_redesign/p1_v4_d2b_20261108"
COLUMNS = ["param_id", "description", "value", "unit", "country", "node", "tier", "source", "source_locator", "source_sha256", "derivation_script",
           "sensitivity_low", "sensitivity_high", "decision_ref", "status"]
EV = dict(mass=ROOT / D2C / "TRUNK_DRY_MASS.csv", lit=ROOT / D2C / "evidence" / "D2C_TRUNK_LITERATURE.json", calc=ROOT / D2C / "evidence" / "D2C_TRUNK_CALC.json",
          d2b=ROOT / D2B / "evidence" / "TRUNK_LITERATURE.json")
REPLANT_MAIN, REPLANT_LOW = 0.04, 0.022


def file_row(r: Registry, pid: str, p: Path, desc: str, tier: str) -> None:
    r.add(pid, desc, int(p.stat().st_size), "bytes", tier, "V4 D2c (section 2; evidence in the D2c delivery)", f"file: {p.relative_to(ROOT)}", sha256(p), decision_ref="223", status="REFERENCE_ONLY")


def trunk_mass() -> dict:
    m = pd.read_csv(EV["mass"], keep_default_na=False).set_index("source_id")
    inc = m[m.included.astype(str) == "True"]
    return dict(mid=float(m.at["CENTRE", "per_palm_t_dm"]), low=float(m.at["LOW", "per_palm_t_dm"]), high=float(m.at["HIGH", "per_palm_t_dm"]),
                sources={k: float(v) for k, v in inc.per_palm_t_dm.items()})


def new_rows() -> Registry:
    r = Registry(SCRIPT)
    basis = BIOMASS_DIR / "BIOMASS_BASIS_T06.csv"
    file_row(r, "v4_biomass_basis_table_t06", basis, "T06: BIOMASS_BASIS_T05.csv with the oil palm trunk row on the measured trunk dry mass per palm (dry matter per reported t = "
             "dry mass per palm / 2 t per palm; x LHV_dry 16.12182 / 15); every other row byte-identical to T05 (V4 D2c section 2.2)", "C")
    file_row(r, "v4_biomass_potential_2050_t06", BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4_T06.csv", "solid-biomass potential of the v4 main set (research.demand.v4.biomass_potential = "
             "v4_adjusted_t06): T05 with the five oil palm trunk rows on the measured trunk dry mass (x 0.1523 before the deductions); ASEAN11 1,252.05 TWh", "C")
    file_row(r, "v4_biomass_potential_adjustment_t06", BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4_T06.csv", "F3 / F4 / F5 (T06) adjustment by country and category", "C")
    m = trunk_mass(); ev_m = sha256(EV["mass"])
    src = "Khalid, Zin & Anderson (1999) JOPR 11(1): 23-32; Chow, Mohd Basri & Chan (2008) OPB 56: 23-28; Henson (2006) OPB 52: 1-24"
    loc = f"{D2C}/TRUNK_DRY_MASS.csv; {D2C}/evidence/D2C_TRUNK_LITERATURE.json H1-H3; {D2B}/evidence/TRUNK_LITERATURE.json T01 T04 T09 T12"
    r.add("v4_oil_palm_trunk_dry_mass_per_palm", "oil palm trunk dry mass per palm at replanting (decision 223): median of three measured sources, each per-hectare value over its own "
          f"planting density - Chow 2008 {m['sources']['CHOW2008']:.4f} (37.264 t DM/ha / 136), Henson 2006 {m['sources']['HENSON2006']:.4f} (Fig. 8 polynomial at 25 years "
          f"41.95 t DM/ha / standard 148), Khalid 1999 {m['sources']['KHALID1999']:.4f} (41.07 t DM/ha / 136); range = min / max. Henson Fig. 8 includes the Khalid 1999 points "
          "(not fully independent); not used: Husin POD 36 0.600 (estimate), secondary quotations (Corley 1971 0.300, Tinker & Smilde 1963 0.344), carbon / unstated bases. "
          "Replaces the whole-palm fresh mass of the trunk chain (IRENA 2 t per palm; T05 equivalent 0.583 t DM per palm = high-sensitivity switch value v4_adjusted_t05)",
          m["mid"], "t DM per palm", "B", src, loc, ev_m, sensitivity_low=m["low"], sensitivity_high=m["high"], decision_ref="223", status="REGISTERED")
    t = pd.read_csv(basis, keep_default_na=False).set_index("category"); x = t.loc["oil_palm_trunk"]
    r.add("v4_oil_palm_trunk_energy_per_reported_t_t06", "oil palm trunk energy per reported tonne of the potential chain under T06 (v4 main): dry mass per palm / 2 t per palm "
          "x LHV_dry 16.12182 GJ/t (D2b); W08 / T04: 15 GJ/t on the reported mass; T05: 4.702 (registry v4_oil_palm_trunk_energy_per_fresh_t). Range = min / max measured dry mass",
          15.0 * float(x.factor_mid), "GJ per reported t", "C", "derived: BIOMASS_BASIS_T06.csv", f"scripts_project/v4_biomass_potential.py basis_factors('t06'); {loc}", sha256(basis),
          sensitivity_low=15.0 * float(x.factor_low), sensitivity_high=15.0 * float(x.factor_high), decision_ref="223", status="REGISTERED")
    r.add("v4_oil_palm_replanting_rate", "oil palm replanting rate of the trunk potential chain (share of the harvested area replanted per year): main 0.04 unchanged = long-run steady "
          "state of a 25-year cycle (IRENA 2022 App. A; Hambali & Rivai 2017; Sulaiman 2013); low 0.022 = Malaysian estates 2014-2024 average (Bernama / MPOB 2025-03, deputy "
          "minister); ID PSR realised about 50,000 ha/yr since 2016 (smallholders only, Kontan 2024). The trunk potential scales linearly (x 0.55 at the low). Sensitivity only "
          "(decision 223); high = the main value", REPLANT_MAIN, "share of harvested area per year", "C",
          "IRENA (2022) Appendix A; Hambali & Rivai (2017) IOP EES 65; Bernama via MPOB Prestasi Sawit 2025-03-12; Kontan 2024-03-28",
          f"{D2B}/evidence/TRUNK_LITERATURE.json T18 T21 T29 T30", sha256(EV["d2b"]), sensitivity_low=REPLANT_LOW, sensitivity_high=REPLANT_MAIN, decision_ref="223", status="SENSITIVITY")
    return r


def corrections(base: pd.DataFrame) -> pd.DataFrame:
    R = base.set_index("param_id"); rows = []
    t6 = pd.read_csv(BIOMASS_DIR / "BIOMASS_BASIS_T06.csv", keep_default_na=False).set_index("category").loc["oil_palm_trunk"]
    t5 = pd.read_csv(BIOMASS_DIR / "BIOMASS_BASIS_T05.csv", keep_default_na=False).set_index("category").loc["oil_palm_trunk"]
    f6, fl, f5 = float(t6.factor_mid), float(t6.factor_low), float(t5.factor_mid)
    for pid in R.index:
        if not (pid.startswith("biomass_potential_") and pid.endswith("_oil_palm_trunk")):
            continue
        x = R.loc[pid].to_dict(); v = float(x["value"])
        y = dict(x, param_id=pid, description=f"{x['description']} | [V4 D2c, decision 223] range = measured trunk dry mass (T06 = v4 main, factor {f6:.4f} on this v3 value; "
                 f"low {fl:.4f} = minimum measured dry mass per palm; high {f5:.4f} = T05 whole-palm fresh mass x dry matter, the high-sensitivity switch value v4_adjusted_t05); "
                 f"former range {x['sensitivity_low']}-{x['sensitivity_high']} (D2b)", decision_ref=(x["decision_ref"] + ", 223").strip(", "),
                 sensitivity_low=fmt(v * fl), sensitivity_high=fmt(v * f5))
        rows.append({c: y[c] for c in COLUMNS})
    return pd.DataFrame(rows, columns=COLUMNS)


def main():
    for k, p in EV.items():
        if not p.exists():
            raise SystemExit(f"{p} missing: sync the D2c delivery folder into the repository first")
    r = new_rows()
    out = REG_DIR / "fragments" / "v4_d2c.csv"
    r.write(out)
    base, _ = DR.assemble(DR.CORRECTIONS[:DR.CORRECTIONS.index("v4_d2c_corrections")])
    corr = corrections(base)
    if len(corr) != 5:
        raise SystemExit(f"expected 5 trunk potential rows, found {len(corr)}")
    corr.sort_values("param_id").to_csv(REG_DIR / "fragments" / "v4_d2c_corrections.csv", index=False, lineterminator="\n")
    print(out, len(r.rows), "rows; corrections", len(corr))


if __name__ == "__main__":
    main()
