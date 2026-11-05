"""G2-5: biomass definitions and series of Viet Nam (A3 item 8 = decision 206 item 1; closed-loop rule 206 item 3; template step 7).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_biomass.py

UNSD (two vintages: the UNdata export of 2025-05-02 used by the model = repository capsule, and the SDMX interface queried 2026-11-06), the UN
Energy Balances 2019 publication (W11 table), FAOSTAT FO / QCL (S2 download). Checks: jumps, household / industry reallocation, 'E' status,
FAOSTAT comparison, bagasse against sugar cane, which residues UNSD reports (5140 black liquor, 5150 other vegetal), autoproducer fuelwood.
Writes VN_BIOMASS_CHECK.csv (A6), tables/VN_BIOMASS_SERIES.csv, evidence/_biomass_evidence.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

sys.path.insert(0, str(cm.S2W / "scripts"))
import v4s2_common as s2   # noqa: E402

T = cm.WORK / "tables"
FW = 0.00254   # frozen upstream TWh per thousand m3 fuelwood (9.144 GJ/m3)
BAG = 0.002144   # TWh per kt bagasse (7.72 GJ/t)


def main():
    ev = cm.Ev("biomass")
    s = cm.sdmx_long()
    b = s[s.commodity.isin(["5110", "5120", "5150", "5160", "5130", "5140", "5300"])].copy()
    piv = b.pivot_table(index=["commodity_name", "transaction", "transaction_name"], columns="year", values="value", aggfunc="first")
    stt = b.pivot_table(index=["commodity_name", "transaction"], columns="year", values="obs_status", aggfunc="first")
    piv.to_csv(T / "VN_BIOMASS_SDMX_PIVOT.csv", float_format="%.3f")
    get = lambda com, tr: b[(b.commodity == com) & (b.transaction == tr)].set_index("year").value
    gst = lambda com, tr: b[(b.commodity == com) & (b.transaction == tr)].set_index("year").obs_status
    yrs = range(2005, 2023)
    ser = pd.DataFrame(index=list(yrs))
    ser["fuelwood_production_km3"] = get("5110", "01"); ser["fuelwood_industry_km3"] = get("5110", "121"); ser["fuelwood_industry_status"] = gst("5110", "121")
    ser["fuelwood_households_km3"] = get("5110", "1231"); ser["fuelwood_agriculture_km3"] = get("5110", "1232"); ser["fuelwood_commerce_km3"] = get("5110", "1235")
    ser["fuelwood_autoproducer_km3"] = get("5110", "08812"); ser["fuelwood_charcoal_plants_km3"] = get("5110", "085CH"); ser["fuelwood_final_km3"] = get("5110", "12")
    ser["bagasse_industry_kt"] = get("5120", "121"); ser["other_vegetal_households_tj"] = get("5150", "1231"); ser["charcoal_households_kt"] = get("5160", "1231")
    ser = ser.fillna({c: 0.0 for c in ser.columns if c.endswith(("km3", "kt", "tj"))})
    ser["fuelwood_industry_twh"] = ser.fuelwood_industry_km3 * FW
    ser["households_all_biomass_twh"] = ser.fuelwood_households_km3 * FW + ser.other_vegetal_households_tj / 3600 + ser.charcoal_households_kt * 0.00819
    # FAOSTAT
    FO, QCL = s2.fao("FO"), s2.fao("QCL")
    fwd = FO[(FO.Area == "Viet Nam") & (FO.Element == "Production") & (FO.Item == "Wood fuel, non-coniferous")].set_index("year")
    ser["fao_wood_fuel_m3"] = fwd.value; ser["fao_wood_fuel_flag"] = fwd.flag
    cane = QCL[(QCL.Area == "Viet Nam") & (QCL.Element == "Production") & (QCL.Item == "Sugar cane")].set_index("year")
    ser["fao_sugar_cane_t"] = cane.value
    ser["bagasse_over_cane"] = ser.bagasse_industry_kt * 1e3 / ser.fao_sugar_cane_t
    ser.index.name = "year"
    ser.to_csv(T / "VN_BIOMASS_SERIES.csv", float_format="%.4f")
    # export (model) vs SDMX, 2019
    rows = pd.read_csv(T / "VN_UNSD_2019_ROWS.csv")
    ex = lambda com, tr: float(rows[(rows.commodity == com) & (rows.sdmx_transaction == tr)].q_export.iloc[0]) if len(rows[(rows.commodity == com) & (rows.sdmx_transaction == tr)]) else np.nan
    fw_ex, fw_sd = ex("Fuelwood", "121"), float(ser.at[2019, "fuelwood_industry_km3"])
    bg_ex, bg_sd = ex("Bagasse", "121"), float(ser.at[2019, "bagasse_industry_kt"])
    eb = pd.read_csv(cm.NCVW / "ncv/UN_EB2019_ASEAN11_TJ.csv")
    eb = eb[(eb.country == "VN") & (eb.year == 2019) & (eb.column == "Biofuels and waste")].set_index("flow").value_tj
    eb_ind = float(eb.get("Industriesn.e.s", np.nan)); eb_hh = float(eb.get("Households", np.nan)) if "Households" in eb.index else np.nan
    ser19 = ser.loc[2019]
    pre = ser.loc[2010:2017, "fuelwood_industry_km3"]; post = ser.loc[2020:2021, "fuelwood_industry_km3"]
    for k, v in (("fuelwood_industry_2019_export_km3", fw_ex), ("fuelwood_industry_2019_sdmx_km3", fw_sd), ("bagasse_industry_2019_export_kt", bg_ex),
                 ("bagasse_industry_2019_sdmx_kt", bg_sd), ("fuelwood_industry_mean_2010_2017_km3", float(pre.mean())), ("fuelwood_industry_mean_2020_2021_km3", float(post.mean())),
                 ("un_eb2019_industry_nes_biofuels_tj", eb_ind), ("other_vegetal_households_2019_tj", float(ser19.other_vegetal_households_tj)),
                 ("fuelwood_autoproducer_2019_km3", float(ser19.fuelwood_autoproducer_km3)), ("fao_wood_fuel_2019_m3", float(ser19.fao_wood_fuel_m3)),
                 ("bagasse_over_cane_2019_sdmx", float(ser19.bagasse_over_cane))):
        ev.put(k, v, "km3" if k.endswith("km3") else ("kt" if k.endswith("kt") else ("TJ" if k.endswith("tj") else ("m3" if k.endswith("m3") else "ratio"))),
               "UNSD SDMX 2026-11 / UNdata export 2025-05-02 / UN EB 2019 / FAOSTAT", "VERIFIED" if "mean" not in k and "over" not in k else "EXACT", "B")
    # A6 table
    def twh_fw(km3):
        return km3 * FW
    A6 = pd.DataFrame([
        dict(commodity="5110 fuelwood", flow="consumption not elsewhere specified (industry)", value_2019=f"{fw_ex:,.1f} thousand m3 (export 2025-05-02, model) = {twh_fw(fw_ex):.2f} TWh; SDMX 2026-11: {fw_sd:,.1f} (status {ser19.fuelwood_industry_status}) = {twh_fw(fw_sd):.2f} TWh",
             series_note=f"industry 2010-2017 mean {pre.mean():,.0f}, 2020-2021 mean {post.mean():,.0f} thousand m3 (SDMX); households reported only to {int(ser[ser.fuelwood_households_km3 > 0].index.max())}, other vegetal material (households) from 2016; the SDMX vintage revised 2019 industry by {fw_sd - fw_ex:+,.0f} thousand m3",
             faostat_compare=f"FAOSTAT wood fuel 2019 {ser19.fao_wood_fuel_m3:,.0f} m3 ({ser19.fao_wood_fuel_flag}, constant since 2015: carry-forward); UNSD fuelwood production 2019 {ser19.fuelwood_production_km3:,.0f} thousand m3 (SDMX)",
             proposed_main=f"keep the model (export) value {fw_ex:,.1f} thousand m3 ({twh_fw(fw_ex):.2f} TWh): equal to the 2005-2014 level (A, 11.8-14.8) and to the 2020-2021 mean {post.mean():,.0f} (E)",
             proposed_sensitivity=f"low: SDMX 2026-11 vintage {fw_sd:,.1f} (E, {twh_fw(fw_sd):.2f} TWh), a low point of the 2015-2019 break (households fuelwood set to 0 from 2018, other vegetal households from 2016)"),
        dict(commodity="5120 bagasse", flow="consumption n.e.s. (industry)", value_2019=f"export {bg_ex:,.1f} kt ({bg_ex * BAG:.2f} TWh); SDMX {bg_sd:,.1f} kt ({bg_sd * BAG:.2f} TWh)",
             series_note="no jump; follows sugar cane", faostat_compare=f"SDMX bagasse / FAOSTAT sugar cane 2019 = {ser19.bagasse_over_cane:.3f} t/t (wet bagasse; IRENA 2017 residue factor 0.2 is lower)",
             proposed_main="keep the reported quantity in T_v2 (UNSD reports it: 206 item 3 'already in T_v2'); assign it to food and tobacco (hybrid split)",
             proposed_sensitivity="closed-loop reading for sugar mills (own residue): bagasse and its heat outside T_v2"),
        dict(commodity="5140 black liquor", flow="all", value_2019="not reported (no VN series in SDMX 2005-2022)", series_note="",
             faostat_compare="FAOSTAT 2019 chemical + dissolving pulp 250 kt (E / I) -> about 1.5 TWh black liquor (ETSAP 22 GJ/t)",
             proposed_main="outside T_v2 (closed loop); listed in the pulp and paper row as closed_loop_biomass", proposed_sensitivity=""),
        dict(commodity="5150 other vegetal material and residues", flow="households only (2016-2022)", value_2019=f"{ser19.other_vegetal_households_tj:,.0f} TJ households; no industry series; not in the UNdata export used by the model",
             series_note="series starts in 2016 (IEA 2021 edition: bagasse, other solid vegetal matters added for 2016-2019 from APERC)", faostat_compare="FAOSTAT rice 2019 43.5 Mt (husk is the main candidate, INFERENCE)",
             proposed_main="industry: nothing reported, so residues burned in mills (rice husk, coffee husk) stay outside T_v2 (closed loop)", proposed_sensitivity="households: coverage gap of the export (W12 item 4)"),
        dict(commodity="5110 fuelwood", flow="transformation in electricity plants - autoproducers", value_2019=f"{ser19.fuelwood_autoproducer_km3:,.1f} thousand m3 = {twh_fw(ser19.fuelwood_autoproducer_km3):.2f} TWh",
             series_note="national electricity from solid biofuels 2019 only 30 GWh (SDMX 7000T/01SBF): the fuel serves own-use heat (INFERENCE)",
             faostat_compare="", proposed_main="leave outside T_v2 (own-use heat of autoproducers = closed loop)", proposed_sensitivity="move to industry final consumption (+10.4 TWh 2019)"),
        dict(commodity="UN Energy Balances 2019 publication", flow="industries n.e.s., biofuels and waste", value_2019=f"{eb_ind:,.0f} TJ = {eb_ind / 3600:.1f} TWh",
             series_note="third vintage: far above both UNSD database vintages (export 47.7 TWh, SDMX 30.1 TWh for fuelwood + bagasse)", faostat_compare="",
             proposed_main="not used (superseded by the database revisions)", proposed_sensitivity="")])
    A6.to_csv(cm.WORK / "VN_BIOMASS_CHECK.csv", index=False)
    cm.jdump(dict(fuelwood_industry_2019_export_km3=fw_ex, fuelwood_industry_2019_sdmx_km3=fw_sd, fuelwood_2020_2021_mean_km3=float(post.mean()),
                  bagasse_2019_export_kt=bg_ex, bagasse_2019_sdmx_kt=bg_sd), cm.WORK / "evidence/_biomass_chain_inputs.json")
    ev.write(cm.WORK / "evidence/_biomass_evidence.json")
    pd.set_option("display.width", 250)
    print(ser[["fuelwood_production_km3", "fuelwood_industry_km3", "fuelwood_industry_status", "fuelwood_households_km3", "fuelwood_autoproducer_km3", "fuelwood_charcoal_plants_km3",
               "bagasse_industry_kt", "other_vegetal_households_tj", "fao_wood_fuel_m3", "bagasse_over_cane"]].round(1).to_string())
    print(fw_ex, fw_sd, bg_ex, bg_sd, eb_ind)


if __name__ == "__main__":
    main()
