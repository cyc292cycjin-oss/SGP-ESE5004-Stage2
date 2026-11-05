"""G2-1: national statistics base of Viet Nam and the quality of the 'dispersed' split (B-G2 item 1; template steps 1 and 7 data).

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/v4w07g2_unsd.py

Reads (read only): the UNSD SDMX responses in sdmx/ (queried by v4w07g2_sdmx.py), the 2019 source capsule of the repository (UNdata export
2025-05-02 rows used by the model), the 52 UNdata export files of the upstream checkout, industry_cache.json, the APEC 2022 VN matrix of v3,
the ATS anchor table. Writes tables/VN_*.csv and evidence/_unsd_evidence.json.
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4w07g2_common as cm   # noqa: E402

T = cm.WORK / "tables"
EXPORT_DIR = Path("/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean/data/demand/unsd/data")
IND = ["121", "1211", "1213", "1214", "1214A", "1214B", "1214C", "1214D", "1214E", "1214F", "1214G", "1214H", "1214I", "1214J", "1214O"]
SUBROW_TO_CACHE = {"1211": "iron and steel", "1213": "chemical and petrochemical", "1214A": "non-ferrous metals", "1214B": "non-metallic minerals",
                   "1214C": "transport equipment", "1214D": "machinery", "1214E": "mining and quarrying", "1214F": "food and tobacco",
                   "1214G": "paper pulp and print", "1214H": "wood and wood products", "1214I": "construction", "1214J": "textile and leather",
                   "1214O": "other"}
GROUP = {"0100": "coal", "0110": "coal", "0121": "coal", "0129": "coal", "0311": "coal", "0350": "coal", "0371": "coal", "3000": "gas",
         "4630": "oil", "4670": "oil", "4680": "oil", "4694": "oil", "5110": "biomass", "5120": "biomass", "5130": "biomass", "5140": "biomass",
         "5150": "biomass", "5160": "biomass", "5300": "biomass", "6100": "biomass", "6200": "biomass", "7000": "electricity"}
ACT_2019_2022 = {"iron and steel": (17469.0, 20004.0, "USGS MYB 2022 Vietnam Table 1 raw steel, kt (2019 / 2022)"),
                 "non-metallic minerals": (105533.0, 117626.0, "USGS MYB 2022 Vietnam Table 1 cement, hydraulic, kt (2019 / 2022)"),
                 "chemical and petrochemical": (1150.0, 1180.0, "USGS MYB 2022 Vietnam Table 1 ammonia N content, kt (2019 / 2022)")}


def export_files() -> pd.DataFrame:
    rows = []
    for g in sorted(glob.glob(str(EXPORT_DIR / "*.txt"))):
        L = open(g, encoding="utf-8", errors="replace").read().splitlines()
        d = [x for x in L if x.startswith('"') and x.count('";"') >= 4 and not x.startswith('"Country or Area"')]
        countries = []
        for x in d:
            c = x.split('";"')[0].strip('"')
            if not countries or countries[-1] != c:
                countries.append(c)
        rows.append(dict(file=Path(g).name, sha256=cm.sha256(Path(g)), data_rows=len(d), commodity=d[0].split('";"')[1].split(" - ")[0] if d else "",
                         first_country=countries[0] if countries else "", last_country=countries[-1] if countries else "",
                         has_viet_nam=any(x.startswith('"Viet Nam"') for x in d), at_row_limit=(len(d) == 100000)))
    return pd.DataFrame(rows)


def main():
    T.mkdir(exist_ok=True); (cm.WORK / "evidence").mkdir(exist_ok=True)
    ev = cm.Ev("unsd")
    # ---------------- SDMX receipts and long table ----------------
    rec = []
    for f in cm.SDMX_FILES:
        r = json.loads((cm.WORK / "sdmx" / f"{f}.xml.receipt.json").read_text())
        assert cm.sha256(cm.WORK / "sdmx" / f"{f}.xml") == r["sha256"]
        rec.append(dict(file=f"sdmx/{f}.xml", url=r["url"], utc=r["utc"], http_status=r["http_status"], bytes=r["bytes"], sha256=r["sha256"]))
    pd.DataFrame(rec).to_csv(cm.WORK / "sdmx/SDMX_RECEIPTS.csv", index=False)
    s = cm.sdmx_long()
    s.to_csv(T / "VN_SDMX_LONG.csv", index=False, float_format="%.6f")
    ev.put("sdmx_observations", int(len(s)), "rows", "sdmx/*.xml (UNSD DF_UNDATA_ENERGY, queried 2026-11-06)", "VERIFIED", "A")
    # conversion factor of hard coal by year
    hc = s[(s.commodity == "0100") & (s.transaction == "121")].set_index("year").conversion_factor
    for y, v in hc.items():
        ev.put(f"hard_coal_cf_{y}", float(v), "GJ/t", "SDMX CONVERSION_FACTOR, hard coal, consumption by manufacturing (0100/121)", "VERIFIED", "A")
    # ---------------- 2019: export (model input) against SDMX (current vintage) ----------------
    cap = cm.capsule_vn_2019()
    ff = cm.frozen_factors()
    cap["q"] = pd.to_numeric(cap.Quantity, errors="coerce")
    y19 = s[s.year == 2019].copy()
    out = []
    name_to_code = {v.lower(): k for k, v in cm.codelists()["CL_COMMODITY_NRG"].items()}
    alias = {"coke-oven coke": "0311", "coke oven coke": "0311", "natural gas (including lng)": "3000", "liquefied petroleum gas (lpg)": "4630",
             "liquified petroleum gas (lpg)": "4630", "fuel oil": "4680", "hard coal": "0100", "bagasse": "5120", "fuelwood": "5110", "charcoal": "5160",
             "electricity": "7000", "gas oil/ diesel oil": "4670", "motor gasoline": "4652", "kerosene-type jet fuel": "4661", "biogasoline": "5210"}
    trn = {v.lower(): k for k, v in cm.codelists()["CL_TRANSACTION_NRG"].items()}
    trn.update({"consumption by manufacturing, construction and non-fuel mining industry": "121", "consumption by chemical and petrochemical industry": "1213",
                "consumption by iron and steel industry": "1211", "consumption by other manuf., const. and non-fuel min. ind.": "1214",
                "consumption by industries not elsewhere specified": "1214O", "consumption in agriculture, forestry and fishing": "1232",
                "consumption by commercial and public services": "1235", "consumption in road": "1221"})
    for r in cap.itertuples():
        com = alias.get(r.Commodity.lower(), name_to_code.get(r.Commodity.lower()))
        tr = trn.get(r.Transaction.lower())
        z = y19[(y19.commodity == com) & (y19.transaction == tr)] if com and tr else y19.iloc[0:0]
        f = ff.get(r.Commodity)
        twh_v3 = (r.q * f if f else (r.q * 0.9 / 3600 if r.Unit.strip().startswith("Terajoules") else (r.q / 1000 if "Kilowatt" in r.Unit else np.nan)))
        out.append(dict(commodity=r.Commodity, transaction=r.Transaction, unit=r.Unit, q_export=r.q, footnote_export=r._6 if hasattr(r, "_6") else "",
                        sdmx_commodity=com, sdmx_transaction=tr, q_sdmx=float(z.value.iloc[0]) if len(z) else np.nan,
                        obs_status_sdmx=z.obs_status.iloc[0] if len(z) else "", cf_sdmx=float(z.conversion_factor.iloc[0]) if len(z) else np.nan,
                        twh_v3_factor=twh_v3, twh_sdmx_cf=(float(z.value.iloc[0] * z.conversion_factor.iloc[0]) / 3600 * (0.9 if com == "3000" else 1.0) if len(z) else np.nan)))
    rows19 = pd.DataFrame(out)
    rows19["export_minus_sdmx"] = rows19.q_export - rows19.q_sdmx
    rows19.to_csv(T / "VN_UNSD_2019_ROWS.csv", index=False, float_format="%.6f")
    # SDMX 2019 rows that the export (model) does not contain at all
    have = set(zip(rows19.sdmx_commodity, rows19.sdmx_transaction))
    miss = y19[[(c, t) not in have for c, t in zip(y19.commodity, y19.transaction)]].copy()
    miss = miss[miss.transaction.isin(IND + ["08812", "08822", "1231", "1232", "1235", "1221", "1222", "1224", "12"])]
    miss.to_csv(T / "VN_SDMX_2019_NOT_IN_EXPORT.csv", index=False, float_format="%.6f")
    # ---------------- export truncation (diesel) ----------------
    xf = export_files(); xf.to_csv(T / "VN_EXPORT_FILES.csv", index=False)
    dz = xf[xf.commodity.str.startswith("Gas Oil")].iloc[0]
    ev.put("export_diesel_file_rows", int(dz.data_rows), "rows", f"{dz.file} (UNdata export 2025-05-02)", "VERIFIED", "A")
    ev.put("export_diesel_file_last_country", dz.last_country, "text", dz.file, "VERIFIED", "A")
    ev.put("export_diesel_has_viet_nam", bool(dz.has_viet_nam), "bool", dz.file, "VERIFIED", "A")
    ev.put("export_files_at_row_limit", ";".join(xf[xf.at_row_limit].file), "list", "52 UNdata export files", "VERIFIED", "A")
    dsl = y19[y19.commodity == "4670"].copy()
    dsl["twh_v3_factor"] = dsl.value * ff["Gas Oil/ Diesel Oil"]
    dsl.to_csv(T / "VN_DIESEL_2019_SDMX.csv", index=False, float_format="%.6f")
    for tr, lab in [("12", "final"), ("121", "industry"), ("1211", "steel"), ("1213", "chemical"), ("1214O", "industry_nes"), ("1221", "road"),
                    ("1222", "rail"), ("1232", "agriculture"), ("1235", "commerce")]:
        z = dsl[dsl.transaction == tr]
        if len(z):
            ev.put(f"diesel_2019_{lab}_kt", float(z.value.iloc[0]), "kt", "SDMX 4670 Gas Oil/Diesel Oil 2019", "VERIFIED", "A")
            ev.put(f"diesel_2019_{lab}_twh", float(z.twh_v3_factor.iloc[0]), "TWh", "x frozen upstream factor 0.01194 TWh/kt (42.98 GJ/t)", "EXACT", "A")
    # ---------------- industry sub-row coverage series 2005-2022 ----------------
    ind = s[s.transaction.isin(IND) & s.commodity.isin(GROUP)].copy()
    ind["group"] = ind.commodity.map(GROUP)
    ind["tj_ncv"] = ind.tj * np.where(ind.commodity == "3000", 0.9, 1.0)
    cov = []
    for y, g in ind.groupby("year"):
        tot = g[g.transaction == "121"].tj_ncv.sum()
        explicit = g[g.transaction.isin(["1211", "1213", "1214A", "1214B", "1214C", "1214D", "1214E", "1214F", "1214G", "1214H", "1214I", "1214J"])].tj_ncv.sum()
        nes = g[g.transaction == "1214O"].tj_ncv.sum()
        rows_nz = g[(g.transaction.isin(list(SUBROW_TO_CACHE))) & (g.transaction != "1214O") & (g.value != 0)]
        cov.append(dict(year=y, industry_tj=tot, explicit_subrows_tj=explicit, nes_tj=nes, nes_share=nes / tot if tot else np.nan,
                        explicit_share=explicit / tot if tot else np.nan, n_nonzero_subrow_series=len(rows_nz),
                        subrows_present=";".join(sorted({SUBROW_TO_CACHE[t] for t in rows_nz.transaction})),
                        electricity_explicit_tj=g[(g.group == "electricity") & g.transaction.isin(["1211", "1213", "1214B", "1214F", "1214G", "1214J"])].tj_ncv.sum(),
                        coal_explicit_tj=g[(g.group == "coal") & (g.transaction != "121") & (g.transaction != "1214") & (g.transaction != "1214O")].tj_ncv.sum()))
    cov = pd.DataFrame(cov); cov.to_csv(T / "VN_INDUSTRY_COVERAGE_SERIES.csv", index=False, float_format="%.4f")
    for r in cov.itertuples():
        if r.year in (2015, 2019, 2020, 2021, 2022):
            ev.put(f"industry_nes_share_{r.year}", float(r.nes_share), "share", "SDMX industry rows (NCV basis, gas x0.9): 1214O / 121", "EXACT", "A")
    # ---------------- 2019 sub-sector matrices: UNSD cache, APEC 2022, hybrid ----------------
    cache = json.loads((cm.REPO / cm.CACHE_REL).read_text())
    subs = [k for k in cache["records"][0] if k not in ("country", "carrier")]
    U = pd.DataFrame({r["carrier"]: {k: float(r[k]) for k in subs} for r in cache["records"] if r["country"] == cm.CC})   # MWh (cache units)
    A = pd.read_csv(cm.REPO / cm.APEC_REL).set_index("cache_subsector")
    A = A[[cm.APEC_COL[c] for c in cm.CARS19]].rename(columns={v: k for k, v in cm.APEC_COL.items()}).reindex(subs).fillna(0.0)
    ats = pd.read_csv(cm.REPO / cm.ATS_REL)
    e19 = {c: float(ats[(ats.country == cm.CC) & (ats.sector == "Industry") & (ats.carrier == c)].base_2019_mwh.iloc[0]) for c in cm.CARS19}
    bag_mwh = float(rows19[(rows19.commodity == "Bagasse") & (rows19.sdmx_transaction == "121")].twh_v3_factor.iloc[0]) * 1e6
    A = A.astype(float)
    elr = el_rows_2019()
    for k, x in elr.items():
        ev.put(f"el_row_2019_backcast.{k.replace(' ', '_')}", x / 1e6, "TWh", "UNSD SDMX 2020 electricity sub-row back-cast to 2019 (steel by raw steel output, chemical by share)", "INFERENCE", "C")
    H = hybrid(U, A, bag_mwh, elr); H0 = hybrid(U, A, bag_mwh)
    Ay = A.copy()
    for sub, (q19, q22, _) in ACT_2019_2022.items():
        Ay.loc[sub] = Ay.loc[sub] * q19 / q22
    Hy = hybrid(U, Ay, bag_mwh, elr)
    mats = []
    for name, M in (("unsd_cache", U), ("apec2022", A), ("hybrid", H), ("hybrid_no_el2020", H0), ("apec2022_yearadj", Ay), ("hybrid_yearadj", Hy)):
        for c in cm.CARS19:
            tot = float(M[c].sum())
            for sub in subs:
                mats.append(dict(matrix=name, subsector=sub, carrier=c, cell=float(M.at[sub, c]), share=float(M.at[sub, c]) / tot if tot else 0.0,
                                 sub19_twh=e19[c] * (float(M.at[sub, c]) / tot if tot else (1.0 if sub == "other" else 0.0)) / 1e6))
    mats = pd.DataFrame(mats); mats.to_csv(T / "VN_SHARE_MATRICES_2019.csv", index=False, float_format="%.6f")
    piv = mats.groupby(["matrix", "subsector"]).sub19_twh.sum().unstack(0)
    piv.to_csv(T / "VN_SUBSECTOR_2019_BY_MATRIX.csv", float_format="%.4f")
    for name in ("unsd_cache", "apec2022", "hybrid"):
        for sub in ("iron and steel", "non-metallic minerals", "other", "textile and leather", "food and tobacco", "paper pulp and print"):
            ev.put(f"sub19_{name}_{sub.replace(' ', '_')}_twh", float(piv.at[sub, name]), "TWh", "VN_SUBSECTOR_2019_BY_MATRIX.csv (D1 2019 base x matrix shares)", "EXACT", "C")
    # coke in the APEC run: e19 coal x APEC steel coal share vs the UNSD coke row
    steel_coal_apec = e19["coal"] * A.at["iron and steel", "coal"] / A["coal"].sum() / 1e6
    ev.put("apec_run_steel_coal_2019_twh", steel_coal_apec, "TWh", "e19 coal x APEC 2022 steel coal share (51 / 687.7 PJ)", "EXACT", "C")
    ev.put("unsd_steel_coke_2019_twh", U.at["iron and steel", "coal"] / 1e6, "TWh", "UNSD 2019 coke-oven coke, consumption by iron and steel 5,326 kt x 0.0078334", "EXACT", "A")
    ev.put("coke_spread_to_other_rows_twh", U.at["iron and steel", "coal"] / 1e6 - steel_coal_apec, "TWh", "UNSD steel coke not kept in steel by the APEC shares (v3 VN rule)", "EXACT", "C")
    # APEC 2022 against UNSD 2019 by carrier
    car = []
    for c in cm.CARS19:
        car.append(dict(carrier=c, apec2022_pj=float(A[c].sum()), apec2022_twh=float(A[c].sum()) / 3.6, unsd2019_d1_twh=e19[c] / 1e6,
                        ratio_apec2022_to_unsd2019=float(A[c].sum()) / 3.6 / (e19[c] / 1e6) if e19[c] else np.nan))
    pd.DataFrame(car).to_csv(T / "VN_APEC2022_VS_UNSD2019_CARRIERS.csv", index=False, float_format="%.4f")
    ev.extra["act_2019_2022"] = {k: dict(q2019=v[0], q2022=v[1], source=v[2]) for k, v in ACT_2019_2022.items()}
    ev.write(cm.WORK / "evidence/_unsd_evidence.json")
    pd.set_option("display.width", 220)
    print(cov[["year", "industry_tj", "nes_share", "explicit_share", "n_nonzero_subrow_series"]].round(3).to_string())
    print(piv.round(2).to_string())
    print(pd.DataFrame(car).round(3).to_string())
    print(miss[["commodity_name", "transaction_name", "value", "obs_status"]].to_string())
    print(xf[xf.at_row_limit | ~xf.has_viet_nam].head(60)[["file", "commodity", "data_rows", "last_country", "has_viet_nam"]].to_string())


def el_rows_2019() -> dict:
    """UNSD reports VN industry electricity sub-rows only from 2020 (iron and steel, chemical): back-cast to 2019 (grade C). Steel by raw steel
    output (USGS 17,469 / 19,900 kt), chemical by its 2020 share of industry electricity. MWh."""
    s = cm.sdmx_long()
    v = lambda tr, y: float(s[(s.commodity == "7000") & (s.transaction == tr) & (s.year == y)].value.sum()) * 1e3
    return {"iron and steel": v("1211", 2020) * 17469.0 / 19900.0, "chemical and petrochemical": v("1213", 2020) / v("121", 2020) * v("121", 2019)}


def hybrid(U: pd.DataFrame, A: pd.DataFrame, bag_mwh: float, el_rows: dict | None = None) -> pd.DataFrame:
    """UNSD explicit rows kept; the UNSD 'other' (n.e.s.) amount of each carrier spread over the APEC rows that UNSD does not report for that
    carrier ('other' = APEC non-specified keeps its own APEC weight). Biomass: bagasse to food and tobacco (sugar mills), fuelwood spread over the
    APEC biomass rows except food (APEC 2022 food biomass 34 PJ ~ bagasse). el_rows: electricity rows back-cast from UNSD 2020 (taken out of the
    n.e.s. electricity before the APEC spread). Units: MWh."""
    H = pd.DataFrame(0.0, index=U.index, columns=list(cm.CARS19))
    for c in cm.CARS19:
        explicit = [s for s in U.index if s != "other" and U.at[s, c] > 0]
        for s in explicit:
            H.at[s, c] = U.at[s, c]
        nes = U.at["other", c]
        if c == "biomass":
            H.at["food and tobacco", c] = bag_mwh; nes -= bag_mwh
            explicit = explicit + ["food and tobacco"]
        if c == "electricity" and el_rows:
            for s_, x in el_rows.items():
                H.at[s_, c] += x; nes -= x
            explicit = explicit + list(el_rows)
        w = A[c].copy(); w[explicit] = 0.0
        if w.sum() > 0:
            H[c] += nes * w / w.sum()
        else:
            H.at["other", c] += nes
    return H


if __name__ == "__main__":
    main()
