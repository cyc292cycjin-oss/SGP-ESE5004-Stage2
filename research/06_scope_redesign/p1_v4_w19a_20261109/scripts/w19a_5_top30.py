"""W19a section 5.3: status of the D2b (= W10 / D2a method) top 30 at the W14 package COMMIT.

Status classes: REPLACED (v4 main value from a switch / table, old row = fallback) | VERIFIED_RANGE (value checked against
sources and a range registered, main kept) | METHOD_OR_SCENARIO (rule / scenario choice, no data upgrade possible) | OPEN (not
treated; a physical clip of the registered range alone does not count as treated). The basis of each entry is the registry row
change at 26c2e47d (evidence/REGISTRY_C462_CLASSES.csv) and the D1 / D2a / D2b / D2c deliverables named in the column 'evidence'.
The reviewer's 11-09 05:00 classification was not found in the workspace: column reviewer_0500 = 'not provided'.
"""
from pathlib import Path

import pandas as pd

D = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_w19a_20261109")
TOP30 = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_v4_d2b_20261108/RERANK_D2B_TOP30.csv")

MAP = {
    "scenario_switch_wacc_mode": ("METHOD_OR_SCENARIO", "main uniform 7 % (decision 90 / 111); country_specific is a W19 sensitivity; basis unification needed first (W19a section 3)", "W19a section 3; D2b 4.8 (NOTE ONLY)"),
    "share_transport_electric_efficiency": ("VERIFIED_RANGE", "D2b 4.4 KEEP + RANGE: ASEAN fleet ratio mid 3.367 within 10 % of the model 3.31; range 33.93-76.86 registered", "D2b DATA_UPGRADES 4.4; registry range changed"),
    "co2_injection_cap_unified_KH": ("OPEN", "registered range 1.8-900 Mt/a (IJGGC 2014 low / hydrodynamic high) unchanged; W19a section 2: mechanism, bracket and PROPOSED range (registry not changed)", "W19a section 2; KH_CO2_ACCOUNT.csv"),
    "fuel_price_lng_regasification_adder": ("REPLACED", "v4 main v4_lng_regas_adder_asean_tariffs 2.0507 EUR2020/MWh (switch lng_regas_adder = asean_tariffs, C); 1.26 = v3.1 fallback; range 1.80-4.77", "D2b DATA_UPGRADES 4.1"),
    "offwind_alpha_calibration_rule": ("VERIFIED_RANGE", "D2b 4.6: coefficient 0.849-1.042 (mid 0.896) registered as v4_offwind_alpha_vn_reference_area (SENSITIVITY, C); not applied, alpha stays 1.0 (one reference area)", "D2b DATA_UPGRADES 4.6"),
    "renewable_cap_built_solar_rooftop_MY": ("VERIFIED_RANGE", "D2b 4.7 RANGE ONLY: low end = SEDA MyRER 42 GW (one source lineage); value kept", "D2b DATA_UPGRADES 4.7"),
    "share_bev_charge_efficiency": ("OPEN", "D1 212 (a) clipped the range at the physical bound 1.0 only; the PyPSA-Eur value is not checked against ASEAN data", "D1 (registry desc+ '[V4 D1, decision 212 (a)]')"),
    "share_transport_ice_efficiency": ("VERIFIED_RANGE", "covered by D2b 4.4 through the electric / combustion fleet ratio (value kept); the range is registered on the electric-efficiency row only, this row unchanged", "D2b DATA_UPGRADES 4.4"),
    "gas_production_node_allocation_TH": ("METHOD_OR_SCENARIO", "node allocation rule gem_fields vs load_shares (discrete); field-level production and landing points would be a data upgrade (W10 candidate, not done)", "W10 TOP30; registry unchanged"),
    "share_shipping_methanol_share_2050": ("METHOD_OR_SCENARIO", "shipping fuel scenario (PyPSA-Eur trajectory 1.0 in 2050); scenario choice, not data", "W10 0.1 item 2 (route shares = scenario)"),
    "onwind_alpha_MY": ("OPEN", "registered range 0.91-1.29 unchanged; no measured wind-farm CF used", "registry unchanged"),
    "co2_ship_chain_fixed_cost": ("VERIFIED_RANGE", "D2b 4.2 KEEP + RANGE: 10.03-14.29 EUR2020/t from ZEP 2011 / IEAGHG 2020 / BEIS 2018 (derived split); value 11.42 kept", "D2b DATA_UPGRADES 4.2"),
    "share_land_transport_electric_share_2050": ("METHOD_OR_SCENARIO", "electrification share of land transport = scenario (W10 0.1 item 2)", "W10 0.1 item 2"),
    "lng_terminal_expansion_capex_main": ("OPEN", "PyPSA-Eur code constant 8,020 EUR/MW/a; no ASEAN terminal unit cost (IGU 2024 candidate in W10 download list)", "registry unchanged"),
    "gas_production_node_allocation_MY": ("METHOD_OR_SCENARIO", "as TH: node allocation rule (discrete)", "registry unchanged"),
    "ev_annual_km_per_vehicle": ("OPEN", "C-grade assumption 12,000 km; range 6,000-24,000 unchanged", "registry unchanged"),
    "xb_stock_la_th_dedicated_lines": ("OPEN", "DATA_PENDING LA-TH dedicated lines (rated capacities not sourced)", "registry unchanged"),
    "onwind_alpha_MM": ("OPEN", "as onwind_alpha_MY", "registry unchanged"),
    "renewable_cap_built_solar_rooftop_SG": ("OPEN", "registered range +-50 % unchanged", "registry unchanged"),
    "share_bev_dsm_restriction_value": ("OPEN", "PyPSA-Eur default 0.8; range 0.64-0.96 unchanged", "registry unchanged"),
    "share_MWh_MeOH_per_MWh_H2": ("VERIFIED_RANGE", "D1 212 (a): value 0.8787 = stoichiometric maximum M_MeOH x LHV_MeOH / (3 M_H2 x LHV_H2) (physical fact); range clipped to 0.703-0.879, i.e. only lower efficiencies remain", "D1 (registry desc+)"),
    "biomass_potential_ID_oil_palm_trunk": ("REPLACED", "v4 main T06: 158.46 -> 24.14 TWh (measured trunk dry mass 0.2834 t DM/palm x LHV_dry; D2c); row = v3.1 fallback with range 23.33-49.67 TWh", "D2c REPORT 0; REGISTRY_C462_CLASSES (b)"),
    "co2_ship_chain_per_km_cost": ("VERIFIED_RANGE", "D2b 4.2 KEEP + RANGE: slope 0.00295-0.00553 EUR2020/(t km) (ZEP 2011 OLS); value kept", "D2b DATA_UPGRADES 4.2"),
    "co2_sequestration_cost_price_year": ("VERIFIED_RANGE", "D2b 4.3: DATA_PENDING -> 2020 by INFERENCE (PyPSA-Eur release history), range 2015-2020; 30 EUR/t unchanged", "D2b DATA_UPGRADES 4.3"),
    "onwind_alpha_LA": ("OPEN", "as onwind_alpha_MY", "registry unchanged"),
    "share_MWh_MeOH_per_MWh_e": ("OPEN", "PyPSA-Eur 3.6907; range unchanged (not a physical bound case)", "registry unchanged"),
    "th_my_line91_s_nom_2025": ("OPEN", "80 MW = APG TH-MY 380 MW minus the 300 MW HVDC (decision 97 a); the AC rating of line 91 itself is not sourced (W10 download candidate); range 80-380 unchanged", "registry unchanged"),
    "share_agriculture_machinery_electric_efficiency": ("OPEN", "PyPSA-Eur agriculture shares applied to ASEAN; unchanged", "registry unchanged"),
    "biomass_msw_ch4_yield_food_wet": ("OPEN", "IPCC 2006 default DOC with the IPCC min / max as range (registered since D1); no ASEAN measurement", "registry unchanged"),
    "biomass_potential_ID_oil_palm_efb": ("REPLACED", "v4 main T04 / T06: 216.63 -> 103.98 TWh (EFB energy per wet t 7.2 GJ = (1 - 0.60) x 18.0, factor 0.48; D2a)", "D2a section 3.2; REGISTRY_C462_CLASSES (b)"),
}


def main():
    t = pd.read_csv(TOP30)
    cls = pd.read_csv(D / "evidence" / "REGISTRY_C462_CLASSES.csv", dtype=str, keep_default_na=False).set_index("param_id")
    rows = []
    for _, r in t.iterrows():
        p = r.param_id
        st, basis, ev = MAP[p]
        c = cls.loc[p] if p in cls.index else None
        rows.append(dict(rank_d2b=int(r["rank"]), param_id=p, country=r.country if isinstance(r.country, str) else "", mechanism=r.mechanism, bias_class=r.bias_class,
                         dB6_first_order_bn=round(float(r.dB6) / 1e9, 4), owen_max_country=r.owen_max_country, owen_max_bn=round(float(r.owen_max_eur) / 1e9, 4),
                         status_w19a=st, basis=basis, evidence=ev, registry_class_462=(c.cls if c is not None else "not in the 462"),
                         registry_change=(c.changed_columns if c is not None else ""), replaced_by=(c.replaced_by if c is not None else ""),
                         reviewer_0500="not provided (no file in the workspace)", tag="VERIFIED (registry diff) / INFERENCE (status wording)"))
    out = pd.DataFrame(rows)
    # consistency: REPLACED <-> class b, VERIFIED_RANGE mostly class c / d
    out["check"] = [("ok" if (s == "REPLACED") == (k == "b") else "CHECK") for s, k in zip(out.status_w19a, out.registry_class_462)]
    out.to_csv(D / "TOP30_STATUS.csv", index=False)
    print(out.status_w19a.value_counts().to_string())
    print(out[["rank_d2b", "param_id", "status_w19a", "registry_class_462", "check"]].to_string())


if __name__ == "__main__":
    main()
