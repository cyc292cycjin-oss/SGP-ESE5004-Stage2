"""V4 S1 section 4 (items 2-6): BPS IBS 2019 energy by industrial code, mapping, coverage against UNSD / HEESI, proposed split of the ID 'other' bucket.

    PYTHONHASHSEED=0 python scripts/v4s1_bps_energy.py --work <work dir> --repo /home/jin/wt_v4_data      (WSL pypsa-earth python)

Input: s1/ID_BPS_IBS_2019_RAW.csv (v4s1_bps_parse.py; IBS-total lines, 2-digit codes as printed, some 3-4 digit codes), HEESI 2025 Annex 03 factors
(s1/HEESI_2025_VALUES_USED.csv), s1/ID_CAPTIVE_*.csv (section 1), the repository v3 tables.
2. Conversion: HEESI 2025 Annex 03 (PDF p.170, printed p.154) multipliers to BOE, BOE = 3.6 GJ / 0.6130 (electric power factor) = 5.873 GJ:
   gasoline (Bensin) kL x 5.8275 (Premium), diesel (Minyak Solar) kL x 6.4871 (Gasoil), coal t x 4.2000 (Kalimantan coal, used before 2023; average
   coal 3.4554 as sensitivity; the model's UNSD factor 25.8 GJ/t also listed), briquette t x 3.5638, gas m3 x 0.0353147 MSCF/m3 x 0.1796 (PGN and
   non-PGN), LPG litres x 0.54 kg/l (assumption: no density on disk, grade C) x 8.5246 BOE/t. Lubricant is non-energy use and kept in litres only.
   Electricity end use = purchased + generated - sold.
3. Mapping KBLI 2015 2-digit -> UNSD row (IRES / ISIC rev.4 divisions) -> v3 sub-sector for ID (ID has UNSD rows only for chemicals, iron and steel
   and 'other'), with 2394 cement and 241 / 242 / 2431 / 2432 split out.
4. Comparison by carrier: IBS total against the UNSD 2019 ID industry (D1 base) and the UNSD rows, and against HEESI 2025 table 5.1.1 (2019).
5. Proposed split of the ID 2019 'other' bucket (633.14 TWh on the v2 basis = UNSD other row after the v3 cement deduction): captive coal (section 1
   central, low / high listed), v3 explicit non-ferrous (2019 equivalent), IBS-attributable energy by KBLI (grid electricity only, so that self-generation
   is not counted twice), residual. Nothing changes the v3 shares.
Outputs: s1/ID_BPS_IBS_2019_BY_KBLI.csv, s1/ID_BPS_VS_UNSD_2019.csv, s1/ID_OTHER_BUCKET_SPLIT_PROPOSED.csv, s1/_bps_energy_evidence.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4s1_common as cm   # noqa: E402

LPG_KG_PER_L = 0.54
MSCF_PER_M3 = 35.3147 / 1000.0
UNSD_OF = {"10": "food and tobacco", "11": "food and tobacco", "12": "food and tobacco", "13": "textile and leather", "14": "textile and leather",
           "15": "textile and leather", "16": "wood and wood products", "17": "paper pulp and print", "18": "paper pulp and print",
           "19": "energy sector (coke and refined petroleum): not industry", "20": "chemical and petrochemical", "21": "chemical and petrochemical",
           "22": "non-specified (rubber and plastics)", "23": "non-metallic minerals", "24": "iron and steel / non-ferrous metals", "25": "machinery", "26": "machinery",
           "27": "machinery", "28": "machinery", "29": "transport equipment", "30": "transport equipment", "31": "non-specified", "32": "non-specified",
           "33": "non-specified (repair and installation; INFERENCE)"}
SPLIT_CODES = {"2394": ("non-metallic minerals: cement", "cement (explicit, v3 2019 deduction from other)", "other"),
               "2410": ("iron and steel", "steel (explicit; UNSD iron-and-steel row)", "iron and steel"),
               "2431": ("iron and steel (casting)", "steel (explicit; UNSD iron-and-steel row)", "iron and steel"),
               "2420": ("non-ferrous metals (incl. nickel, aluminium, copper)", "non-ferrous explicit (nickel, aluminium, alumina, copper)", "other"),
               "2432": ("non-ferrous metals (casting)", "non-ferrous explicit", "other")}


def v3_of(code2: str) -> tuple[str, str]:
    """(v3 sub-sector for ID, UNSD row present for ID)."""
    if code2 in ("20", "21"):
        return "dispersed (UNSD chemical row; ammonia explicit)", "chemical and petrochemical"
    if code2 == "19":
        return "outside industry", "-"
    if code2 == "24":
        return "split: steel (241, 2431) / non-ferrous explicit (242, 2432)", "iron and steel / other"
    if code2 == "23":
        return "split: cement explicit (2394) / other", "other"
    return "other", "other"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); ap.add_argument("--repo", type=Path, default=cm.REPO); a = ap.parse_args()
    R = a.repo / "research_inputs"; out = a.work / "s1"
    H = pd.read_csv(out / "HEESI_2025_VALUES_USED.csv")
    BOE = cm.boe_gj(H)
    f = {k: cm.hv(H, k, None, "Annex 03") for k in ("Premium", "Gasoil", "Kalimantan Coal", "Average Coal", "Briquette", "Natural Gas", "LPG")}
    cf = cm.conv_factors()
    twh = lambda boe: boe * BOE / 3.6e6
    B = pd.read_csv(out / "ID_BPS_IBS_2019_RAW.csv", dtype={"code": str})
    t5 = B[(B.table == "5.1") & (B.line == "total")].set_index("code"); t6 = B[(B.table == "6a.1") & (B.line == "total")].set_index("code")
    codes = [c for c in t5.index if len(c) == 2] + list(SPLIT_CODES) + ["Total"]
    rows = []
    for c in codes:
        r5, r6 = t5.loc[c], t6.loc[c]
        q = dict(gasoline_l=r6.gasoline_l, diesel_l=r6.diesel_l, coal_kg=r6.coal_kg, briquette_kg=r6.coal_briquette_kg, gas_pgn_m3=r6.gas_pgn_m3,
                 gas_nonpgn_m3=r6.gas_nonpgn_m3, lpg_l=r6.lpg_l, lubricant_l=r6.lubricant_l, el_generated_kwh=r5.el_generated_kwh,
                 el_purchased_kwh=r5.el_purchased_kwh, el_sold_kwh=r5.el_sold_kwh)
        e = dict(gasoline_twh=twh(q["gasoline_l"] / 1e3 * f["Premium"]), diesel_twh=twh(q["diesel_l"] / 1e3 * f["Gasoil"]),
                 lpg_twh=twh(q["lpg_l"] * LPG_KG_PER_L / 1e3 * f["LPG"]), coal_twh=twh(q["coal_kg"] / 1e3 * f["Kalimantan Coal"]),
                 coal_twh_avgcoal=twh(q["coal_kg"] / 1e3 * f["Average Coal"]), coal_twh_model_factor=q["coal_kg"] / 1e6 * cf["Hard coal"],
                 briquette_twh=twh(q["briquette_kg"] / 1e3 * f["Briquette"]),
                 gas_twh=twh((q["gas_pgn_m3"] + q["gas_nonpgn_m3"]) * MSCF_PER_M3 * f["Natural Gas"]),
                 el_purchased_twh=q["el_purchased_kwh"] / 1e9, el_generated_twh=q["el_generated_kwh"] / 1e9, el_sold_twh=q["el_sold_kwh"] / 1e9)
        e["oil_twh"] = e["gasoline_twh"] + e["diesel_twh"] + e["lpg_twh"]
        e["coal_all_twh"] = e["coal_twh"] + e["briquette_twh"]
        e["el_end_use_twh"] = e["el_purchased_twh"] + e["el_generated_twh"] - e["el_sold_twh"]
        e["el_grid_net_twh"] = e["el_purchased_twh"] - e["el_sold_twh"]
        e["fuels_twh"] = e["oil_twh"] + e["coal_all_twh"] + e["gas_twh"]
        e["total_end_use_twh"] = e["fuels_twh"] + e["el_end_use_twh"]
        if c in SPLIT_CODES:
            unsd_row, v3s, present = SPLIT_CODES[c]
        elif c == "Total":
            unsd_row, v3s, present = "all manufacturing (IBS)", "", ""
        else:
            unsd_row = UNSD_OF[c]; v3s, present = v3_of(c)
        rows.append(dict(kbli=c, level=("total" if c == "Total" else len(c)), unsd_row_irs=unsd_row, unsd_row_present_for_id=present, v3_subsector_id=v3s, **q, **e,
                         source="BPS Statistik Industri Manufaktur Indonesia 2019 (IBS large and medium): table 5.1 (PDF p.109-120), table 6a.1 (p.123-148); IBS-total lines",
                         conversion="HEESI 2025 Annex 03; BOE = 5.873 GJ; LPG 0.54 kg/l assumed"))
    K = pd.DataFrame(rows)
    two = K[K.level == 2]
    tot = K[K.kbli == "Total"].iloc[0]
    for col in ("fuels_twh", "el_end_use_twh", "coal_kg", "gas_pgn_m3"):
        if abs(two[col].sum() - tot[col]) > 1e-6 * max(1.0, abs(tot[col])):
            raise ValueError(f"2-digit codes do not add up to the printed total: {col}")
    K.to_csv(out / "ID_BPS_IBS_2019_BY_KBLI.csv", index=False, float_format="%.12g")

    # ---- 4. comparison with UNSD and HEESI ---------------------------------------------------------------------------------
    dem = pd.read_csv(R / "demand_v5/DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv", keep_default_na=False)
    did = dem[(dem.country == "ID") & (dem.sector == "Industry")]
    e19 = {r.carrier: float(r.base_2019_mwh) / 1e6 for r in did.itertuples()}
    cache = json.loads((R / "assembly_v1/sources/industry_cache.json").read_text())
    rec = {r["carrier"]: r for r in cache["records"] if r["country"] == "ID"}
    rowsh = lambda row, car: float(rec[car][row]) / sum(float(rec[car][k]) for k in rec[car] if k not in ("country", "carrier"))
    unsd_rows = {row: {car: e19[car] * rowsh(row, car) for car in e19} for row in ("chemical and petrochemical", "iron and steel", "other")}
    m_chem = two.kbli.isin(["20", "21"]); m_steel = K.kbli.isin(["2410", "2431"])
    bps = {"all industry": two[two.kbli != "19"], "chemical and petrochemical": two[m_chem], "iron and steel": K[m_steel],
           "other": pd.concat([two[~two.kbli.isin(["19", "20", "21", "24"])], K[K.kbli.isin(["2420", "2432"])]])}
    heesi = dict(coal=twh(cm.hv(H, "Coal", 2019, "5.1.2") ), electricity=cm.hv(H, "Electricity", 2019, "5.1.1") / 1e3,
                 gas=twh(cm.hv(H, "Gas", 2019, "5.1.1") * 1e3 * f["Natural Gas"]), oil=twh(cm.hv(H, "Total oil fuel", 2019, "5.1.1") * f["Gasoil"]),
                 lpg=twh(cm.hv(H, "LPG", 2019, "5.1.1") * f["LPG"]))
    cmp_ = []
    carmap = {"coal": "coal_all_twh", "oil": "oil_twh", "gas": "gas_twh", "electricity": "el_end_use_twh", "biomass": None}
    for row, z in bps.items():
        ref = {k: sum(e19.values()) if False else (e19[k] if row == "all industry" else unsd_rows[row][k]) for k in e19}
        for car, colname in carmap.items():
            v = float(z[colname].sum()) if colname else 0.0
            cmp_.append(dict(scope=row, carrier=car, bps_ibs_twh=v, unsd_2019_twh=ref[car], coverage=(v / ref[car] if ref[car] else np.nan),
                             heesi_2019_twh=(heesi.get(car) if row == "all industry" else np.nan),
                             note=("IBS 6a.1 has no biomass / fuel oil / kerosene column" if car in ("biomass", "oil") else "") +
                                  ("; HEESI oil = total oil fuel at the gasoil factor (approximate)" if car == "oil" and row == "all industry" else "")))
        v = float(z.total_end_use_twh.sum()); refT = sum(ref.values())
        cmp_.append(dict(scope=row, carrier="total", bps_ibs_twh=v, unsd_2019_twh=refT, coverage=v / refT, heesi_2019_twh=np.nan, note=""))
    extra = [dict(scope="all industry", carrier="electricity purchased only", bps_ibs_twh=float(tot.el_purchased_twh), unsd_2019_twh=e19["electricity"],
                  coverage=float(tot.el_purchased_twh) / e19["electricity"], heesi_2019_twh=cm.hv(H, "PLN sales Industry", 2019) / 1e3,
                  note="HEESI 6.4.4 PLN sales to the industry tariff 2019"),
             dict(scope="all industry", carrier="electricity self-generated", bps_ibs_twh=float(tot.el_generated_twh), unsd_2019_twh=np.nan, coverage=np.nan,
                  heesi_2019_twh=cm.hv(H, "Non PLN consumption Industry", 2019) / 1e3, note="HEESI 6.4.4 non-PLN industrial consumption 2019; UNSD autoproducer production 44.80 TWh")]
    CMP = pd.DataFrame(cmp_ + extra)
    CMP.to_csv(out / "ID_BPS_VS_UNSD_2019.csv", index=False, float_format="%.6g")

    # ---- 5. proposed split of the 2019 other bucket -------------------------------------------------------------------------
    ob = pd.read_csv(R / "demand_v5/INDUSTRY_2050_OTHER_BUCKET.csv"); ob = ob[(ob["mode"] == "aeo8_ats_anchor") & (ob.country == "ID")].iloc[0]
    cars = ("coal", "oil", "gas", "biomass", "electricity")
    other = {c: float(ob[f"other_2019_{c}_mwh"]) / 1e6 for c in cars}
    O = pd.read_csv(out / "ID_CAPTIVE_OPTIONS.csv")
    base_o = O[(O.option == "a") & (O.level == "central")].iloc[0]
    capt = {}
    for lv in ("low", "central", "mid", "high"):
        bo = O[(O.option == "b") & (O.level == lv)].iloc[0]
        capt[lv] = float(base_o.other_2019_coal_twh - bo.other_2019_coal_twh)
    E = pd.read_csv(out / "ID_CAPTIVE_COAL_2019.csv")
    ec = E[(E.level == "central") & (E.group != "合计")]
    v3ev = json.loads((R / "industry_v3/INDUSTRY_V3_EVIDENCE.json").read_text())
    gf = v3ev["cases"]["main"]["nonferrous"]["ID:nonferrous_nickel"]["growth_factor"]
    sub = pd.read_csv(R / "industry_v3/INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv"); sid = sub[(sub.case == "main") & (sub.country == "ID")]
    ne = v3ev["nickel_unit_energy"]; nf = pd.read_csv(R / "industry_v3/NONFERROUS_PRODUCTION_V3.csv"); q19 = float(nf[nf.route == "nickel"].q_2019_t.sum())
    split = []

    def blk(block, label, vec, grade, status, basis):
        split.append(dict(block=block, label=label, **{f"{c}_twh": vec.get(c, 0.0) for c in cars}, total_twh=sum(vec.values()), grade=grade, status=status, basis=basis))
    blk("0", "ID 2019 'other' bucket, v2 basis (UNSD other row after the v3 cement deduction)", other, "B / C", "VERIFIED", "INDUSTRY_2050_OTHER_BUCKET.csv aeo8_ats_anchor; v3-equivalent = x 0.954658")
    sc = capt["central"] / ec.coal_in_industry_twh_model.sum()
    for (grp, s3), g in ec.groupby(["group", "v3_subsector"], dropna=False):
        lab = f"captive power coal, {grp}" + (f" ({s3})" if isinstance(s3, str) else "")
        blk("1", lab, {"coal": float(g.coal_in_industry_twh_model.sum()) * sc}, "C", "PROPOSED (section 1 central; low / high in the note)",
            f"GIPT 2019 captive capacity x hours x PLN t/MWh; scaled by {sc:.4f} to the coal leaving the other row after the cement spread (scratch chain)")
    split.append(dict(block="1", label="captive power coal, total (central); range low / mid / high", coal_twh=capt["central"], total_twh=capt["central"], grade="C",
                      status="PROPOSED", basis=f"low {capt['low']:.3f}, mid {capt['mid']:.3f}, high {capt['high']:.3f} TWh; its electricity (central {float(base_o.other_2019_coal_twh) and float(O[(O.option == 'b') & (O.level == 'central')].captive_electricity_added_2019_twh.iloc[0]):.3f} TWh) would move to grid electricity under option (b)",
                      oil_twh=0.0, gas_twh=0.0, biomass_twh=0.0, electricity_twh=0.0))
    # v3 explicit non-ferrous, 2019 equivalents (process part; the nickel electricity is the captive coal of block 1)
    al = {k: float(sid[sid.subsector == k].mwh_2050.sum()) / 1e6 / gf for k in ("nonferrous_alumina", "nonferrous_aluminium_primary", "nonferrous_copper")}
    alc = {k: sid[sid.subsector == k].groupby("carrier").mwh_2050.sum() / 1e6 / gf for k in al}
    blk("2", "nickel process fuel 2019 (Wei 2020 Case 3-FeNi fuel x USGS 2019 Ni content), coal", {"coal": q19 * ne["fuel_mwh_per_t_ni"] / 1e6}, "C", "INFERENCE",
        "v3 explicit nickel; its electricity (11.33 TWh in 2019) is generated by the nickel captive coal of block 1 (no second count)")
    for k, v in alc.items():
        vec = {"electricity": float(v.get("electricity", 0.0)), "gas": float(v.get("gas", 0.0)) + float(v.get("heat", 0.0))}
        blk("2", f"{k.replace('nonferrous_', '')} 2019 equivalent (v3 2050 / growth = 2019 output x PyPSA-Eur 2050 ratio)", vec, "C", "INFERENCE",
            "v3 explicit; primary aluminium ran on the Inalum Asahan hydro (own generation)" if "aluminium" in k else "v3 explicit")
    grp = {"food 10-12": ["10", "11", "12"], "textiles 13-15": ["13", "14", "15"], "wood 16": ["16"], "paper and printing 17-18": ["17", "18"],
           "rubber and plastics 22": ["22"], "non-metallic minerals without cement (23 - 2394)": ["23", "-2394"], "machinery 25-28": ["25", "26", "27", "28"],
           "transport equipment 29-30": ["29", "30"], "other manufacturing 31-33": ["31", "32", "33"]}
    for lab, cs in grp.items():
        z = K.set_index("kbli")
        sign = lambda c: (-1.0, c[1:]) if c.startswith("-") else (1.0, c)
        vec = {"coal": 0.0, "oil": 0.0, "gas": 0.0, "electricity": 0.0}
        for c in cs:
            s, cc = sign(c)
            vec["coal"] += s * float(z.at[cc, "coal_all_twh"]); vec["oil"] += s * float(z.at[cc, "oil_twh"]); vec["gas"] += s * float(z.at[cc, "gas_twh"])
            vec["electricity"] += s * float(z.at[cc, "el_grid_net_twh"])
        blk("3", f"IBS 2019 attributable: {lab}", vec, "B (quantities) / C (conversion)", "VERIFIED (lower bound: IBS coverage)",
            "BPS IBS large and medium industry; electricity = purchased - sold (self-generation is represented by its fuel); IBS has no biomass column")
    # named UNSD commodities in the biomass of the other row (the v3 cement deduction took biomass pro rata, so each keeps its share)
    u = cm.unsd()
    nes = u[u.transaction.str.strip().str.lower().isin(["consumption not elsewhere specified (industry)"])].copy()
    nes["twh"] = nes.q * nes.commodity.map(cf)
    bio_comm = {k: float(nes[nes.commodity == k].twh.sum()) for k in ("Fuelwood", "Bagasse", "Biodiesel", "Charcoal")}
    bio_raw = sum(bio_comm.values())   # = cache other biomass (185.17 TWh): fuelwood + bagasse + biodiesel + charcoal
    if abs(bio_raw - float(rec["biomass"]["other"]) / 1e6) > 1e-6:
        raise ValueError(f"biomass commodities {bio_raw} != cache other biomass")
    bsh = {k: v / bio_raw * other["biomass"] for k, v in bio_comm.items()}
    blk("3", "UNSD named commodity: bagasse -> sugar mills (KBLI 1072, food)", {"biomass": bsh["Bagasse"]}, "B", "VERIFIED (commodity) / INFERENCE (user)",
        f"UNSD 2019 bagasse n.e.s. industry 6,964.7 kt = {bio_comm['Bagasse']:.3f} TWh at the pypsa-asean factor; pro rata after the cement deduction")
    S = pd.DataFrame(split)
    used = S[S.block.isin(["2", "3"]) | ((S.block == "1") & ~S.label.str.contains("total"))]
    res = {c: other[c] - float(used[f"{c}_twh"].sum()) for c in cars}
    blk("4", "regional residual (not attributable; supervisor item 5)", res, "D", "INFERENCE",
        "other - blocks 1 (central) - 2 - 3; IBS has no biomass column")
    hk = cm.hv(H, "Kalimantan Coal", None, "Annex 03") * BOE; ha = cm.hv(H, "Average Coal", None, "Annex 03") * BOE; mf = cf["Hard coal"] * 3.6e3
    split.append(dict(block="4a", label="of the residual biomass: UNSD fuelwood 'n.e.s. industry' (65,253 thousand m3)", biomass_twh=bsh["Fuelwood"], total_twh=bsh["Fuelwood"],
                      coal_twh=0.0, oil_twh=0.0, gas_twh=0.0, electricity_twh=0.0, grade="C (conflict)", status="VERIFIED (UNSD row) / data conflict",
                      basis=f"{bio_comm['Fuelwood']:.3f} TWh before the cement deduction; HEESI 2025 5.1.1 / 5.1.2 industrial biomass 2019 = 217 kt = {twh(cm.hv(H, 'Industrial biomass', 2019, '5.1.2')):.3f} TWh"))
    split.append(dict(block="4a", label="of the residual biomass: UNSD biodiesel and charcoal n.e.s. industry", biomass_twh=bsh["Biodiesel"] + bsh["Charcoal"],
                      total_twh=bsh["Biodiesel"] + bsh["Charcoal"], coal_twh=0.0, oil_twh=0.0, gas_twh=0.0, electricity_twh=0.0, grade="B", status="VERIFIED",
                      basis="biodiesel 362 kt (B20 blend in industrial diesel), charcoal 97.2 kt"))
    split.append(dict(block="5 (memo)", label="coal heating value: residual coal at HEESI Kalimantan 4.2 BOE/t instead of 25.8 GJ/t (change)", coal_twh=res["coal"] * (hk / mf - 1),
                      total_twh=res["coal"] * (hk / mf - 1), oil_twh=0.0, gas_twh=0.0, biomass_twh=0.0, electricity_twh=0.0, grade="B", status="INFERENCE (unit basis)",
                      basis=f"{hk:.2f} vs {mf:.2f} GJ/t; at HEESI average coal 3.4554 BOE/t ({ha:.2f} GJ/t): {res['coal'] * (ha / mf - 1):.3f} TWh; not added to the blocks"))
    S = pd.DataFrame(split)
    S.to_csv(out / "ID_OTHER_BUCKET_SPLIT_PROPOSED.csv", index=False, float_format="%.6f")
    ev = dict(boe_gj=BOE, factors=f, lpg_kg_per_l=LPG_KG_PER_L, totals=tot[[c for c in K.columns if c.endswith("_twh")]].to_dict(), heesi_2019_twh=heesi,
              comparison=CMP.to_dict("records"), other_2019=other, captive_coal_leaving_other=capt, residual=res,
              shares={k: float(S[S.block == k].total_twh.sum()) for k in ("1", "2", "3", "4")})
    ev["shares"]["1"] = capt["central"]
    (out / "_bps_energy_evidence.json").write_text(json.dumps(ev, indent=1, ensure_ascii=False, default=float) + "\n", encoding="utf-8")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 80); pd.set_option("display.max_rows", 100)
    print(K[["kbli", "fuels_twh", "coal_all_twh", "gas_twh", "oil_twh", "el_purchased_twh", "el_generated_twh", "el_sold_twh", "el_end_use_twh", "total_end_use_twh"]].round(3).to_string())
    print(CMP.round(3).to_string())
    print(S[["block", "label", "coal_twh", "oil_twh", "gas_twh", "biomass_twh", "electricity_twh", "total_twh"]].round(3).to_string())


if __name__ == "__main__":
    main()
