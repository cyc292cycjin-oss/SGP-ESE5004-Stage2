"""DFX v3: locate the 1.2 GWh closure residual of the v2 bridge by sector (anchor + attributed conversions - model loads). Read-only."""
import json
from pathlib import Path

import pandas as pd

OUT = Path("/mnt/d/ResearchWorkspaces/ASEAN/work/p1_dfx_20261026")
DEM = Path("/home/jin/wt_dfx_v3_20261026/research_inputs/demand_v5")
C11 = ["BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN"]
d1 = pd.read_csv(OUT / "DEMAND_BY_COUNTRY_SECTOR_CARRIER_v2.csv", keep_default_na=False); r = d1[(d1.network_account != "memo") & d1.country.isin(C11)]
an = pd.read_csv(DEM / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
dt = pd.read_csv(DEM / "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False); dt["v"] = pd.to_numeric(dt.value_2050_mwh, errors="coerce").fillna(0.0) / 1e6
par = json.loads((OUT / "evidence/DFX_D1_CHECKS_v2.json").read_text())["ledger_parameters"]
rows = []
for c in C11:
    a = an.loc[c]; rc = r[r.country == c]; tc = dt[dt.country == c]
    # transport: anchor -> EV conversion + shipping conversion = model
    land = float(tc[(tc.sector == "Transport") & tc.account.isin(["RoadResidualFuel", "TransportNEC", "TransportEmbeddedFuelParent"]) & (tc.carrier != "electricity")].v.sum())
    ev = float(rc[rc.subsector == "road (land transport, EV)"].twh.sum()); dship = float(tc[tc.account == "DomesticShippingFuel"].v.sum()); shm = float(rc[rc.subsector == "domestic shipping"].twh.sum())
    tr = a.ras_sector_anchor_Transport_mwh / 1e6 + (ev - land) + (shm - dship) - float(rc[rc.sector == "Transport"].twh.sum())
    # buildings: anchor - zeroed negatives + cooking conversion = model
    bld = 0.0
    for key, sec in (("residential", "Residential"), ("commercial", "Commercial")):
        raw = a[f"{key}_fuel_anchor_raw_mwh"] / 1e6; zer = a[f"{key}_fuel_zeroed"]
        bio = float(tc[(tc.sector == sec) & (tc.carrier == "biomass")].v.sum()); cc = float(rc[(rc.sector == sec) & (rc.carrier == "clean cooking useful")].twh.sum())
        adj = (-raw if zer == "negative" else (-raw if zer == "no_2019_fuel_rows" else 0.0))
        bld += a[f"ras_sector_anchor_{sec}_mwh"] / 1e6 + adj + (cc - bio) - float(rc[rc.sector == sec].twh.sum())
    raw = a.agriculture_fuel_anchor_raw_mwh / 1e6; zer = a.agriculture_fuel_zeroed; adj = -raw if zer else 0.0
    ag_oil = float(tc[(tc.sector == "AgricultureOthers") & tc.carrier.isin(["oil", "unclassified_fuel"])].v.sum()); ag_m = float(rc[(rc.sector == "AgricultureOthers") & rc.carrier.isin(["agriculture machinery electric", "oil final energy"])].twh.sum())
    ag_bio = float(tc[(tc.sector == "AgricultureOthers") & (tc.carrier == "biomass")].v.sum()); ag_bm = float(rc[(rc.sector == "AgricultureOthers") & rc.carrier.isin(["biomass final energy", "industry heat"])].twh.sum())
    ag = a.ras_sector_anchor_AgricultureOthers_mwh / 1e6 + adj + (ag_m - ag_oil) + (ag_bm - ag_bio) - float(rc[rc.sector == "AgricultureOthers"].twh.sum())
    neu_t = float(tc[tc.sector == "NonEnergyUse"].v.sum()); hvc = float(tc[(tc.sector == "NonEnergyUse") & (tc.carrier == "oil") & tc.account.isin(["NonEnergy:Naphtha", "NonEnergy:Ethane", "NonEnergy:Liquefied petroleum gas (LPG)", "NonEnergy:Natural gas liquids"])].v.sum())
    neu = neu_t - 0.6 * hvc - float(rc[rc.sector == "NonEnergyUse"].twh.sum())
    rows.append(dict(country=c, transport=tr, buildings=bld, agriculture=ag, neu=neu, ag_bio=ag_bio, ag_bm=ag_bm, ag_oil=ag_oil, ag_m=ag_m))
df = pd.DataFrame(rows).set_index("country"); pd.set_option("display.width", 200)
print((df * 1e3).round(4).to_string()); print("sums (GWh):", (df[["transport", "buildings", "agriculture", "neu"]].sum() * 1e3).round(4).to_dict())
