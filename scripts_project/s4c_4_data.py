"""S4C-4 data (decision 89): unit cost of the extra-ASEAN CO2 storage option = CO2 liquefaction + ocean shipping over a South-East Asia ->
Australia-scale distance (3,000-6,000 km) + offshore storage, in EUR2020 per tonne exported; registry fragment s4c_4.

Sources (public, downloaded under working principle 7 category 1; files and SHA256 in work/p1_step4c_20261016/sources_s4c/co2):
  * IEAGHG (2004) "Ship Transport of CO2", report PH4/30 (study by Mitsubishi Heavy Industries), Table 5-3 "Total cost of CO2 marine
    transportation" (PDF page 32): CO2 supplied to the liquefaction plant at 100 bar (the model's capture links already carry the
    compression electricity, technology-data 'compression-electricity-input', and the report says its 10 MPa costs are the ones to combine
    with published capture costs), 50,000 t ships, 15/16 kn, 6.205 Mt/a, capital charge 11.02 %/a (= annuity of 10 %, 25 years, IEA GHG
    standard criteria), US$ of the report year (July 2004). Components per year (million US$): liquefaction capital 3.3 + running 6.0;
    ships capital / crew-insurance-maintenance / fuel 36.1 / 16.4 / 7.5 at 3,000 km and 63.3 / 28.7 / 15.0 at 6,000 km; harbour fee 11.4;
    buffer tanks capital 16.5 + running 7.5; loading / unloading 0.9 + 2.0; totals 17.3 and 24.9 US$/t. Table 5-2 (CO2 at 0.1 MPa):
    liquefaction 8.8 + 45.5 -> 24.6 and 32.2 US$/t (reference). The report places Japan - northern Australia at about 6,000 km.
  * ZEP (2011) "The Costs of CO2 Capture, Transport and Storage - Post-demonstration CCS in the EU" (Figure 19, report page 35): storage cost
    per case, EUR / t CO2 stored, Low / Medium / High; offshore saline aquifer, no legacy wells 6 / 14 / 20 (main: Medium; the uncapped
    sink of decision 89 matches the large-capacity saline aquifers), offshore DOGF without / with legacy wells 3 / 10 / 14 and 2 / 6 / 9;
    costs referenced to the second quarter of 2009, 8 % real WACC.
  * Cross-checks only: ERIA (2022) Study on the Potential for Promoting CCUS in ASEAN Countries Vol. II, Table 2.8 (ZEP ship costs up to
    1,500 km; 'a distance of at least 3,000-5,000 km' needed in ASEAN, no cost given); GCCSI (2025) Needs, Opportunities and Prospects for
    CO2 Shipping in CCS Projects, Table 3 (IEAGHG 2004 the only published source beyond 2,000 km; other studies US$9-50/t at <= 2,000 km);
    IEAGHG (2020-10) CO2 shipping infrastructures (1,000 km, 1.4-1.8 Mt/a: 41-44 US$/t levelised); IEAGHG (2025-08) T&S cost review
    (Clarksons 2024: GBP 12-45/t for 200-1,200 nm in north-west Europe).

Distance assumption: 4,500 km = midpoint of the instruction range 3,000-6,000 km, linear between the two tabulated IEAGHG distances (only the
ship component changes between them). Conversion: US$2004 -> US$2020 with the US GDP implicit price deflator (FRED A191RD3A086NBEA, pinned
research_inputs/registry_v5/sources/A191RD3A086NBEA.csv: 2004 = 79.077, 2020 = 105.377) -> EUR2020 at the registered ECB 2020 mean rate
(fx_usd_to_eur_2020); EUR2009 -> EUR2020 with the EA20 GDP deflator (research_inputs/prices/sources/ECB_EA20_GDP_DEFLATOR.csv). Grade C,
sensitivity +-50 % (instruction S4C-4 item 2).

    python scripts_project/s4c_4_data.py --sources /mnt/d/ResearchWorkspaces/ASEAN/work/p1_step4c_20261016/sources_s4c/co2
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4c_4_data.py"
INSTRUCTION_SHA = "e1bad922b036bcb425cb9b77853e5cc4f9ca771c59c90da1a23321b89a1dcdd3"
OUT = ROOT / "research_inputs" / "co2_v5"
T_PER_YEAR = 6205000.0
# IEAGHG 2004 Table 5-3 (100 bar), 50,000 t ships, 15/16 kn: million US$/a
LIQ_100BAR = 3.3 + 6.0
LIQ_ATM = 8.8 + 45.5   # Table 5-2 (0.1 MPa), reference
SHIP = {3000: 36.1 + 16.4 + 7.5, 6000: 63.3 + 28.7 + 15.0}
HARBOUR = 11.4
TANKS = 16.5 + 7.5
LOADING = 0.9 + 2.0
TABLE_TOTAL = {3000: 17.3, 6000: 24.9}   # US$/t as printed
DIST_MAIN = 4500.0
ZEP_STORAGE = {"offshore_SA_no_legacy": (6.0, 14.0, 20.0), "offshore_DOGF_no_legacy": (3.0, 10.0, 14.0), "offshore_DOGF_legacy": (2.0, 6.0, 9.0)}
MAIN_STORAGE = "offshore_SA_no_legacy"
SENS = 0.5
FILES = {"ieaghg2004": "IEAGHG_2004_PH4-30_Ship_Transport_of_CO2.pdf", "zep2011": "ZEP_2025_Report_Costs.pdf", "eria": "ERIA_CCUS_ASEAN_Vol_II.pdf",
         "gccsi2025": "GCCSI_2025_CO2_Shipping_in_CCS_Projects.pdf", "ieaghg2020": "IEAGHG_2020-10_CO2_Shipping_Infrastructures.pdf",
         "ieaghg2025": "IEAGHG_2025-08_CO2_Transport_Storage_Cost_Review.pdf"}
URLS = {"ieaghg2004": "https://publications.ieaghg.org/docs/General_Docs/Reports/PH4-30%20Ship%20Transport.pdf",
        "zep2011": "https://carbonmanagementeurope.org/wp-content/uploads/2025/07/ZEP-Report-Costs.pdf"}


def deflator(path, col_year, col_val, year, key=None):
    for r in csv.DictReader(open(path)):
        y = r[col_year][:4]
        if y == str(year) and (key is None or r.get("KEY") == key):
            return float(r[col_val])
    raise ValueError(f"{path}: no {year}")


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--sources", type=Path, required=True); a = ap.parse_args()
    shas = {k: sha256(a.sources / f) for k, f in FILES.items()}
    fred = ROOT / "research_inputs/registry_v5/sources/A191RD3A086NBEA.csv"
    us04, us20 = deflator(fred, "observation_date", "A191RD3A086NBEA", 2004), deflator(fred, "observation_date", "A191RD3A086NBEA", 2020)
    ea = ROOT / "research_inputs/prices/sources/ECB_EA20_GDP_DEFLATOR.csv"
    ea09, ea20 = deflator(ea, "TIME_PERIOD", "OBS_VALUE", 2009), deflator(ea, "TIME_PERIOD", "OBS_VALUE", 2020)
    reg_tab = pd.read_csv(REG_DIR / "DATA_REGISTRY.csv", dtype=str, keep_default_na=False).set_index("param_id")
    fx = float(reg_tab.at["fx_usd_to_eur_2020", "value"])
    f_usd = us20 / us04 * fx; f_eur = ea20 / ea09
    per_t = lambda musd: musd * 1e6 / T_PER_YEAR
    comp = {}
    for d in (3000, 6000):
        c = dict(liquefaction=per_t(LIQ_100BAR), ships=per_t(SHIP[d]), harbour=per_t(HARBOUR), buffer_tanks=per_t(TANKS), loading_unloading=per_t(LOADING))
        c["total"] = sum(c.values())
        if abs(c["total"] - TABLE_TOTAL[d]) > 0.06:
            raise ValueError(f"component sum {c['total']:.2f} differs from IEAGHG Table 5-3 total {TABLE_TOTAL[d]} at {d} km")
        comp[d] = c
    w = (DIST_MAIN - 3000) / 3000
    main_ship = {k: comp[3000][k] + w * (comp[6000][k] - comp[3000][k]) for k in comp[3000]}
    lo, me, hi = ZEP_STORAGE[MAIN_STORAGE]
    ship_eur = main_ship["total"] * f_usd; stor_eur = me * f_eur; total = ship_eur + stor_eur
    rows = []
    for d, c in [(3000, comp[3000]), (DIST_MAIN, main_ship), (6000, comp[6000])]:
        for k, v in c.items():
            rows.append(dict(item=f"shipping_chain_{k}", distance_km=d, value=v, unit="US$2004/tCO2", eur2020_per_t=v * f_usd,
                             source="IEAGHG 2004 PH4/30 Table 5-3 (100 bar, 50,000 t, 15/16 kn)" + (" - linear between 3,000 and 6,000 km" if d == DIST_MAIN else "")))
    rows.append(dict(item="liquefaction_atmospheric_inlet_reference", distance_km="", value=per_t(LIQ_ATM), unit="US$2004/tCO2", eur2020_per_t=per_t(LIQ_ATM) * f_usd,
                     source="IEAGHG 2004 PH4/30 Table 5-2 (0.1 MPa): replaces the 100 bar liquefaction if capture were delivered at atmospheric pressure"))
    for case, (l, m, h) in ZEP_STORAGE.items():
        for lab, v in [("low", l), ("medium", m), ("high", h)]:
            rows.append(dict(item=f"storage_{case}_{lab}", distance_km="", value=v, unit="EUR2009/tCO2", eur2020_per_t=v * f_eur, source="ZEP 2011 Figure 19 (Q2 2009 prices, WACC 8 %)"))
    rows.append(dict(item="unit_cost_main", distance_km=DIST_MAIN, value=total, unit="EUR2020/tCO2", eur2020_per_t=total,
                     source=f"shipping chain at {DIST_MAIN:.0f} km ({main_ship['total']:.2f} US$2004 x {f_usd:.5f}) + ZEP offshore SA medium ({me} EUR2009 x {f_eur:.5f})"))
    rows.append(dict(item="unit_cost_main_low_minus50", distance_km="", value=total * (1 - SENS), unit="EUR2020/tCO2", eur2020_per_t=total * (1 - SENS), source="grade C, -50 %"))
    rows.append(dict(item="unit_cost_main_high_plus50", distance_km="", value=total * (1 + SENS), unit="EUR2020/tCO2", eur2020_per_t=total * (1 + SENS), source="grade C, +50 %"))
    for d in (3000, 6000):
        rows.append(dict(item=f"unit_cost_at_{d}_km_reference", distance_km=d, value=comp[d]["total"] * f_usd + stor_eur, unit="EUR2020/tCO2", eur2020_per_t=comp[d]["total"] * f_usd + stor_eur, source="distance end points of the instruction range"))
    OUT.mkdir(parents=True, exist_ok=True)
    tab = OUT / "EXTRA_ASEAN_STORAGE_COST_S4C4.csv"
    write_csv(rows, tab, ["item", "distance_km", "value", "unit", "eur2020_per_t", "source"]); tsha = sha256(tab)
    src = f"ieaghg2004:{shas['ieaghg2004']}|zep2011:{shas['zep2011']}|table:{tsha}"
    reg = Registry(SCRIPT); cfg = "configs/research/baseline.yaml"
    reg.add("co2_extra_asean_storage_cost", "Decision 89: unit cost of exporting captured CO2 to an extra-ASEAN offshore sink = liquefaction (CO2 at 100 bar) + ship transport "
            f"({DIST_MAIN:.0f} km, midpoint of 3,000-6,000 km, IEAGHG 2004 Table 5-3, 50,000 t ships) + offshore saline-aquifer storage (ZEP 2011 Figure 19, Medium); "
            f"{main_ship['total']:.2f} US$2004/t x {f_usd:.4f} + {me} EUR2009/t x {f_eur:.4f}", total, "EUR2020/tCO2", "C",
            "IEAGHG (2004) Ship Transport of CO2, PH4/30; ZEP (2011) The Costs of CO2 Capture, Transport and Storage", f"{URLS['ieaghg2004']} Table 5-3; {URLS['zep2011']} Figure 19",
            src, sensitivity_low=total * (1 - SENS), sensitivity_high=total * (1 + SENS), decision_ref="89")
    reg.add("co2_extra_asean_shipping_chain_4500km", f"Liquefaction (100 bar inlet) + ships + harbour + buffer tanks + loading/unloading at {DIST_MAIN:.0f} km, linear between the IEAGHG 2004 Table 5-3 "
            f"values 3,000 km ({comp[3000]['total']:.2f}) and 6,000 km ({comp[6000]['total']:.2f}); 6.205 Mt/a, capital charge 11.02 %/a (10 %, 25 a)", main_ship["total"], "US$2004/tCO2", "C",
            "IEAGHG (2004) PH4/30", f"{URLS['ieaghg2004']} Table 5-3 PDF p.32", shas["ieaghg2004"], sensitivity_low=comp[3000]["total"], sensitivity_high=comp[6000]["total"], decision_ref="89")
    reg.add("co2_extra_asean_offshore_storage_eur2009", "Offshore storage, saline aquifer without legacy wells, ZEP 2011 Figure 19 Medium (Low 6 / High 20); DOGF alternatives 3/10/14 (no legacy wells), 2/6/9 (legacy wells)",
            me, "EUR2009/tCO2", "C", "ZEP (2011)", f"{URLS['zep2011']} Figure 19 (report p.35)", shas["zep2011"], sensitivity_low=lo, sensitivity_high=hi, decision_ref="89")
    reg.add("conv_usd2004_to_eur2020", f"US GDP deflator 2020/2004 ({us20}/{us04}) x ECB 2020 mean EUR/USD ({fx})", f_usd, "EUR2020/US$2004", "A",
            "FRED A191RD3A086NBEA; registry fx_usd_to_eur_2020", "research_inputs/registry_v5/sources/A191RD3A086NBEA.csv", sha256(fred), decision_ref="89")
    reg.add("conv_eur2009_to_eur2020", f"EA20 GDP deflator 2020/2009 ({ea20}/{ea09:.4f})", f_eur, "EUR2020/EUR2009", "A", "ECB Data Portal MNA EA20 GDP deflator",
            "research_inputs/prices/sources/ECB_EA20_GDP_DEFLATOR.csv", sha256(ea), decision_ref="89")
    reg.add("co2_extra_asean_storage_switch", "research.co2.extra_asean_storage values: on (main: one export link per node from '<node> co2 stored' to the country's uncapped store "
            "'co2 sequestered extra-ASEAN <ISO2>', unit cost on the store size as for the national sequestration store; both scenarios) | off (sensitivity, reproduces the "
            "infeasible disconnected case)", "on|off", "flag", "B", "S4C instruction S4C-4 items 1, 3", cfg, INSTRUCTION_SHA, decision_ref="89", status="REFERENCE_ONLY")
    reg.add("co2_extra_asean_accounting", "Exported CO2 counts as storage of the capturing country (decision 20): it leaves the national captured-CO2 buffer and never enters an atmosphere; "
            "not counted against the national injection cap (research_co2_storage_cap); limitation: one ASEAN-wide unit cost, no transport from inland nodes to a port (LA is landlocked; "
            "its exports would need a corridor through a neighbour), offshore unloading facilities not in the IEAGHG 2004 scope", "capture_country", "flag", "B",
            "S4C instruction S4C-4 items 1, 5", "scripts_project/s4c_layers.apply_extra_asean_storage", INSTRUCTION_SHA, decision_ref="89,20", status="REFERENCE_ONLY")
    reg.add("co2_extra_asean_cost_crosscheck", "Cross-check: GCCSI 2025 Table 3 lists IEAGHG 2004 as the only published shipping cost beyond 2,000 km (US$10-44/t, 200-12,000 km); later "
            "studies at <= 2,000 km report US$9-50/t (IEAGHG 2020: 41-44 US$/t at 1,000 km and 1.4-1.8 Mt/a), i.e. the 2004 basis (large ships, 6.2 Mt/a) is at the low end",
            "low_end", "flag", "B", "GCCSI (2025); IEAGHG (2020-10); IEAGHG (2025-08); ERIA (2022) Vol. II Table 2.8", "sources_s4c/co2", f"gccsi:{shas['gccsi2025']}|ieaghg2020:{shas['ieaghg2020']}",
            decision_ref="89", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4c_4.csv")
    print(pd.DataFrame(rows)[["item", "distance_km", "value", "unit", "eur2020_per_t"]].round(3).to_string())
    print(dict(f_usd=f_usd, f_eur=f_eur, ship_eur=ship_eur, storage_eur=stor_eur, total=total))


if __name__ == "__main__":
    main()
