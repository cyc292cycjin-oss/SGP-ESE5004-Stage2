"""D1 section 1: fossil fuel import prices for 2050 from WEO 2025 Table 2.3 (USD MER 2024).

S4C-0 (decision 85, modifies decision 33 after the smoke results): main = STEPS 2050 (crude 76 USD/bbl,
natural gas Japan LNG 9.7 USD/MBtu GCV, steam coal Japan 84 USD/t at 6,000 kcal/kg); NZE 2050 (25 / 4.9 / 49)
is the low-price sensitivity; CPS 2050 (106 / 12.9 / 105) is registered as an optional value. The model
selects one scenario for all three fuels with research.fuels.price_scenario (s2_costs.fuel_price_ids).
The param_id suffixes _main / _high_price are the D1 names, kept for traceability; the status column
carries the current role. 2024 historical kept as reference.
D1 (superseded): main = NZE 2050, high-price sensitivity = STEPS 2050.
Conversion to EUR2020/MWh (NCV, consistent with the model fuel buses whose UNSD
reconstruction is NCV-based and with technology-data fuel rows in EUR/MWh_th LHV):
  USD2024 -> USD2020 with the US GDP implicit price deflator (FRED A191RD3A086NBEA),
  USD2020 -> EUR2020 with the 2020 ECB annual mean rate used by the author pipeline,
  energy units with the constants registered in d1_common.UNIT_CONSTANTS.
"""
from __future__ import annotations

from d1_common import (REG_DIR, SRC_DIR, UNIT_CONSTANTS, USD2024_TO_EUR2020, Registry, read_csv,
                       src_sha, write_csv, write_json)

SCRIPT = "scripts_project/d1_fuel_prices.py"
WEO_CSV = "WEO2025_FOSSIL_PRICES.csv"
WEO_PDF_SHA = "ebee58b6b93d6aed43db5247d54b03a7248510c2986bd24cfb4cca59d339b8f4"
TD_FUEL_2050 = {  # technology-data v0.13.2 outputs/costs_2050.csv fuel rows, EUR/MWh_th (independent comparison)
    "oil": (52.9111, "IEA WEM2017 97USD/boe; costs_2050.csv technology oil, parameter fuel"),
    "gas": (24.5680, "DIW 2013; costs_2050.csv technology gas, parameter fuel"),
    "coal": (9.5542, "DIW 2013; costs_2050.csv technology coal, parameter fuel"),
}


def mwh_per_bbl_ncv():
    btu = UNIT_CONSTANTS["conv_btu_per_bbl_crude_gcv"][0]
    mwh_per_mbtu = UNIT_CONSTANTS["conv_mwh_per_mbtu"][0]
    return btu / 1e6 * mwh_per_mbtu * UNIT_CONSTANTS["conv_oil_gcv_to_ncv"][0]


def mwh_per_t_coal():
    return UNIT_CONSTANTS["conv_gj_per_t_coal_6000kcal"][0] / 3.6


def gas_usd_per_mbtu_to_usd_per_mwh_ncv(p):
    return p / UNIT_CONSTANTS["conv_mwh_per_mbtu"][0] / UNIT_CONSTANTS["conv_gas_gcv_to_ncv"][0]


def pick(rows, fuel, region, scenario, year):
    for r in rows:
        if r["fuel"] == fuel and r["region"] == region and r["scenario"] == scenario and r["year"] == str(year):
            return float(r["value"]), r
    raise KeyError((fuel, region, scenario, year))


def main():
    rows = read_csv(SRC_DIR / WEO_CSV)
    csv_sha = src_sha(WEO_CSV)
    sha = f"WorldEnergyOutlook2025.pdf:{WEO_PDF_SHA}; extraction:{csv_sha}"
    reg = Registry(SCRIPT)
    table = []
    fx = USD2024_TO_EUR2020
    specs = {
        "oil": ("IEA crude oil", "IEA crude oil (weighted avg import price, IEA members)", "USD/barrel",
                lambda p: p / mwh_per_bbl_ncv(), "crude oil import price; bbl -> MWh NCV via EIA 5.689 MMBtu/bbl GCV x 0.95"),
        "gas": ("Natural gas", "Japan", "USD/MBtu",
                gas_usd_per_mbtu_to_usd_per_mwh_ncv, "Japan = pure LNG import price at customs border before regasification, GCV basis -> NCV (/0.90); proxy for ASEAN LNG imports (no Southeast Asia entry in Table 2.3)"),
        "coal": ("Steam coal", "Japan", "USD/tonne",
                 lambda p: p / mwh_per_t_coal(), "Japan = pure import price adjusted to 6,000 kcal/kg (treated as net as received); Coastal China 2050 identical (49)"),
    }
    roles = {"STEPS": "S4C-0 main (decision 85, research.fuels.price_scenario: steps; param_id suffix is the D1 name)",
             "NZE": "S4C-0 low-price sensitivity (decision 85, research.fuels.price_scenario: nze; D1 main until S4B, param_id suffix is the D1 name)",
             "CPS": "S4C-0 optional value, not a main run (decision 85, research.fuels.price_scenario: cps)", "historical": "reference only"}
    for carrier, (fuel, region, unit, to_usd_mwh, note) in specs.items():
        for scenario, year, status, tag in [("NZE", 2050, "SENSITIVITY", "main"), ("STEPS", 2050, "REGISTERED", "high_price"),
                                            ("CPS", 2050, "SENSITIVITY", "optional"), ("historical", 2024, "REFERENCE_ONLY", "ref_2024")]:
            p, r = pick(rows, fuel, region, scenario, year)
            usd_mwh = to_usd_mwh(p)
            eur_mwh = usd_mwh * fx
            table.append(dict(carrier=carrier, scenario=scenario, year=year, weo_value=p, weo_unit=unit,
                              usd2024_per_mwh_ncv=usd_mwh, eur2020_per_mwh_ncv=eur_mwh, region=region,
                              table="Table 2.3", pdf_page=r["pdf_page"], note=note))
            reg.add(f"fuel_price_{carrier}_{scenario}_{year}_{tag}",
                    f"{fuel} ({region}) {scenario} {year}: {p:g} {unit} (USD MER 2024) -> EUR2020/MWh NCV; {note}; role: {roles[scenario]}",
                    eur_mwh, "EUR2020/MWh_NCV", "B", "IEA WEO 2025 Table 2.3",
                    f"PDF p.{r['pdf_page']} (printed {r['printed_page']}); extraction {WEO_CSV}", sha,
                    sensitivity_low=None, sensitivity_high=None, decision_ref=("46,D1-1,33,85" if scenario != "historical" else "46,D1-1"), status=status)
            reg.add(f"fuel_price_{carrier}_{scenario}_{year}_{tag}_source_value",
                    f"{fuel} ({region}) {scenario} {year} as printed", p, unit + " (USD MER 2024)", "A",
                    "IEA WEO 2025 Table 2.3", f"PDF p.{r['pdf_page']}", sha, status="REFERENCE_ONLY")
    # comparison with technology-data fuel rows (independent source)
    comp = []
    for carrier, (td, loc) in TD_FUEL_2050.items():
        main = next(t for t in table if t["carrier"] == carrier and t["scenario"] == "NZE")
        high = next(t for t in table if t["carrier"] == carrier and t["scenario"] == "STEPS")
        comp.append(dict(carrier=carrier, weo_nze_2050_eur2020_mwh=main["eur2020_per_mwh_ncv"],
                         weo_steps_2050_eur2020_mwh=high["eur2020_per_mwh_ncv"], technology_data_v0_13_2_2050=td,
                         ratio_nze_to_td=main["eur2020_per_mwh_ncv"] / td, technology_data_locator=loc))
    reg.add("fuel_price_conversion_usd2024_to_eur2020", "Combined factor USD2024 -> EUR2020 = US GDP deflator "
            "(105.377/125.587) x ECB 2020 mean USD->EUR (0.877229)", fx, "EUR2020/USD2024", "B",
            "FRED A191RD3A086NBEA; ECB via currency_converter 0.18.9", "see conv_* and fx_* rows", csv_sha,
            decision_ref="D1-0 units")
    reg.add("fuel_price_mwh_per_bbl_crude_ncv", "Energy per barrel of crude on an NCV basis used for the oil price "
            "conversion (5.689 MMBtu GCV x 0.95); IEA convention 1 bbl ~ 0.136 toe = 1.582 MWh agrees within 0.2%",
            mwh_per_bbl_ncv(), "MWh/bbl", "B", "US EIA conversion calculators; IPCC Box 1.1", "see conv_* rows", csv_sha,
            sensitivity_low=mwh_per_bbl_ncv() * 0.97, sensitivity_high=mwh_per_bbl_ncv() * 1.03)
    reg.add("fuel_price_basis", "Fuel prices are registered per MWh of net calorific value (NCV/LHV), matching the "
            "UNSD GCV->NCV reconstruction of the research demand layer and technology-data fuel rows (EUR/MWh_th LHV)",
            "NCV", "basis", "A", "scripts_project/reconstruct_base_accounts.py; technology-data unit convention",
            "natural gas TJ GCV x 0.90", csv_sha)
    reg.add("fuel_price_lng_regasification_adder", "WEO Japan LNG price is before regasification; no sourced ASEAN "
            "regasification tariff available -> not added", None, "EUR2020/MWh", "C", "IEA WEO 2025 Table 2.3 note",
            "PDF p.109 note on LNG customs border price", sha, status="DATA_PENDING")
    out_dir = REG_DIR / "fragments"
    reg.write(out_dir / "fuel_prices.csv")
    write_csv(table, REG_DIR / "FUEL_PRICES_2050_EUR2020.csv",
              ["carrier", "scenario", "year", "region", "weo_value", "weo_unit", "usd2024_per_mwh_ncv",
               "eur2020_per_mwh_ncv", "table", "pdf_page", "note"])
    write_csv(comp, REG_DIR / "FUEL_PRICES_CROSSCHECK_TECHNOLOGY_DATA.csv", list(comp[0].keys()))
    write_json(dict(script=SCRIPT, usd2024_to_eur2020=fx, mwh_per_bbl_ncv=mwh_per_bbl_ncv(),
                    mwh_per_t_coal_6000kcal=mwh_per_t_coal(), table=table, crosscheck=comp),
               out_dir / "fuel_prices.json")
    for t in table:
        print(f"{t['carrier']:5s} {t['scenario']:10s} {t['year']} {t['weo_value']:>7g} {t['weo_unit']:10s} -> "
              f"{t['usd2024_per_mwh_ncv']:7.2f} USD2024/MWh -> {t['eur2020_per_mwh_ncv']:7.2f} EUR2020/MWh")
    for c in comp:
        print(f"  crosscheck {c['carrier']}: NZE {c['weo_nze_2050_eur2020_mwh']:.2f} vs technology-data {c['technology_data_v0_13_2_2050']:.2f} (ratio {c['ratio_nze_to_td']:.2f})")


if __name__ == "__main__":
    main()
