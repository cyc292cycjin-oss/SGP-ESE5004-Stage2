"""V4 W08 checklist section 9 (G5 recommended variant MAIN; I2 section 3.3): hourly shapes of the industrial loads.

Inputs: research_inputs/industry_v4/INDUSTRY_PROFILES_8760.parquet + INDUSTRY_PROFILE_INDEX.csv (G5 PROFILES_8760.parquet / PROFILE_INDEX.csv: 2013
UTC hour starts, tz-naive like the network snapshots, each curve annual mean 1.0, already shifted to the node's legal time zone; electricity shapes
from FfE dataset 59 'Normalized Industrial Electrical Load Profiles' - CC BY 4.0, (c) FfE, eXtremOS Project; heat shapes from NREL 'Manufacturing
Thermal Energy Use in 2014' (McMillan 2019, DOI 10.7799/1570008) - DOE/NREL/ALLIANCE data licence: credit DOE/NREL/ALLIANCE); node time zones
research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv.
Rule (G5 g5_peaks.py composition, I2 i2_peaks.py key extension; unchanged): per country x time zone x energy type (elec / heat) the composite shape
= sum over sub-sector keys of 2050 energy x the key's MAIN curve / sum of the energies (annual mean 1.0); 'dispersed' is split into keys by the
2050 energy of the s3_0 rows (PyPSA-Eur sector -> key, SECTOR_KEY); continuous processes are flat curves in MAIN; 'other' = the ASEAN dispersed
mix shape; fuels, feedstocks, hydrogen, ammonia and methanol stay constant. A node x carrier load = annual energy x the composite of its zone
(3 h snapshots: mean of the three hours). Electricity: 'industry electricity'; heat: the low-temperature heat load and the three band loads.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
from v4_common import ROOT, V4_DIR   # noqa: E402

HEAT = ["heat", "heat_high", "heat_medium_a", "heat_medium_b"]
V3_KEY = {"steel": "steel", "cement": "cement", "ammonia": "ammonia", "nonferrous_nickel": "nickel", "nonferrous_aluminium_primary": "aluminium_primary",
          "nonferrous_alumina": "alumina", "nonferrous_copper": "copper", "other": "other",
          "pulp_paper": "pulp_paper", "pulp_paper_new_lines": "pulp_paper", "hvc": "ethylene", "hvc_new_plants": "ethylene", "methanol": "methanol",
          "methanol_new_plants": "methanol", "glass": "glass_lime", "lime": "glass_lime", "alumina": "alumina", "copper": "copper"}
SECTOR_KEY = {"Ammonia": "ammonia", "Chlorine": "chlorine", "HVC": "ethylene", "Methanol": "methanol", "Other chemicals": "chemicals_other",
              "Pharmaceutical products etc.": "pharma", "Food, beverages and tobacco": "food", "Machinery equipment": "machinery", "Transport equipment": "transport_equipment",
              "Textiles and leather": "textiles", "Wood and wood products": "wood", "Paper production": "pulp_paper", "Pulp production": "pulp_paper",
              "Printing and media reproduction": "printing", "Alumina production": "alumina", "Aluminium - primary production": "aluminium_primary",
              "Aluminium - secondary production": "aluminium_secondary", "Other non-ferrous metals": "nonferrous_other", "Ceramics & other NMM": "ceramics_nmm",
              "Glass production": "glass_lime"}
OTHER_BUCKET_ROWS = ("other", "construction", "mining and quarrying")
TZ_CSV = ROOT / "research_inputs/transport_v3/EV_NODE_TIMEZONE_V3.csv"


def node_tz() -> pd.Series:
    return pd.read_csv(TZ_CSV).set_index("node").utc_offset_h


def dispersed_rows(pz: pd.DataFrame) -> pd.DataFrame:
    """s3_0 energy-fallback rows ('all (see mapping shares)') outside the other bucket, by PyPSA-Eur sector (I2 pz_dispersed)."""
    z = pz[pz.carrier == "all (see mapping shares)"].copy()
    z["pypsa_eur_sector"] = z.method.astype(str).str.split(" via ").str[-1]
    z = z[~z.subsector.isin(OTHER_BUCKET_ROWS)]
    return z.rename(columns={"subsector": "unsd_row"})[["country", "unsd_row", "pypsa_eur_sector", "mwh_2019", "mwh_2050"]]


NEW_KEYS = ("pulp_paper", "pulp_paper_new_lines", "hvc", "hvc_new_plants", "methanol", "methanol_new_plants", "glass", "lime", "alumina", "copper")


def composition(parts_by_country: dict, disp: pd.DataFrame, nodes) -> pd.DataFrame:
    """country x zone x key x etype energy (MWh/a). parts_by_country {cc: {sub-sector: {carrier: MWh}}} (v4_industry snapshot parts).
    ID zone split (G5 / I2 rule): the v3 sub-sector node shares INDUSTRY_NODE_SHARES_V3.csv (ammonia on the petrochem shares); the v4 sub-sectors
    on their v4 node shares (v4_outputs.Nodes, electricity)."""
    TZ = node_tz(); disp = disp.copy(); disp["key"] = disp.pypsa_eur_sector.map(SECTOR_KEY)
    NS = pd.read_csv(ROOT / "research_inputs/industry_v3/INDUSTRY_NODE_SHARES_V3.csv")
    rows = []
    for c, parts in parts_by_country.items():
        for sub, car_v in parts.items():
            for car, x in car_v.items():
                et = "elec" if car == "electricity" else ("heat" if car in HEAT else None)
                if et is None or x == 0:
                    continue
                if sub == "dispersed":
                    d = disp[disp.country == c]
                    split = (d.groupby("key").mwh_2050.sum() / d.mwh_2050.sum()).to_dict() if len(d) and d.mwh_2050.sum() > 0 else {"other": 1.0}
                else:
                    split = {V3_KEY[sub]: 1.0}
                if c == "ID":
                    if sub in NEW_KEYS:
                        sh, _ = nodes.shares("ID", sub, "electricity")
                        ns = pd.DataFrame(dict(node=list(sh), share=list(sh.values())))
                    else:
                        ns = NS[(NS.country == "ID") & (NS.subsector == ("petrochem" if sub == "ammonia" else sub))]
                    if ns.empty:
                        raise ValueError("no ID node shares for " + sub)
                    zs = ns.assign(z=ns.node.map(TZ)).groupby("z").share.sum()
                    zs = zs / zs.sum()
                else:
                    zs = pd.Series({float(TZ[TZ.index.str.startswith(c)].iloc[0]): 1.0})
                for k, f in split.items():
                    for z, s in zs.items():
                        rows.append(dict(country=c, zone=f"UTC+{z:g}", key=k, etype=et, mwh=x * f * s))
    return pd.DataFrame(rows).groupby(["country", "zone", "key", "etype"], as_index=False).mwh.sum()


class Shapes:
    def __init__(self, weights: pd.DataFrame, variant: str = "MAIN"):
        self.P = pd.read_parquet(V4_DIR / "INDUSTRY_PROFILES_8760.parquet"); self.I = pd.read_csv(V4_DIR / "INDUSTRY_PROFILE_INDEX.csv")
        self.W = weights; self.variant = variant; self.cache = {}

    def curve(self, key: str, et: str, c: str, zone: str) -> np.ndarray:
        q = self.I[(self.I.variant == self.variant) & (self.I.subsector == key) & (self.I.etype == et)]
        zz = q[q.zone == zone]
        if zz.empty:
            zz = q[q.zone == f"{c}@{zone}"]
        if len(zz) != 1:
            raise ValueError(f"curve lookup {self.variant} {key} {et} {c} {zone}: {len(zz)}")
        return self.P[zz.curve_id.iloc[0]].to_numpy()

    def composite(self, c: str, zone: str, et: str) -> np.ndarray | None:
        k = (c, zone, et)
        if k not in self.cache:
            ce = self.W[(self.W.country == c) & (self.W.zone == zone) & (self.W.etype == et) & (self.W.mwh > 0)]
            if ce.empty:
                self.cache[k] = None
            else:
                y = sum(r.mwh * self.curve(r.key, et, c, r.zone) for r in ce.itertuples()) / float(ce.mwh.sum())
                self.cache[k] = y / y.mean()   # mean 1.0 (the curves are mean 1; the division only removes rounding)
        return self.cache[k]

    def shape_3h(self, c: str, node: str, et: str, n_snap: int) -> np.ndarray | None:
        tz = node_tz()
        if node not in tz.index:
            return None
        y = self.composite(c, f"UTC+{float(tz[node]):g}", et)
        if y is None:
            return None
        if n_snap == 8760:
            return y
        if n_snap <= 0 or 8760 % n_snap:   # V4 D2a (Fable F-12): any regular aggregation of the hourly year (2920 x 3 h, 1460 x 6 h, 365 x 24 h, ...)
            raise ValueError(f"industry curves: {n_snap} snapshots (a divisor of 8760 expected: 8760, 2920 x 3 h, 365 x 24 h, ...)")
        return y.reshape(n_snap, 8760 // n_snap).mean(1)
