"""S4R R2: renewable potential comparison (read-only), revised per S4R supplement 01 (decision 129) section 3.
Model candidate caps (S4P extraction of the integrated build network) vs ESMAP/Solargis 2020 Level-1 area x uniform power density,
Zhong et al. PNAS Nexus Table S3 (high / moderate), iScience 2025 Table S6, registry official figures, WBG-ESMAP offshore technical potential.
Adds the decomposition of the model / ESMAP ratio into the density parameter (4.6 vs 5.1 MW/km2) and the basis differences (protected
areas: excluded by the model and PyPSA-Eur, not by ESMAP Level 1; forest: all forest classes excluded by the model and PyPSA-Eur, only
compact forest >= 50 % cover by ESMAP Level 1; other criteria). Output POTENTIAL_COMPARISON.csv / .md."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from s4r_paths import COUNTRIES, EV, ISO3, OUT, REPO, S4P, dump_json, load_json, md_table  # noqa: E402

DENS_MODEL = 4.6        # MW/km2, PyPSA-Earth solar (pypsa-asean config.default.yaml renewable.solar.capacity_per_sqkm)
DENS_EUR = 5.1          # MW/km2, PyPSA-Eur v2025.07.0 config.default.yaml line 270 (main run per supplement 01: density only)
DENS_ONWIND = 3.0       # both
# Zhong et al. 2026 PNAS Nexus, SI Table S3 (GW): solar high/moderate, onshore high/moderate, offshore high/moderate
ZHONG = {"BN": (16.0, 2.5, 0, 0, 0, 0), "KH": (3198.0, 8.1, 69.0, 65.0, 88.8, 0), "ID": (1052.0, 208.0, 61.0, 61.0, 589, 0), "LA": (1278.0, 8.8, 13.0, 3.5, 0, 0),
         "MY": (1965.0, 59, 2.0, 2.0, 53.3, 0), "MM": (7717.0, 30.0, 482.0, 6.97, 0, 0), "PH": (1910.0, 45, 217.0, 5.54, 69.4, 0), "SG": (8.6, 8.6, 0, 0, 0, 0),
         "TH": (10538.0, 22.8, 239, 17.00, 29.6, 0), "VN": (2847.0, 94.2, 311, 27.75, 322.1, 0)}
# iScience 2025 SI Table S6 (GW): solar high/moderate, wind high/moderate
ISC = {"BN": (16.0, 2.5, 0, 0), "KH": (3198.0, 8.1, 69.0, 65.0), "ID": (1052.0, 208.0, 61.0, 61.0), "LA": (1278.0, 8.8, 13.0, 3.5), "MY": (1965.0, 6.5, 2.0, 2.0),
       "MM": (7717.0, 30.0, 482.0, 6.97), "PH": (1910.0, 45, 217.0, 5.54), "SG": (8.6, 8.6, 0, 0), "TH": (10538.0, 22.8, 239, 17.00), "VN": (2847.0, 71.7, 311, 27.75)}
# WBG-ESMAP Global Offshore Wind Technical Potential (country-level xlsx, EAP tab): fixed, floating GW (S4P EXT_TECH_POLICY_BENCHMARKS)
ESMAP_OFF = {"VN": (261.05, 338.32), "PH": (18.75, 161.90), "ID": (197.71, 79.39), "KH": (0.13, 0.0)}
# registry official reference values (CANDIDATE_POTENTIAL_VS_MODEL_BY_COUNTRY.csv / registry potential_*): solar, onwind, offwind GW
OFFICIAL = {"VN": dict(solar=963, onwind=221, offwind=600, src="Decision 500/QD-TTg (PDP VIII) technical potential"), "ID": dict(solar=3294, onwind=155, src="ESDM 2023"),
            "MY": dict(solar=269, src="SEDA MyRER 2021"), "PH": dict(solar=58.11, onwind=93.99, offwind=178, src="DOE CREZ 2024; WB roadmap 2022")}
# World Bank WDI (API, read 2026-10-20): terrestrial protected areas % of land (ER.LND.PTLD.ZS, 2025) and forest area % of land (AG.LND.FRST.ZS, 2024)
WB_PROTECTED = {"BN": 39.9, "ID": 12.0, "KH": 39.8, "LA": 18.8, "MM": 6.7, "MY": 13.3, "PH": 16.0, "SG": 4.6, "TH": 18.4, "TL": 16.1, "VN": 7.6}
WB_FOREST = {"BN": 72.1, "ID": 50.7, "KH": 37.6, "LA": 56.6, "MM": 42.0, "MY": 57.7, "PH": 24.8, "SG": 21.8, "TH": 38.7, "TL": 71.0, "VN": 47.1}


def main():
    S = load_json(S4P / "ASPECTS_SUMMARY.json")
    caps = S["aspect3_candidate_caps_gw"]
    sol = pd.read_csv(EV / "SOLARGIS_ESMAP_2020_ASEAN11.csv")
    sol["iso2"] = sol.ISO_A3.map({v: k for k, v in ISO3.items()})
    sol = sol.set_index("iso2")
    area_col = [c for c in sol.columns if c.startswith("Total area")][0]; eval_col = "Evaluated area"; l1_col = [c for c in sol.columns if c.startswith("Level 1 area")][0]
    pvout_col = [c for c in sol.columns if "PVOUT Level 1" in c][0]; ghi_col = [c for c in sol.columns if c.startswith("Average theoretical")][0]
    rows = []
    for c in COUNTRIES:
        g = lambda car: caps.get(car, {}).get(c, np.nan)
        m_solar = g("solar"); m_roof = g("solar rooftop"); m_on = g("onwind"); m_offac = g("offwind-ac"); m_offdc = g("offwind-dc")
        m_off = (0 if pd.isna(m_offac) else m_offac) + (0 if pd.isna(m_offdc) else m_offdc)
        area = float(sol.at[c, eval_col]); l1 = float(sol.at[c, l1_col]); l1_km2 = area * l1
        esmap_l1_eur = l1_km2 * DENS_EUR / 1e3; esmap_l1_model = l1_km2 * DENS_MODEL / 1e3
        model_area_km2 = m_solar * 1e3 / DENS_MODEL if pd.notna(m_solar) else np.nan
        z = ZHONG.get(c, (np.nan,) * 6); i = ISC.get(c, (np.nan,) * 4); eo = ESMAP_OFF.get(c); of = OFFICIAL.get(c, {})
        ratio = m_solar / esmap_l1_eur if pd.notna(m_solar) else np.nan
        # ---- decomposition (supplement 01 section 3): ratio = density factor x land factor; land factor = protected-area factor (upper bound) x residual (forest + other criteria)
        dens_f = DENS_MODEL / DENS_EUR
        land_f = model_area_km2 / l1_km2 if pd.notna(model_area_km2) else np.nan
        prot = WB_PROTECTED[c] / 100.0
        # fraction of the Level-1 area left if ALL protected land lay inside it (upper bound on the protected-area effect); it cannot explain more than the whole land factor
        prot_f = max(1.0 - min(prot / l1, 1.0), land_f if pd.notna(land_f) else 1e-6, 1e-6)
        resid_f = land_f / prot_f if pd.notna(land_f) else np.nan
        lr = np.log(ratio) if (pd.notna(ratio) and ratio > 0) else np.nan
        sh_dens = np.log(dens_f) / lr if pd.notna(lr) and lr != 0 else np.nan
        sh_prot = np.log(prot_f) / lr if pd.notna(lr) and lr != 0 else np.nan
        sh_res = np.log(resid_f) / lr if (pd.notna(lr) and lr != 0 and pd.notna(resid_f) and resid_f > 0) else np.nan
        rows.append(dict(country=c,
                         model_solar_gw=m_solar, model_rooftop_gw=m_roof, model_onwind_gw=m_on, model_offwind_ac_gw=m_offac, model_offwind_dc_gw=m_offdc, model_offwind_total_gw=m_off,
                         country_area_km2=area, esmap_level1_share=l1, esmap_level1_km2=l1_km2, esmap_pvout_l1_kwh_kwp_day=float(sol.at[c, pvout_col]), esmap_ghi=float(sol.at[c, ghi_col]),
                         esmap_l1_x5_1_gw=esmap_l1_eur, esmap_l1_x4_6_gw=esmap_l1_model, model_implied_solar_area_km2=model_area_km2, model_area_share_of_country=model_area_km2 / area if pd.notna(model_area_km2) else np.nan,
                         ratio_model_solar_over_esmap_l1_x5_1=ratio, ratio_model_area_over_esmap_l1=land_f,
                         wb_protected_share_of_land=prot, wb_forest_share_of_land=WB_FOREST[c] / 100.0,
                         decomp_density_factor=dens_f, decomp_protected_factor_upper_bound=prot_f, decomp_residual_forest_other_factor=resid_f,
                         decomp_log_share_density=sh_dens, decomp_log_share_protected_max=sh_prot, decomp_log_share_forest_other_min=sh_res,
                         main_run_cap_density_5_1_gw=m_solar * DENS_EUR / DENS_MODEL if pd.notna(m_solar) else np.nan, sensitivity_upper_esmap_l1_x5_1_gw=esmap_l1_eur,
                         zhong_solar_high_gw=z[0], zhong_solar_moderate_gw=z[1], zhong_onwind_high_gw=z[2], zhong_onwind_moderate_gw=z[3], zhong_offwind_high_gw=z[4],
                         iscience_solar_high_gw=i[0], iscience_solar_moderate_gw=i[1], iscience_wind_high_gw=i[2], iscience_wind_moderate_gw=i[3],
                         esmap_offwind_fixed_gw=eo[0] if eo else np.nan, esmap_offwind_floating_gw=eo[1] if eo else np.nan, esmap_offwind_total_gw=(eo[0] + eo[1]) if eo else np.nan,
                         official_solar_gw=of.get("solar", np.nan), official_onwind_gw=of.get("onwind", np.nan), official_offwind_gw=of.get("offwind", np.nan), official_source=of.get("src", ""),
                         ratio_model_solar_over_zhong_moderate=m_solar / z[1] if (pd.notna(m_solar) and z[1]) else np.nan, ratio_model_solar_over_zhong_high=m_solar / z[0] if (pd.notna(m_solar) and z[0]) else np.nan,
                         ratio_model_offwind_over_esmap=m_off / (eo[0] + eo[1]) if (eo and (eo[0] + eo[1]) > 0) else np.nan, ratio_model_onwind_over_zhong_high=m_on / z[2] if (pd.notna(m_on) and z[2]) else np.nan,
                         adjusted_solar_density_only_gw=m_solar * DENS_EUR / DENS_MODEL if pd.notna(m_solar) else np.nan, adjusted_solar_esmap_l1_x5_1_gw=esmap_l1_eur))
    df = pd.DataFrame(rows).set_index("country")
    df.to_csv(OUT / "POTENTIAL_COMPARISON.csv", float_format="%.4f")
    sysm = df.ratio_model_solar_over_esmap_l1_x5_1
    big = df.drop(["SG", "BN", "TL"])   # decomposition shares quoted for the eight countries with > 10 GW caps
    md = ["# R2 可再生潜力对照（已按补充 01 修订；GW；模型 = 一体化构建网络候选 `p_nom_max`；ESMAP = Solargis 2020 Level 1 面积 × 统一功率密度）", "",
          f"- 模型光伏上限 / ESMAP L1 × 5.1 MW/km² 的比值：中位数 {sysm.median():.2f}，范围 {sysm.min():.2f}–{sysm.max():.2f}；模型隐含光伏用地占国土 {df.model_area_share_of_country.min()*100:.0f}–{df.model_area_share_of_country.max()*100:.0f} %，ESMAP L1 占 {df.esmap_level1_share.min()*100:.0f}–{df.esmap_level1_share.max()*100:.0f} %。",
          f"- **分解（补充 01 §3）：** 比值 = 密度因子 × 用地因子。密度因子 = 4.6 / 5.1 = {DENS_MODEL/DENS_EUR:.3f}（参数差，PyPSA-Earth vs PyPSA-Eur），占对数差的 {big.decomp_log_share_density.min()*100:.0f}–{big.decomp_log_share_density.max()*100:.0f} %（八个 > 10 GW 国家）。用地因子 = 模型可用面积 / ESMAP L1 面积 = {big.ratio_model_area_over_esmap_l1.min():.2f}–{big.ratio_model_area_over_esmap_l1.max():.2f}，全部为口径差：(i) 保护区——模型（natura / WDPA）与 PyPSA-Eur 排除，ESMAP L1 不排除（只在 L2 排除）；以世行陆地保护区占比（{int(min(WB_PROTECTED.values()))}–{int(max(WB_PROTECTED.values()))} %）全部落在 L1 面积内为上界，最多解释对数差的 {big.decomp_log_share_protected_max.min()*100:.0f}–{big.decomp_log_share_protected_max.max()*100:.0f} %；(ii) 林地——模型与 PyPSA-Eur 排除全部林地类（Copernicus 111–126 / CORINE 23–25），ESMAP L1 只排除郁闭度 ≥ 50 % 的密林（ESMAP 2020 Ch.2 p.13），加上其他判据差（ESMAP 排除城市化 > 50 % 像元与距聚落 > 25 km 的偏远区、复杂地形；模型计入城市类 50、排除坡度与 natura），至少占 {max(big.drop('KH').decomp_log_share_forest_other_min.min(), 0)*100:.0f}–{big.decomp_log_share_forest_other_min.max()*100:.0f} %（KH 保护区占国土 40 %，其用地差额可完全由保护区解释）。世行森林占比 {int(min(WB_FOREST.values()))}–{int(max(WB_FOREST.values()))} % 给出林地口径的量级（含密林与开阔林，栅格未重算时无法再分）。",
          "- **结论改写：** 模型相对 ESMAP L1 偏低不是输入错误，而是：约一成来自密度参数（可无争议地对齐 PyPSA-Eur 5.1），其余来自与 PyPSA-Eur 同型的土地口径（保护区 + 全部林地排除）。主算只改密度（上限 × 1.109，按比例缩放 `p_nom_max`，无需栅格重算）；开阔林 121–126 计入作上界敏感性（偏离 PyPSA-Eur、毁林热点审稿风险），其触发规则见 `IMPLEMENTATION_PLAN.md` §2.1。", ""]
    show = df[["model_solar_gw", "esmap_level1_share", "esmap_l1_x5_1_gw", "ratio_model_solar_over_esmap_l1_x5_1", "model_area_share_of_country", "zhong_solar_high_gw", "zhong_solar_moderate_gw", "official_solar_gw", "main_run_cap_density_5_1_gw", "sensitivity_upper_esmap_l1_x5_1_gw"]].copy()
    show.columns = ["模型光伏", "ESMAP L1 份额", "ESMAP L1×5.1", "模型/ESMAP", "模型用地占国土", "Zhong 高", "Zhong 中", "官方", "主算（密度 5.1）", "敏感性上界（L1×5.1）"]
    md.append("## 光伏"); md.append(md_table(show.reset_index())); md.append("")
    show = df[["ratio_model_solar_over_esmap_l1_x5_1", "decomp_density_factor", "ratio_model_area_over_esmap_l1", "wb_protected_share_of_land", "decomp_protected_factor_upper_bound", "decomp_residual_forest_other_factor", "wb_forest_share_of_land", "decomp_log_share_density", "decomp_log_share_protected_max", "decomp_log_share_forest_other_min"]].copy()
    show.columns = ["模型/ESMAP", "密度因子", "用地因子", "世行保护区占比", "保护区因子（上界）", "林地+其他因子（下界）", "世行森林占比", "密度占对数差", "保护区占（≤）", "林地+其他占（≥）"]
    md.append("## 光伏比值分解（口径差 vs 参数；因子相乘 = 比值；对数份额相加 = 1）"); md.append(md_table(show.reset_index())); md.append("")
    show = df[["model_onwind_gw", "zhong_onwind_high_gw", "zhong_onwind_moderate_gw", "iscience_wind_high_gw", "official_onwind_gw", "ratio_model_onwind_over_zhong_high"]].copy()
    show.columns = ["模型陆上风", "Zhong 高", "Zhong 中", "iScience 风 高", "官方", "模型/Zhong 高"]
    md.append("## 陆上风"); md.append(md_table(show.reset_index())); md.append("")
    show = df[["model_offwind_ac_gw", "model_offwind_dc_gw", "model_offwind_total_gw", "esmap_offwind_fixed_gw", "esmap_offwind_floating_gw", "esmap_offwind_total_gw", "zhong_offwind_high_gw", "official_offwind_gw", "ratio_model_offwind_over_esmap"]].copy()
    show.columns = ["模型 AC", "模型 DC", "模型合计", "ESMAP 固定", "ESMAP 漂浮", "ESMAP 合计", "Zhong 高", "官方", "模型/ESMAP"]
    md.append("## 海上风（ESMAP 无行 = EEZ 内无 ≥ 7 m/s 区域：MY、TH、BN、MM、TL、SG）"); md.append(md_table(show.reset_index())); md.append("")
    (OUT / "POTENTIAL_COMPARISON.md").write_text("\n".join(md), encoding="utf-8")
    dump_json(df.reset_index().to_dict(orient="records"), OUT / "evidence/R2_POTENTIALS.json")
    pd.set_option("display.width", 250)
    print(df[["model_solar_gw", "esmap_l1_x5_1_gw", "ratio_model_solar_over_esmap_l1_x5_1", "decomp_density_factor", "ratio_model_area_over_esmap_l1", "decomp_protected_factor_upper_bound", "decomp_residual_forest_other_factor", "decomp_log_share_density", "decomp_log_share_protected_max", "decomp_log_share_forest_other_min", "main_run_cap_density_5_1_gw"]].round(3).to_string())


if __name__ == "__main__":
    main()
