"""M08b supplement 01: markdown tables for the report from BUILD_INPUT_CHANGES_M08B_S01.csv, M08B_S01_NETWORK_FILES.csv and the anchor table (read-only)."""
import json
import pandas as pd

EV = "/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m08b_20261021/evidence"
DEM = "/home/jin/wt_m08b_20261021/research_inputs/demand_v5"
C = ["BN", "KH", "ID", "LA", "MY", "MM", "PH", "SG", "TH", "TL", "VN"]
d = pd.read_csv(f"{EV}/BUILD_INPUT_CHANGES_M08B_S01.csv")
i = d[d.scenario == "integrated"].set_index("country").loc[C]
dc = d[d.scenario == "disconnected"].set_index("country").loc[C]


def f(v, nd=1):
    return f"{v:,.{nd}f}"


def table(cols, hdr):
    out = ["| 国 | " + " | ".join(hdr) + " |", "|---|" + "---|" * len(hdr)]
    for c in C + ["11 国"]:
        r = i.sum() if c == "11 国" else i.loc[c]
        cells = [f(r[k], nd) for k, nd in cols]
        out.append(f"| {'**11 国**' if c == '11 国' else c} | " + " | ".join(f"**{x}**" if c == "11 国" else x for x in cells) + " |")
    return "\n".join(out)


print("### table A (previous columns, before = S4M-3, m08b1, after = S01)")
cols = []; hdr = []
for k, lab, nd in [("final_demand_twh", "终端需求", 0), ("base_electricity_twh", "基础电力", 1), ("fixed_electricity_twh", "固定电力", 0), ("cement_mt", "水泥", 1),
                   ("steel_mt", "粗钢", 1), ("pv_cap_gw", "光伏上限", 0), ("storage_cap_mt", "封存上限", 1)]:
    sfx = ["old", "m08b1", "new"] if k in ("final_demand_twh", "fixed_electricity_twh") else ["old", "new"]
    for s in sfx:
        cols.append((f"{k}_{s}", nd)); hdr.append(f"{lab} {dict(old='前', m08b1='首轮', new='后')[s]}")
print(table(cols, hdr))
print()
print("### table B (new columns)")
cols = [(f"residential_fuel_twh_old", 1), (f"residential_fuel_twh_new", 1), (f"commercial_fuel_twh_old", 1), (f"commercial_fuel_twh_new", 1),
        (f"agriculture_fuel_twh_old", 1), (f"agriculture_fuel_twh_new", 1), ("industry_heat_medium_twh_m08b1", 1), ("industry_heat_medium_a_twh_new", 1),
        ("industry_heat_medium_b_twh_new", 1), ("industry_heat_high_twh_new", 1)]
hdr = ["居民燃料 前", "后", "商业燃料 前", "后", "农业燃料 前", "后", "中温 首轮", "中温 A", "中温 B", "高温"]
print(table(cols, hdr))
print()
print("disconnected demand columns equal integrated:", all(abs(i[k] - dc[k]).max() < 1e-6 for k in i.columns if k.startswith(("final_demand", "base_electricity", "fixed_electricity", "residential", "commercial", "agriculture", "industry_heat"))))
for k in ["final_demand_twh", "fixed_electricity_twh", "industry_electricity_twh", "land_transport_ev_twh", "fixed_gas_twh", "fixed_biomass_twh", "industry_heat_low_twh", "industry_heat_high_twh"]:
    print(k, {s: round(float(i[f"{k}_{s}"].sum()), 1) for s in ("old", "m08b1", "new")})
an = pd.read_csv(f"{DEM}/DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
tl = an.loc["TL"]
print("TL:", {k: round(float(tl[k]) / (1e6 if k.endswith("_mwh") else 1), 4) for k in ["population_2050_million", "ats_tfec_2050_mwh", "ats_elec_2050_mwh", "industry_anchor_mwh", "industry_multiplier",
                                                                                         "tfec_2019_Industry_mwh", "base_load_anchor_mwh", "transport_anchor_mwh", "residential_fuel_anchor_mwh", "agriculture_fuel_anchor_mwh"]})
print("TL network:", {k: round(float(i.at["TL", f"{k}_new"]), 3) for k in ["final_demand_twh", "fixed_electricity_twh", "industry_electricity_twh", "industry_heat_low_twh", "industry_heat_medium_a_twh",
                                                                             "industry_heat_medium_b_twh", "industry_heat_high_twh"]})
s = pd.read_csv(f"{DEM}/INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv").set_index("country")
print("TL industry table TWh:", {k: round(float(s.at["TL", k]) / 1e6, 4) for k in s.columns if k.startswith("pe_") and k.endswith("_mwh") and abs(float(s.at["TL", k])) > 0})
med = s.pe_heat_medium_a_mwh + s.pe_heat_medium_b_mwh
print("medium A sensitivity 11 countries TWh (f 0.1 / 0.2 / 0.3):", [round(float(med.sum()) * f_ / 1e6, 1) for f_ in (0.1, 0.2, 0.3)], "medium total", round(float(med.sum()) / 1e6, 1))
nf = pd.read_csv(f"{EV}/M08B_S01_NETWORK_FILES.csv")
print(nf.to_string(index=False))
print("total MB", round(nf.bytes.sum() / 1e6, 1))
st = json.load(open(f"{EV}/M08B_S01_STATIC_CHECKS.json"))
for sc in ("integrated", "disconnected"):
    m = st["results"][sc]["M08b"]
    print(sc, "band map:", {b: (v["link_carriers"], v["input_bus_carriers"]) for b, v in m["temperature_band_map"]["bands"].items()})
    print(sc, "overflow heat:", m["no_fixed_methane_overflow"]["useful_heat_overflow_twh"], "LNG:", m["lng_uncapped"]["terminals"], m["lng_uncapped"]["capital_cost"],
          "VN cap", m["vn_storage_cap"]["store_e_nom_max_mt"], "pv", round(m["pv_cap_scale"]["ratio_min"], 6), round(m["pv_cap_scale"]["ratio_max"], 6))
    print(sc, "B11 routes:", st["results"][sc]["B11_supply_routes"].get("passed"), "G2.1", st["results"][sc]["G2"]["G2_1"]["file_sha256"][:12])
