"""V4 D2a (decisions 218-220; V4_D2A_INSTRUCTION.md section 3): registry fragment research_inputs/registry_v5/fragments/v4_d2a.csv, assembled into
DATA_REGISTRY.csv by scripts_project/d1_registry.py.

    PYTHONHASHSEED=0 python scripts_project/v4_d2a_registry.py && python scripts_project/d1_registry.py

  T04 (section 3.2)  PALM_RESIDUE_BASIS_T04.csv (file row) and the moisture / dry LHV / energy-per-wet-tonne of EFB, fibre, PKS (evidence/T04_LITERATURE.json of
                     the D2a delivery); the T04 potential tables (file rows).
  PHS (section 3.3)  PHS_STOCK_RECLASS_V4.csv (file row) and the Bhumibol split (171 MW pumped, 608.2 MW conventional, 170.8 MW GEM double count).
  PHS (section 3.4)  PHS_ASEAN_CASE_V4.csv (file row), the Lu et al. (2021) costs in EUR2020 and the ANU 2025 short-list energy caps (SENSITIVITY rows).
Deterministic (no time stamps). Nothing is solved.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from d1_common import REG_DIR, Registry   # noqa: E402
from v4_common import BIOMASS_DIR, ROOT, sha256   # noqa: E402

SCRIPT = "scripts_project/v4_d2a_registry.py"
D2A = "research/06_scope_redesign/p1_v4_d2a_20261107"
FLEET = ROOT / "research_inputs/fleet_v5"; POT = ROOT / "research_inputs/potentials_v5"


def file_row(r: Registry, pid: str, p: Path, desc: str, tier: str, dec: str) -> None:
    r.add(pid, desc, int(p.stat().st_size), "bytes", tier, "V4 D2a (section 3; evidence in the D2a delivery)", f"file: {p.relative_to(ROOT)}", sha256(p), decision_ref=dec, status="REFERENCE_ONLY")


def main():
    reg = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    ev_t04 = ROOT / D2A / "evidence/T04_LITERATURE.json"; ev_phs = ROOT / D2A / "evidence/PHS_STOCK_LITERATURE.json"
    for ev in (ev_t04, ev_phs):
        if not ev.exists():
            raise SystemExit(f"{ev} missing: sync the D2a delivery folder into the repository first")
    r = Registry(SCRIPT)
    # ---- T04
    basis = BIOMASS_DIR / "PALM_RESIDUE_BASIS_T04.csv"
    file_row(r, "v4_palm_residue_basis_table", basis, "T04: mass basis (wet FFB shares of IRENA 2022 Box 4) and heating-value basis of the palm residues; moisture_ar, LHV_dry, energy per wet tonne, verdict per category (V4 D2a section 3.2)", "C", "220")
    file_row(r, "v4_biomass_potential_2050_t04", BIOMASS_DIR / "BIOMASS_POTENTIAL_2050_V4_T04.csv", "solid-biomass potential of the v4 main set: W08 F3 / F4 adjustments plus the T04 palm-residue basis (EFB x 0.48, fibre x 0.76 before the in-mill deductions); research.demand.v4.biomass_potential = v4_adjusted_t04", "C", "209, 210, 220")
    file_row(r, "v4_biomass_potential_adjustment_t04", BIOMASS_DIR / "BIOMASS_POTENTIAL_ADJ_V4_T04.csv", "F3 / F4 / F5 (T04) adjustment by country and category", "C", "209, 210, 220")
    t = pd.read_csv(basis, keep_default_na=False)
    for x in t.itertuples():
        if x.moisture_ar_mid == "":
            continue
        cat = x.category.replace("oil_palm_", "")
        st = "REGISTERED" if str(x.applied) == "True" else "SENSITIVITY"
        r.add(f"v4_palm_residue_moisture_ar_{cat}", f"{x.category}: as-received moisture (wet basis) of the mill residue; T04 verdict: {x.verdict}; sources {x.sources} of evidence/T04_LITERATURE.json",
              float(x.moisture_ar_mid), "share", x.grade if x.grade in ("A", "B", "C") else "C", "Phyllis2 (TNO) / MPOB POEB 91 / Abdullah & Gerhauser 2008 / Abdullah & Sulaiman 2013 (see T04_LITERATURE.json)",
              f"{D2A}/evidence/T04_LITERATURE.json; PALM_RESIDUE_BASIS_T04.csv", sha256(ev_t04), sensitivity_low=float(x.moisture_ar_low), sensitivity_high=float(x.moisture_ar_high), decision_ref="220", status=st)
        if x.lhv_dry_gj_t_mid != "":
            r.add(f"v4_palm_residue_lhv_dry_{cat}", f"{x.category}: lower heating value, dry basis (GJ/t); sources {x.sources}", float(x.lhv_dry_gj_t_mid), "GJ/t dry", x.grade if x.grade in ("A", "B", "C") else "C",
                  "Phyllis2 (TNO) entries and the literature they cite; MPOB POEB 91; Fuel 87 (2008)", f"{D2A}/evidence/T04_LITERATURE.json; PALM_RESIDUE_BASIS_T04.csv", sha256(ev_t04),
                  sensitivity_low=float(x.lhv_dry_gj_t_low), sensitivity_high=float(x.lhv_dry_gj_t_high), decision_ref="220", status=st)
            r.add(f"v4_palm_residue_energy_per_wet_t_{cat}", f"{x.category}: energy per wet tonne used by the v4 main potential (T04): " + (f"(1 - moisture) x LHV_dry = {float(x.consistent_gj_per_wet_t_mid):.3f} GJ/t (W08: 15 GJ/t on the wet mass; factor {float(x.factor_mid):.4f})" if str(x.applied) == "True" else f"15 GJ/t kept ({x.verdict})"),
                  float(x.consistent_gj_per_wet_t_mid) if str(x.applied) == "True" else 15.0, "GJ per wet t", x.grade if x.grade in ("A", "B", "C") else "C", "derived: PALM_RESIDUE_BASIS_T04.csv",
                  f"scripts_project/v4_biomass_potential.py basis_factors; {D2A}/evidence/T04_LITERATURE.json", sha256(basis), sensitivity_low=15.0 * float(x.factor_low), sensitivity_high=15.0 * float(x.factor_high), decision_ref="220", status=st)
    # ---- PHS stock reclassification
    recl = FLEET / "PHS_STOCK_RECLASS_V4.csv"
    file_row(r, "v4_phs_stock_reclass_table", recl, "frozen-stock PHS groups holding conventional reservoir units: Bhumibol TH2 4 950 MW -> 171 MW PHS + 608.2 MW reservoir + 170.8 MW GEM double count (research.fleet.phs_stock_reclass; V4 D2a section 3.3)", "B", "220")
    for pid, val, desc in (("v4_phs_stock_bhumibol_pumped_mw", 171.0, "Bhumibol unit 8 reversible pump-turbine (EGAT: Units 8 (pumped storage) 171 MW; GEM G100000604991 171 MW pumped storage 1996)"),
                           ("v4_phs_stock_bhumibol_conventional_mw", 608.2, "Bhumibol conventional units 1-7 = 6 x 82.2 + 115 MW (EGAT characteristics table; ANDRITZ Hydro News 34); reclassified from 'PHS existing' to 'hydro existing' at TH2 4"),
                           ("v4_phs_stock_bhumibol_gem_double_count_mw", 170.8, "GEM lists 779 MW conventional + 171 MW pumped while EGAT's contracted 779.20 MW already contains unit 8: 170.8 MW counted twice in the frozen base (950 MW), dropped"),
                           ("v4_phs_stock_th_pumped_total_mw", 1531.0, "TH pumped storage after the reclassification = Lam Ta Khong 1,000 + Srinagarind 360 + Bhumibol 171 MW = IHA 2024 (T-20); model before: 2,310 MW")):
        r.add(pid, desc, val, "MW", "B", "EGAT Bhumibol Dam characteristics (egat.co.th, accessed 2026-11-07); ANDRITZ Hydro News 34; IHA Thailand country profile 2024; GEM GIPT 2026-09",
              f"{D2A}/evidence/PHS_STOCK_LITERATURE.json (T-01 - T-05, T-20)", sha256(ev_phs), country="TH", decision_ref="220", status="REGISTERED")
    r.add("v4_phs_stock_ph_kalayaan_mw", "PH Kalayaan I + II = 366 + 370 MW (GEM; DOE 2021 installed 736.0, dependable 720.0); IHA 2024 729 MW is a rating convention (CBK guaranteed 684.6, owner 734.36), not a classification error: model value kept; Pantabangan-Aya 120 MW (S4B1) is a new pumped-storage project on the Aya / Masiway reservoirs (First Gen, MOA 2026-06-30, COD target 2030): PHS classification kept, GEM status 'construction' is early",
          736.0, "MW", "B", "GEM wiki Kalayaan 1 / 2; DOE LOEPP Luzon 2021 (snippet); AboitizPower 2025; IHA East Asia & Pacific profile; First Philippine Holdings 2026-07-06",
          f"{D2A}/evidence/PHS_STOCK_LITERATURE.json (P-01 - P-19)", sha256(ev_phs), country="PH", decision_ref="220", status="REFERENCE_ONLY")
    # ---- PHS asean case
    asean = POT / "PHS_ASEAN_CASE_V4.csv"
    file_row(r, "v4_phs_asean_case_table", asean, "research.supply.phs_case = asean (W19 sensitivity): Lu et al. 2021 costs in EUR2020, ANU 2025 short-list energy caps per country, node rule", "C", "220")
    t = pd.read_csv(asean, keep_default_na=False).set_index("country")
    fx = float(reg.at["fx_usd_to_eur_2020", "value"])
    row = t.loc["ID"]
    for pid, val, unit, desc in (("phs_asean_power_cost_eur2020_per_kw", 560.0 * fx, "EUR2020/kW", "Lu et al. 2021 Table 3 power cost 560 USD2020/kW x fx_usd_to_eur_2020"),
                                 ("phs_asean_energy_cost_eur2020_per_kwh", 50.0 * fx, "EUR2020/kWh", "Lu et al. 2021 Table 3 energy cost 50 USD2020/kWh x fx_usd_to_eur_2020"),
                                 ("phs_asean_fom_eur2020_per_kw_a", 7.0 * fx, "EUR2020/kW/a", "Lu et al. 2021 Table 3 fixed O&M 7 USD2020/kW/a x fx_usd_to_eur_2020"),
                                 ("phs_asean_lifetime_a", 50.0, "years", "Lu et al. 2021 Table 3 lifetime 50 a"),
                                 ("phs_asean_round_trip", 0.80, "per unit", "Lu et al. 2021 / ANU 2025 round-trip efficiency 0.80 (technology-data PHS 0.75 in the main case)")):
        for col, v in (("power_eur2020_per_kw", 560.0 * fx), ("energy_eur2020_per_kwh", 50.0 * fx), ("fom_eur2020_per_kw_a", 7.0 * fx)):
            if abs(float(row[col]) - v) > 1e-6:
                raise SystemExit(f"PHS_ASEAN_CASE_V4.csv {col} {row[col]} != {v} (fx {fx})")
        r.add(pid, desc + " (sensitivity case asean; main = technology-data v0.15.0 PHS 2,297 EUR2020/kW, 6 h; V4 D1 PHS_PROPOSAL.md section 4)", val, unit, "B",
              "Lu, Blakers, Stocks, Do (2021) Energy 236:121387, Table 3; registry fx_usd_to_eur_2020", "research/06_scope_redesign/p1_v4_d1_20261107/evidence/PHS_LITERATURE.json; PHS_ASEAN_CASE_V4.csv", sha256(asean),
              decision_ref="220", status="SENSITIVITY")
    for c in t.index:
        if str(t.at[c, "anu_shortlist_twh"]) != "":
            r.add(f"phs_asean_energy_cap_{c}", f"{c} energy cap of the asean-case PHS tiers = ANU 2025 A/AA/AAA short list {t.at[c, 'anu_sites_1500_500_50_gwh']} sites (1500 / 500 / 50 GWh), TWh (a selection of sites, not the resource; node rule: {t.at[c, 'node_rule']})",
                  float(t.at[c, "anu_shortlist_twh"]) * 1e6, "MWh", "B", "Blakers, Weber, Silalahi (2025) Progress in Energy 7:022004 (ANU short list; V4 D1 PHS_PROPOSAL.md section 3)",
                  "research/06_scope_redesign/p1_v4_d1_20261107/evidence/PHS_LITERATURE.json; PHS_ASEAN_CASE_V4.csv", sha256(asean), country=c, decision_ref="220", status="SENSITIVITY")
    out = REG_DIR / "fragments" / "v4_d2a.csv"
    r.write(out)
    print(out, len(r.rows))


if __name__ == "__main__":
    main()
