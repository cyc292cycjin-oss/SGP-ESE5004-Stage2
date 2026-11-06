"""V4 D1 (decisions 212, 214, 215; V4_D1_INSTRUCTION.md sections 3-5): registry rows of the D1 data step, assembled into DATA_REGISTRY.csv by
scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v4_d1_registry.py && python scripts_project/d1_registry.py

  fragments/v4_d1.csv              new rows: the missing-cost rule of the biomass pools (section 3; value read from the registry proxy rows of unsourced residues).
  fragments/v4_d1_corrections.csv  full-row replacements (section 4, decision 212 (a)): registered sensitivity ranges whose endpoints violate a physical bound are
                                   clipped to it (main values and networks unchanged); physics_limits() holds the derivations (stoichiometry, model heating values).
Deterministic (no time stamps). Nothing is solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import REG_DIR, Registry, fmt   # noqa: E402
from s2_layers import MISSING_COST_PROXY_ID, MISSING_COST_PROXY_SOURCE   # noqa: E402

SCRIPT = "scripts_project/v4_d1_registry.py"
COLUMNS = ["param_id", "description", "value", "unit", "country", "node", "tier", "source", "source_locator", "source_sha256", "derivation_script",
           "sensitivity_low", "sensitivity_high", "decision_ref", "status"]

# ---- section 4 (decision 212 (a)): physical bounds of the registered ranges -----------------------------------------------------------------------
ATOMIC = dict(H=1.008, C=12.011, N=14.007, O=15.999)   # g/mol, IUPAC 2021 abridged standard atomic weights (conventional values)
MOLAR = dict(CO2=ATOMIC["C"] + 2 * ATOMIC["O"], MeOH=ATOMIC["C"] + 4 * ATOMIC["H"] + ATOMIC["O"], H2=2 * ATOMIC["H"], NH3=ATOMIC["N"] + 3 * ATOMIC["H"])
LHV_H2_MWH_PER_T = 33.33   # hydrogen LHV 33.33 kWh/kg: technology-data / PyPSA-Eur convention; the registry has no hydrogen heating-value row (INFERENCE that the
                           # model hydrogen MWh are on this basis); 120.0 MJ/kg (33.333) or 119.96 MJ/kg (33.322) change the H2 limits by <= 1e-4 relative
HOURS_PER_YEAR = 8760.0


def physics_limits(reg: pd.DataFrame) -> dict:
    """Bounds used by PHYSICS_FIXES, from the model heating values (registry) and stoichiometry:
      CO2 + 3 H2 -> CH3OH + H2O:  MWh_MeOH per t CO2 <= M_MeOH / M_CO2 x LHV_MeOH;  MWh_MeOH per MWh_H2 <= M_MeOH x LHV_MeOH / (3 M_H2 x LHV_H2)
      N2 + 3 H2 -> 2 NH3:         MWh_H2 per t NH3 >= 1.5 M_H2 / M_NH3 x LHV_H2 (stoichiometric minimum of the hydrogen input)
      LHV per mass of any hydrocarbon <= that of methane (highest H/C): natural gas (no hydrogen) and oil products <= LHV_CH4."""
    r = reg.set_index("param_id").value
    lhv_meoh = float(r["industry_pe_param_MWh_MeOH_per_tMeOH"]); lhv_ch4_gj = float(r["biomass_methane_lhv"])
    m = MOLAR
    return dict(lhv_meoh_mwh_t=lhv_meoh, lhv_h2_mwh_t=LHV_H2_MWH_PER_T, lhv_ch4_gj_t=lhv_ch4_gj, lhv_ch4_mwh_t=lhv_ch4_gj / 3.6, molar=dict(m),
                meoh_per_tco2_max=m["MeOH"] / m["CO2"] * lhv_meoh, meoh_per_mwh_h2_max=m["MeOH"] * lhv_meoh / (3 * m["H2"] * LHV_H2_MWH_PER_T),
                h2_per_tnh3_min=1.5 * m["H2"] / m["NH3"] * LHV_H2_MWH_PER_T, hours_per_year=HOURS_PER_YEAR)


# (param_id, new low (None = keep, "value" = the main value, or a key of physics_limits), new high (same), class, basis)
PHYSICS_FIXES = [
    ("share_bev_charge_efficiency", None, 1.0, "efficiency > 1", "an efficiency cannot exceed 1 (physical upper bound, not data)"),
    ("share_bev_avail_max", None, 1.0, "share > 1", "the share of BEVs plugged in cannot exceed 1 (physical upper bound, not data)"),
    ("share_MWh_MeOH_per_tCO2", None, "meoh_per_tco2_max", "above stoichiometry", "CO2 + 3 H2 -> CH3OH + H2O: M_MeOH / M_CO2 x LHV_MeOH"),
    ("share_MWh_MeOH_per_MWh_H2", None, "meoh_per_mwh_h2_max", "above stoichiometry", "CO2 + 3 H2 -> CH3OH + H2O: M_MeOH x LHV_MeOH / (3 M_H2 x LHV_H2)"),
    ("share_MWh_H2_per_tNH3_electrolysis", "h2_per_tnh3_min", None, "below stoichiometry", "N2 + 3 H2 -> 2 NH3: hydrogen input >= 1.5 M_H2 / M_NH3 x LHV_H2"),
    ("share_MWh_NH3_per_tNH3", "value", "value", "pure-substance heating value", "the ammonia LHV is a property of the substance (5.166 MWh/t = 18.6 GJ/t); no range"),
    ("liquid_ship_mwh_per_t_ammonia", "value", "value", "pure-substance heating value", "the ammonia LHV is a property of the substance (5.166 MWh/t = 18.6 GJ/t); no range"),
    ("liquid_ship_mwh_per_t_methanol", "value", "value", "pure-substance heating value", "the methanol LHV is a property of the substance (5.528 MWh/t = 19.9 GJ/t); no range"),
    ("liquid_ship_mwh_per_t_oil", None, "lhv_ch4_mwh_t", "heating value above any hydrocarbon", "no hydrocarbon has a higher LHV per mass than methane (registry biomass_methane_lhv 50.04 GJ/t = 13.9 MWh/t)"),
    ("conv_gj_per_t_natural_gas_mass", None, "lhv_ch4_gj_t", "heating value above any hydrocarbon", "natural gas (hydrocarbons and inerts) cannot exceed the LHV of methane (registry biomass_methane_lhv 50.04 GJ/t)"),
    ("liquid_ship_hours_per_year", None, "hours_per_year", "hours above the year", "operating hours per year cannot exceed 8,760 h"),
]


def physics_corrections(reg: pd.DataFrame) -> tuple:
    """Full replacement rows of the PHYSICS_FIXES parameters (only sensitivity_low / sensitivity_high, description and decision_ref change) and the fix log."""
    L = physics_limits(reg); R = reg.set_index("param_id"); rows, log = [], []

    def res(k, old, v):
        if k is None:
            return float(old) if old != "" else None
        if k == "value":
            return v
        return float(k) if isinstance(k, float) else float(L[k])

    for pid, lo, hi, cls, basis in PHYSICS_FIXES:
        x = R.loc[pid].to_dict(); v = float(x["value"]); olo, ohi = x["sensitivity_low"], x["sensitivity_high"]
        nlo, nhi = res(lo, olo, v), res(hi, ohi, v)
        note = ""
        if nhi is not None and nhi < v - 1e-12:
            note = f"main value {v:g} is above the physical upper bound {nhi:.6g} by {v - nhi:.6g} ({(v - nhi) / nhi:.3%}); main value not changed (instruction section 4.1)"
        if nlo is not None and nlo > v + 1e-12:
            note = f"main value {v:g} is below the physical lower bound {nlo:.6g}; main value not changed (instruction section 4.1)"
        y = dict(x, param_id=pid, sensitivity_low=fmt(nlo), sensitivity_high=fmt(nhi),
                 description=f"{x['description']} | [V4 D1, decision 212 (a)] registered range clipped to the physical bound ({basis}); range {olo}-{ohi} -> {fmt(nlo)}-{fmt(nhi)}; a physical limit, not data",
                 decision_ref=(x["decision_ref"] + ", 212 (a)").strip(", "))
        rows.append({c: y[c] for c in COLUMNS})
        log.append(dict(param_id=pid, unit=x["unit"], value=v, old_low=olo, old_high=ohi, new_low=fmt(nlo), new_high=fmt(nhi), cls=cls, basis=basis, main_value_note=note))
    return pd.DataFrame(rows, columns=COLUMNS), log


def proxy_rows(reg: pd.DataFrame) -> pd.DataFrame:
    """Registry biomass cost rows priced with the uniform proxy of unsourced residues (cassava / coconut / other crop residues)."""
    return reg[reg.param_id.str.startswith("biomass_cost_") & reg.source.str.startswith(MISSING_COST_PROXY_SOURCE)]


def missing_cost_row(r: Registry, reg: pd.DataFrame) -> None:
    peers = proxy_rows(reg)
    vals = sorted(set(peers.value.astype(float)))
    if len(vals) != 1:
        raise SystemExit(f"the registry proxy rows of unsourced residues carry {len(vals)} values: {vals}")
    lo = sorted(set(peers.sensitivity_low.astype(float))); hi = sorted(set(peers.sensitivity_high.astype(float)))
    p0 = peers.iloc[0]
    pend = reg[reg.param_id.str.startswith("biomass_cost_") & (reg.status == "DATA_PENDING")].param_id.tolist()
    r.add(MISSING_COST_PROXY_ID,
          "uniform feedstock cost of biomass pools whose registry cost is DATA_PENDING and whose cost column is empty (research.biomass.missing_cost_rule = "
          f"proxy; v4 main; v3.1 = zero, i.e. 0 EUR/MWh): the registry proxy of unsourced residues ({len(peers)} rows biomass_cost_*_cassava / coconut / "
          f"other_crop_residues: {MISSING_COST_PROXY_SOURCE}); applies to {', '.join(pend)}. Grade for oil palm trunk: D (generic residue proxy, no trunk "
          "felling / chipping / transport cost; candidates in DOWNLOAD_CANDIDATES.csv of V4 D1)",
          vals[0], "EUR2020/MWh", "C", f"{MISSING_COST_PROXY_SOURCE} (registry proxy of unsourced residues; decisions 212 item 5, 215 item 5)",
          f"research_inputs/registry_v5/DATA_REGISTRY.csv: biomass_cost_* rows whose source starts with '{MISSING_COST_PROXY_SOURCE}' ({len(peers)} rows; {p0.source_locator})",
          p0.source_sha256, sensitivity_low=lo[0] if len(lo) == 1 else None, sensitivity_high=hi[0] if len(hi) == 1 else None,
          decision_ref="212 item 5, 215 item 5", status="REGISTERED")


def main():
    reg = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False)
    r = Registry(SCRIPT)
    missing_cost_row(r, reg)
    out = REG_DIR / "fragments" / "v4_d1.csv"
    r.write(out)
    print(out, len(r.rows))
    head = REG_DIR / "fragments" / "v4_d1_corrections.csv"
    import d1_registry as DR
    base, _ = DR.assemble([c for c in DR.CORRECTIONS if c != "v4_d1_corrections"])   # the rows as they stand without the D1 corrections (idempotent)
    corr, log = physics_corrections(base)
    corr.sort_values("param_id").to_csv(head, index=False, lineterminator="\n")
    for x in log:
        print(" ", x["param_id"], x["old_low"], x["old_high"], "->", x["new_low"], x["new_high"], x["main_value_note"])


if __name__ == "__main__":
    main()
