"""V4 D2b section 4: literature data upgrades - decision per item (replace only with >= 2 independent sources whose basis can be converted; otherwise keep
the current value and register a range). Source values are those read in evidence/DATA_UPG_A.json (D..) and DATA_UPG_B.json (E..) of this delivery;
conversions are restated here (deterministic). Writes DATA_UPGRADES.csv and evidence/DATA_UPGRADES_CALC.json. Nothing is solved.

    python scripts/d2b_data_upgrades.py

Currency conversion (DATA_UPG_A note): local currency of price year Y -> EUR at the Eurostat annual average of Y -> EUR2020 by the euro-area HICP ratio
2020 / Y (rates as recorded in DATA_UPG_A.json, not re-fetched); 1 MMBtu = 0.29307 MWh.
"""
import json
import statistics as st
from pathlib import Path

W = Path(__file__).resolve().parents[1]
MWH_PER_MMBTU = 0.29307
FX = {"USD_2017": 1.1297, "USD_2019": 1.1195, "USD_2020": 1.1422, "THB_2020": 35.7081, "MYR_2019": 4.6374, "MYR_2025": 4.8339, "SGD_2025": 1.4756, "GBP_2017": 0.87667}
HICP = {2009: 91.65, 2017: 101.78, 2018: 103.56, 2019: 104.8, 2020: 105.06, 2024: 126.07, 2025: 128.75}


def eur2020(x, cur, year):
    return x / FX[f"{cur}_{year}"] * HICP[2020] / HICP[year]


def lng():
    t = {}
    t["TH_LMPT1_2020_Ld_plus_Lc"] = dict(eur2020_mwh=eur2020((18.35 + 0.5382) / MWH_PER_MMBTU, "THB", 2020), ev="D01;D02", note="ERC-approved Ld 18.35 + Lc 0.5382 THB/MMBtu (2020)")
    t["MY_RGTSU_2025"] = dict(eur2020_mwh=eur2020(3.456 * 3.6, "MYR", 2025), ev="D07", note="ST-approved 3.456 RM/GJ/day of capacity, read at full utilisation")
    t["MY_RGTP_2025"] = dict(eur2020_mwh=eur2020(3.149 * 3.6, "MYR", 2025), ev="D08", note="ST-approved 3.149 RM/GJ/day, full utilisation")
    t["MY_RGTSU_2019"] = dict(eur2020_mwh=eur2020(3.518 / MWH_PER_MMBTU, "MYR", 2019), ev="D05", note="2019 tariff (superseded by 2025; not used in the median)")
    t["MY_RGTP_2019"] = dict(eur2020_mwh=eur2020(0.637 / MWH_PER_MMBTU, "USD", 2019), ev="D06", note="2019 tariff (superseded by 2025; not used in the median)")
    sg = 0.95 + 0.12 + 0.04   # reservation (per MMBtu of MaxGRR per day = per MMBtu at full use) + shoulder utilisation + GSC FY26 (D09, D10); 2025 FX / HICP for FY26
    t["SG_SLNG_FY26"] = dict(eur2020_mwh=eur2020(sg / MWH_PER_MMBTU, "SGD", 2025), ev="D09;D10", note="SLNG/EMA FY26: 0.95 reservation + 0.12 shoulder utilisation + 0.04 GSC SGD/MMBtu (range 0.02-0.22 utilisation)",
                          low=eur2020((0.95 + 0.02) / MWH_PER_MMBTU, "SGD", 2025), high=eur2020((0.95 + 0.22 + 0.04) / MWH_PER_MMBTU, "SGD", 2025))
    t["ID_Arun_2017"] = dict(eur2020_mwh=eur2020(1.53 / MWH_PER_MMBTU, "USD", 2017), ev="D11", note="Arun regasification fee (Pertamina), news report; no BPH Migas regulated toll found (D13)")
    t["ID_FSRU_2017_snippet"] = dict(eur2020_mwh=eur2020(3.0 / MWH_PER_MMBTU, "USD", 2017), ev="D12", note="SNIPPET only (403): FSRU West Java / Lampung / Bali ~3.0 USD/MMBtu - not used")
    groups = {"TH": t["TH_LMPT1_2020_Ld_plus_Lc"]["eur2020_mwh"], "MY": st.median([t["MY_RGTSU_2025"]["eur2020_mwh"], t["MY_RGTP_2025"]["eur2020_mwh"]]),
              "SG": t["SG_SLNG_FY26"]["eur2020_mwh"], "ID": t["ID_Arun_2017"]["eur2020_mwh"]}
    val = st.median(groups.values())
    return dict(terminals=t, country_groups=groups, value=val, low=min(groups.values()), high=max(groups.values()), old=1.26, change_pct=100 * (val / 1.26 - 1),
                verdict="REPLACE: four national regulators / operators (TH ERC, MY Suruhanjaya Tenaga, SG EMA-SLNG, ID Arun) publish per-energy terminal tariffs; independent, convertible (full-utilisation tariff per MWh, the basis of the registered adder); value = median of the country groups",
                caveat="the published tariffs are full-cost (capacity charge incl. capital recovery); the model also charges the expansion capex 8,020 EUR2020/MW/a on NEW terminal capacity (~0.92 EUR/MWh at full use) - the capital part is counted twice on expanded capacity (as for the old 1.26); open question")


def ship():
    s, f_model = 0.0029515, 11.4166656
    zep1 = dict(fixed=14.29, slope=0.00553, ev="D25", note="ZEP 2011 Table 1 (2.5 Mtpa point-to-point, ship + liquefaction 5.3), OLS through 180-1,500 km, Q2 2009 -> EUR2020 (derived, re-computed: slope 0.00482 EUR2009/(t km), intercept 7.17 + 5.3)")
    zep2 = dict(fixed=11.87, slope=0.00437, ev="D26", note="ZEP 2011 Table 2 (20 Mtpa network, ship incl. stand-alone liquefaction), OLS (derived)")
    ieaghg = dict(total_1000km=17.246, ev="D16", note="IEAGHG 2020-10 scenario 1 pre-pressurised, 1,000 km, 7 barg (EUR2018)")
    beis = dict(total_600km=11.798, slope_minus25pct=0.00393, ev="D21;D24", note="Element Energy for BEIS 2018 central case 600 km pre-pressurised (GBP2017); same consultancy as IEAGHG 2020 (not independent)")
    fixed_from_totals = {"IEAGHG2020_at_model_slope": ieaghg["total_1000km"] - s * 1000, "BEIS2018_at_model_slope": beis["total_600km"] - s * 600}
    fixed_all = [zep1["fixed"], zep2["fixed"]] + list(fixed_from_totals.values())
    slopes = [s, zep1["slope"], zep2["slope"], beis["slope_minus25pct"]]
    return dict(model=dict(fixed=f_model, slope=s), zep_table1=zep1, zep_table2=zep2, ieaghg2020=ieaghg, beis2018=beis, fixed_from_totals=fixed_from_totals,
                fixed_range=[min(fixed_all), max(fixed_all)], slope_range=[min(slopes), max(slopes)],
                chain_1000km=dict(model=f_model + s * 1000, ieaghg2020=ieaghg["total_1000km"], zep_t1=zep1["fixed"] + zep1["slope"] * 1000, zep_t2=zep2["fixed"] + zep2["slope"] * 1000),
                verdict=("KEEP + RANGE: the literature gives chain totals at single distances with different pressure levels (7 barg low pressure vs the 100 bar chain "
                         "of IEAGHG 2004), inlet conditions (pre-pressurised) and ship sizes; the split into a distance-independent part and a per-km slope is a "
                         "derivation (OLS / model slope), not a source value. IEAGHG 2020 and BEIS 2018 share the lead consultancy. Model chain at 1,000 km "
                         "(14.37 EUR2020/t) lies inside the literature spread (BEIS lower, IEAGHG / ZEP higher). Fixed part range and slope range registered"))


def storage():
    rng = {"ID": (34.275, 51.275, 77.275, "D39"), "MY": (81.773, 128.773, 198.773, "D40"), "BN": (13.5793, 18.5793, 25.5793, "D41"), "TH": (12.024, 16.024, 23.024, "D42"),
           "VN": (3.3034, 5.3034, 9.3034, "D43")}
    out = {c: dict(low_gt=a, p50_gt=b, high_gt=h, cap_low_t=a * 1e9 / 50, cap_p50_t=b * 1e9 / 50, cap_high_t=h * 1e9 / 50, ev=e) for c, (a, b, h, e) in rng.items()}
    out["PH"] = dict(low_gt=None, p50_gt=0.0672, high_gt=None, ev="D44", note="hydrocarbon fields only (Malampaya); no ERIA range")
    out["KH"] = dict(note="not assessed by ERIA (D46); model 0.09 Gt / cap 1.8 Mt/a from OGCI 2025 / IJGGC 2014 (not read: D48)")
    return dict(countries=out, verdict="RANGE ONLY (decision 126: main stays P50): ERIA / GCCSI 2024 Ch.1 saline P90 / P50 / P10 + hydrocarbon P50 (deterministic); one source (OGCI not read) - ranges registered for W19, main values unchanged; annual caps = potential / 50 years (the build rule)")


def ev():
    # per-class ratio fuel / electricity per km (TTW, derived from the class values in DATA_UPG_B; gasoline 8.9 kWh/L E06, diesel 10.0 kWh/L assumed)
    two = dict(low=17.27 / 2.9, high=22.25 / 2.5, mid=st.median([17.27 / 2.9, 22.25 / 2.5, 15.66 / 2.047, 28.44 / 4.0]),
               ev="E03-E08, E10, E11, E20", pairs="ITDP ID test 17.27 / 2.9; ADB monitored 22.25 / 2.5; VN 15.66 (ITDP) / 2.047 (Le 2023 on-road); ADBI 2040 28.44 / 4.0")
    car = dict(low=44.5 / 12.5, high=66.75 / 14.8, mid=st.median([44.5 / 12.5, 64.8 / 18.4, 66.75 / 14.8]), ev="E10, E11, E14, E16, E18, E19",
               pairs="ERIA 20 km/L vs 8 km/kWh; ADBI ID 13.74 km/L vs 18.4 kWh/100 km; IEA/GFEI TH 7.5 Lge/100 km (WLTP) vs TH real-world 14.8 kWh/100 km")
    heavy = dict(low=182.5 / 123.5, high=403.2 / 123.5, mid=266.7 / 123.5, ev="E10, E11 (ADBI only; trucks not comparable)", pairs="ADBI buses 5.48 / 3.75 / 2.48 km/L diesel vs 0.81 km/kWh")
    shares2 = dict(low=0.08, mid=0.165, high=0.27, ev="E21 (IEA 2018: ID 27 / VN 21 / TH 10 / PH 8 % of road fuel)")
    heavy_sh = dict(low=0.20, mid=0.22, high=0.51, ev="E13 (ADBI 2015 fuel by class: MY 21.5 / TH 19.7 / VN 23.0 / ID 50.9 % trucks + buses; several cells implausible)")

    def ratio(s2, sh, r2, rc, rh):
        sc = 1.0 - s2 - sh
        return 1.0 / (s2 / r2 + sc / rc + sh / rh)
    mid = ratio(shares2["mid"], heavy_sh["mid"], two["mid"], car["mid"], heavy["mid"])
    lo = ratio(shares2["low"], heavy_sh["high"], two["low"], car["low"], heavy["low"])
    hi = ratio(shares2["high"], heavy_sh["low"], two["high"], car["high"], heavy["high"])
    model = 53.19 / 16.0712
    return dict(class_ratio=dict(two_wheeler=two, car=car, bus=heavy), shares=dict(two_wheeler=shares2, heavy=heavy_sh), fleet_ratio_mid=mid, fleet_ratio_low=lo, fleet_ratio_high=hi,
                model_ratio=model, mid_vs_model_pct=100 * (mid / model - 1), ev_eff_range_at_ice_16_0712=[lo * 16.0712, hi * 16.0712],
                verdict=("KEEP + RANGE: class values have >= 2 sources (two-wheelers, cars), but the fleet weights contradict each other (TH two-wheeler share of road "
                         "fuel 10 % IEA vs 27 % ADBI) and trucks have no comparable electric / combustion pair; the energy-weighted mid estimate differs from the "
                         "model ratio 3.31 by less than 10 % -> current values kept (instruction 4.4), fleet ratio range registered (INFERENCE)"))


def rooftop():
    return dict(model_mw=83146.768938, myrer_mw=42000.0, ratio=42000.0 / 83146.768938, peninsular_mw=[34194.0, 37429.0], ev="E50-E53",
                verdict="RANGE ONLY: one source lineage (SEDA MyRER 42 GW national; 34.2 / 37.4 GW peninsular from SEDA too; BCG 4.4 GW covers non-residential estates only) - low end of the registered range = 42,000 MW")


def wacc():
    return dict(iea="nominal, after tax, local currency (E60-E62)", country_table="COUNTRY_WACC_REAL_M08A.csv: IEA nominal post-tax midpoints converted to real by (1 + n) / (1 + CPI 2028-2030) - 1 -> real, after tax",
                uniform="7 %: technology-data / PyPSA-Eur fill value; origin Hirth 2013 (basis not stated, constant-price model) and Noothout et al. 2016 (nominal post-tax) (E64-E67); technology-data costs are in a fixed currency year (real) (E68)",
                verdict="NOTE ONLY (no change to the main run): the country table is real after-tax; the uniform 7 % has no stated basis - its documented origin is nominal post-tax, applied to real (constant EUR2020) costs. The two are therefore not on the same basis; the country-specific WACC stays a W19 sensitivity")


def seq_year():
    return dict(value=2020, basis="INFERENCE: PyPSA-Eur v2025.07.0 docs give 'currency/tCO2' without a year (D34, D35); 30 replaced 10 in release commit e43746df / PR #1753 (D32) together with technology-data v0.10.1 -> v0.13.2 (eur_year 2020, D37); the parameter is not read from technology-data",
                verdict="DETERMINED BY INFERENCE: EUR2020 (as already used); the registered factor range 0.86-1.0 is kept; value 30 EUR/t unchanged (no network change)")


def main():
    L, S, ST_, E, R, Wc, Y = lng(), ship(), storage(), ev(), rooftop(), wacc(), seq_year()
    calc = dict(lng=L, co2_ship=S, co2_storage_potential=ST_, ev_ice=E, my_rooftop=R, wacc=Wc, co2_sequestration_price_year=Y)
    alpha = W / "evidence/VN_OFFWIND_ALPHA.json"
    if alpha.exists():
        calc["vn_offwind_alpha"] = json.loads(alpha.read_text())
    (W / "evidence").mkdir(exist_ok=True)
    (W / "evidence/DATA_UPGRADES_CALC.json").write_text(json.dumps(calc, indent=1, default=float) + "\n", newline="\n")   # LF also on Windows (the repository commits LF)
    print(json.dumps(dict(lng=dict(groups=L["country_groups"], value=L["value"], low=L["low"], high=L["high"]), ship=dict(fixed=S["fixed_range"], slope=S["slope_range"], chain=S["chain_1000km"]),
                          ev=dict(mid=E["fleet_ratio_mid"], low=E["fleet_ratio_low"], high=E["fleet_ratio_high"], pct=E["mid_vs_model_pct"], eff=E["ev_eff_range_at_ice_16_0712"]),
                          rooftop=R["ratio"]), indent=1, default=float))


if __name__ == "__main__":
    main()
