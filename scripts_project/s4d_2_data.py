"""S4D-2 data (decision 92, revised: intra-ASEAN CO2 shipping in both scenarios); registry fragment s4d_2.

Basis (instruction S4D-2 item 1): decisions 18 and 44 cut only cross-border network infrastructure when 'not interconnected'; maritime trade stays
in both scenarios and the value of interconnection comes from lines and pipelines only. CO2 shipping is maritime trade, treated like the liquid
fuels: tagged border_class = maritime_trade (not cross_border), outside B5 and the cross-border switches.

Cost (item 3): IEAGHG (2004) PH4/30 Table 5-3, the same source and components as the extra-ASEAN price (decision 89, s4c_4_data.py): liquefaction
(CO2 at 100 bar) 3.3 + 6.0, ships (capital, crew / insurance / maintenance, fuel) 60.0 at 3,000 km and 107.0 at 6,000 km, harbour fee 11.4, buffer
tanks 16.5 + 7.5, loading / unloading 0.9 + 2.0 million US$2004 per year at 6.205 Mt/a. Only the ship component varies with distance; it is linear
in the one-way distance (fleet size ~ round-trip time = 2 d / speed + port time), so per tonne: fixed 9.766 US$2004/t (ships at zero distance
13.0 M$/a = the port-time share, by the line through the two tabulated points) + 0.0025248 US$2004/(t km); the line reproduces the printed
totals 17.3 / 24.9 US$/t. The extension below 3,000 km follows the same structure (INFERENCE); GCCSI (2025) Table 3 quotes IEAGHG 2004 down to
200 km at about US$10/t, consistent with 10.27 on the line. Distance = great-circle distance between the origin coastal node and the landing
coastal node of the receiver x route factor (scripts_project/s4d_2_ship_routes.py: median sea-path / great-circle ratio over the candidate pairs,
derived from the model geometry, grade C, +-25 %). Storage: the receiver's national sequestration store 'co2 sequestered <ISO2>' (its unit cost
and its annual injection cap, decisions 28 / 20) - not added to the ship link.

    python scripts_project/s4d_2_data.py
"""
from __future__ import annotations

import json

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256
from s4c_4_data import HARBOUR, LIQ_100BAR, LOADING, SHIP, T_PER_YEAR, TANKS, URLS

SCRIPT = "scripts_project/s4d_2_data.py"
INSTRUCTION_SHA = "a35fa7d52c0d645830562e57fb242563b864994682eeb1ce6a2a8d59f73b2586"
OUT = ROOT / "research_inputs" / "co2_v5"
ROUTE_SENS = 0.25
CHAIN_SENS = 0.5


def main():
    R = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    f = float(R.at["conv_usd2004_to_eur2020", "value"])
    slope_musd = (SHIP[6000] - SHIP[3000]) / 3000.0
    ship0 = SHIP[3000] - 3000.0 * slope_musd
    fixed_usd = (LIQ_100BAR + ship0 + HARBOUR + TANKS + LOADING) * 1e6 / T_PER_YEAR
    per_km_usd = slope_musd * 1e6 / T_PER_YEAR
    check = {d: fixed_usd + per_km_usd * d for d in (200, 3000, 6000)}
    fixed, per_km = fixed_usd * f, per_km_usd * f
    routes = OUT / "CO2_SHIP_ROUTES_S4D2.csv"; rj = json.loads((OUT / "CO2_SHIP_ROUTES_S4D2.json").read_text())
    factor = float(rj["route_factor_median"])
    extra = float(R.at["co2_extra_asean_storage_cost", "value"])
    import yaml
    seq = float(yaml.safe_load((ROOT / "configs/research/baseline.yaml").read_text())["research"]["s2"]["co2"]["sequestration_cost_eur_per_t"])   # national store unit cost
    ieaghg = R.at["co2_extra_asean_shipping_chain_4500km", "source_sha256"]
    ins = "work/p1_step4d_20261017/S4D_CLAUDE_CODE_INSTRUCTION.md"; cfg = "configs/research/baseline.yaml"
    reg = Registry(SCRIPT)
    reg.add("s4d2_maritime_trade_basis", "Decision 92 (revised): decisions 18 and 44 cut only cross-border network infrastructure when not interconnected; maritime trade stays in both "
            "scenarios and the value of interconnection comes from lines and pipelines only. CO2 shipping is maritime trade like the liquid fuels: links carry border_class = "
            "maritime_trade, are not removed by the cross-border switches and are not counted by B5 (network components only)", "maritime_trade", "flag", "B",
            "S4D instruction S4D-2 items 1, 4; decisions 18, 44", ins, INSTRUCTION_SHA, decision_ref="92,18,44", status="REFERENCE_ONLY")
    reg.add("s4d2_shipping_structure", "Decision 92: for every coastal buffered node of country i and every other country j with a national injection cap > 0, one link "
            "'<node> co2 ship to <j>' from '<node> co2 stored' to 'co2 sequestered <j>' (enters j's national store: occupies j's annual cap, decision 28, and pays j's store unit "
            "cost; the export counts as abatement of i, decision 20 - it leaves i's captured-CO2 buffer and enters no atmosphere); landing node = coastal node of j with the "
            "shortest sea path (CO2_SHIP_ROUTES_S4D2.csv); both scenarios", "node_to_receiver_store", "flag", "B", "S4D instruction S4D-2 item 2", ins, INSTRUCTION_SHA,
            decision_ref="92,20,28", status="REFERENCE_ONLY")
    reg.add("co2_ship_chain_fixed_cost", f"Decision 92: distance-independent part of the IEAGHG 2004 shipping chain per tonne (liquefaction 100 bar {LIQ_100BAR} + ships at zero distance "
            f"{ship0:.2f} + harbour {HARBOUR} + buffer tanks {TANKS} + loading/unloading {LOADING} M US$2004/a over {T_PER_YEAR / 1e6:.3f} Mt/a = {fixed_usd:.4f} US$2004/t) x {f:.5f}; "
            f"line through Table 5-3 at 3,000 / 6,000 km (check {check[3000]:.2f} / {check[6000]:.2f} vs printed 17.3 / 24.9; {check[200]:.2f} at 200 km vs about 10 in GCCSI 2025 Table 3)",
            fixed, "EUR2020/tCO2", "C", "IEAGHG (2004) Ship Transport of CO2, PH4/30", f"{URLS['ieaghg2004']} Table 5-3 PDF p.32", ieaghg,
            sensitivity_low=fixed * (1 - CHAIN_SENS), sensitivity_high=fixed * (1 + CHAIN_SENS), decision_ref="92")
    reg.add("co2_ship_chain_per_km_cost", f"Decision 92: distance-dependent ship cost per tonne and km of one-way distance, ({SHIP[6000]} - {SHIP[3000]}) M US$2004/a / 3,000 km / "
            f"{T_PER_YEAR / 1e6:.3f} Mt/a = {per_km_usd:.7f} US$2004/(t km) x {f:.5f}", per_km, "EUR2020/(tCO2 km)", "C", "IEAGHG (2004) Ship Transport of CO2, PH4/30",
            f"{URLS['ieaghg2004']} Table 5-3 PDF p.32", ieaghg, sensitivity_low=per_km * (1 - CHAIN_SENS), sensitivity_high=per_km * (1 + CHAIN_SENS), decision_ref="92")
    reg.add("co2_ship_route_factor", f"Decision 92: route factor port-to-port sea distance / great-circle distance = {factor} (median over {rj['pairs_used']} candidate pairs; quartiles "
            f"{rj['quantiles']['0.25']} / {rj['quantiles']['0.75']}, p90 {rj['quantiles']['0.9']}), derived from the model geometry: shortest over-water paths on a "
            f"{rj['grid_deg']} degree grid outside the ASEAN land of the author country shapes (grid bias on straight over-water pairs "
            f"{rj['grid_bias_straight_pairs']['median_ratio']}); no published factor at hand and none in the S4D download category; first-batch sensitivity +-25 %",
            factor, "ratio", "C", "derived (scripts_project/s4d_2_ship_routes.py; author country_shapes)", "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.json",
            sha256(OUT / "CO2_SHIP_ROUTES_S4D2.json"), sensitivity_low=factor * (1 - ROUTE_SENS), sensitivity_high=factor * (1 + ROUTE_SENS), decision_ref="92")
    reg.add("co2_ship_routes_table", f"Decision 92: candidate shipping pairs ({rj['pairs']}): origin coastal buffered node, receiver, landing node (shortest sea path), great-circle km "
            "between the buses (used with the route factor), sea-path km (reference: pair-specific alternative), ratio, nearest-by-great-circle landing for reference",
            "table", "flag", "B", "derived (scripts_project/s4d_2_ship_routes.py)", "research_inputs/co2_v5/CO2_SHIP_ROUTES_S4D2.csv", sha256(routes), decision_ref="92",
            status="REFERENCE_ONLY")
    reg.add("co2_intra_asean_shipping_switch", "research.co2.intra_asean_shipping values: on (main, decision 92, both scenarios) | off; research.co2.ship_route_factor_scale "
            "multiplies co2_ship_route_factor (1.0 main; 0.75 / 1.25 first-batch sensitivity)", "on|off", "flag", "B", "S4D instruction S4D-2 items 2-4, S4D-6 item 2", cfg,
            INSTRUCTION_SHA, decision_ref="92", status="REFERENCE_ONLY")
    floor = fixed + seq
    reg.add("co2_intra_vs_extra_asean_cost_note", f"Cost ordering (for the user): intra-ASEAN shipping costs at least {fixed:.2f} EUR/t (chain at zero distance) + the receiver's "
            f"sequestration {seq:.0f} EUR/t (PyPSA-Eur default, research.s2.co2.sequestration_cost_eur_per_t) = {floor:.2f} EUR/t, above the extra-ASEAN price {extra:.2f} "
            "EUR/t (decision 89: IEAGHG chain at 4,500 km + ZEP 2011 offshore saline aquifer Medium 16.05 EUR2020/t). With uncapped extra-ASEAN storage the shipping option is "
            "dominated at every distance in the main run; it competes only when the extra-ASEAN price rises (e.g. +50 % sensitivity: 61.1 EUR/t) or if the two storage "
            "costs are put on one basis (user decision; not changed here)", "dominated_in_main", "flag", "B", "registry co2_extra_asean_storage_cost; configs/research/baseline.yaml",
            cfg, INSTRUCTION_SHA, decision_ref="92,89", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4d_2.csv")
    print(dict(f=f, fixed_usd=fixed_usd, per_km_usd=per_km_usd, check=check, fixed_eur=fixed, per_km_eur=per_km, factor=factor, floor=floor, extra=extra))


if __name__ == "__main__":
    main()
