"""I2 section 2: unified recompute of the eleven countries in one scratch copy of the data chain (i2_engine.Engine), same rules for every country.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i2_chain.py [--quick]

Cumulative steps (instruction section 2.2; every step records T_v2, 'other', carriers, sub-sectors, anchors, sector totals for all countries):
  S0  v3 (repository, byte-identical gate)
  S1  base replacement: UNSD SDMX 2019 (S5p: SDMX factors, ID hard coal 20.29, ID coke 28.20), industry cache rebuilt from the same SDMX rows,
      anchors IId (country TFEC = AEO8, sector split = own seed x v3 RAS sector factors; I1 'fixedcol')                   [decision 210 items 1, 3]
  S2  anchor boundary alignment: (a) self-produced residues out of the seed and the cache in every country; where the national balance contains
      them (default: as UNSD) the anchor falls by residue x the industry multiplier; ID (HEESI: industrial biomass 0.9 TWh) -> not in the balance;
      (b) ID industrial biomass outside the national balance (fuelwood at the 2010-2017 mean, charcoal) leaves the seed and is added back to the
      ATS industry row at the industry multiplier (reading I, outside the anchor)                                           [210 item 4]
  S3  (ii) corrections, IId: ID household motor gasoline -> road; rail parent row out of the D1 table (W12 F2 option b)       [210 items 3, 6; 209 F2]
  S4  (i) corrections, reading I: captive coal option (b) - ID central (10,589 kt at 20.29), MM low (66 kt at 23.26), PH paper (b) + refinery (b')
  S5  structural (conservation): a steel (spatial only), b cement (ii) / BN (iii), c nickel 2023 base Wei Case 3, d pulp and paper (one rule),
      e HVC 2019 plants (5.191 / 4.627), f methanol (EU27 share dropped; MY / ID / BN explicit energy use), g new plants (ID LINE, MY PIC and
      Sarawak Petchem, VN Long Son, TH Cracker No 5, LA paper line)                                                         [204, 206, 208, 210 items 5, 7]
  S6  country items: a MY ammonia fuel duplicate (mid), b glass (VN TH PH SG), alumina (VN), copper (MM LA), lime (MY), c VN hybrid split with
      T_v2 and decomposition from the same run                                                                              [208]
  S7  network layer at demand / potential level: F7 biomass cap 99 %, F3 / F4 adjusted solid-biomass potential (s3_0 overflow only; T_v2 uses the
      biomass before overflow); F1 / F2 / F6 quantities are reported by i2_tables.py                                         [209]
Additivity: every step's increment applied alone on S1 (S1 alone on S0); sum of singles vs the combined result. Sensitivities on the final state.
Results: /home/jin/v4i2/results/*.json (one per case) and tables/I2_RUNS_INDEX.csv; tables are written by i2_tables.py.
"""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i2_common as cm   # noqa: E402
import i2_engine as E    # noqa: E402
import i2_items as IT    # noqa: E402
import os as _w8os   # noqa: E402
W08_ANCHOR_MODE = _w8os.environ.get('W08_ANCHOR_MODE', 'ras')   # W08 copy: ras = v4 main (decision 211 item 1), fixedcol = IId
W08_ID_PAPER_FW = _w8os.environ.get('W08_ID_PAPER_FW', 'residue')   # W08 copy: residue = decision 211 item 2 (main), purchased = I2 main

OUT = cm.SCRATCH / "results"
KEY = ["country", "sector", "carrier", "account"]
IND_BIO = lambda cc: (cc, "Industry", "biomass", "IndustryFinalEnergy")   # noqa: E731


def d1_series(p: Path) -> pd.Series:
    return pd.read_csv(p).groupby(KEY).base_2019_mwh.sum()


class Inputs:
    def __init__(self):
        self.S0 = d1_series(cm.SCRATCH / "d1_base_S0.csv"); self.B = d1_series(cm.SCRATCH / "d1_base_S5p.csv")
        self.cells = IT.sdmx_industry_cells(); self.res = IT.residues(self.cells)
        self.S = IT.load_sessions()
        c, r = self.cells, self.res
        # ---- (a) residues by country -----------------------------------------------------------------------------------------------------
        ra = r[r.cls == "a"]
        self.a_tot = ra.groupby("country").mwh.sum().to_dict()
        self.a_drop = {(x.country, x.code, x.tx) for x in ra.itertuples()}
        # ---- ID (b): industrial fuelwood is outside the national balance (HEESI industrial biomass 0.9 TWh ~ the SDMX charcoal 0.80 TWh;
        #      biodiesel 3.70 TWh is in HEESI) -> only fuelwood (2010-2017 mean, decision 206) leaves the seed and grows at the v3 multiplier
        idb = c[(c.country == "ID") & (c.tx != "121") & (c.carrier == "biomass") & (c.code == IT.FW_CODE)]
        fw = idb
        self.fw_factor = float(fw.factor.astype(float).iloc[0])                 # SDMX GJ per m3
        self.fw_sdmx_km3 = float(fw.quantity.sum()); self.fw_sdmx_mwh = float(fw.mwh.sum())
        self.fw_mean_mwh = IT.ID_FW_MEAN_KM3 * self.fw_factor * 1000.0 / 3.6
        self.fw_scale = self.fw_mean_mwh / self.fw_sdmx_mwh
        self.idb_sdmx = float(idb.mwh.sum()); self.idb_main = self.idb_sdmx - self.fw_sdmx_mwh + self.fw_mean_mwh
        # checks: D1 S5p industry biomass = SDMX industry 121 biomass (ID), residues within the D1 row
        d1_id = float(self.B.get(IND_BIO("ID"), 0.0)); c121 = float(c[(c.country == "ID") & (c.tx == "121") & (c.carrier == "biomass")].mwh.sum())
        self.check_id_bio = dict(d1_S5p=d1_id, sdmx_121=c121, residues_a=self.a_tot.get("ID", 0.0), outside_balance_sdmx=self.idb_sdmx)
        if abs(d1_id - c121) > 1.0:
            raise SystemExit(f"STOP: ID D1 industry biomass {d1_id} != SDMX 121 biomass {c121}")
        # ---- caches ----------------------------------------------------------------------------------------------------------------------
        self.cache_full = IT.build_cache(c)
        self.cache_a = IT.build_cache(c, drop=self.a_drop, scale={("ID", IT.FW_CODE): self.fw_scale})
        # W08 copy (decision 211 item 2): the ID fuelwood of the SDMX paper row 1214G as a self-produced residue (a); share of the non-paper rows
        fwc = c[(c.country == "ID") & (c.code == IT.FW_CODE) & (c.tx != "121")]
        self.paper_fw_sdmx_mwh = float(fwc[fwc.tx == "1214G"].mwh.sum()); self.paper_fw_sdmx_km3 = float(fwc[fwc.tx == "1214G"].quantity.sum())
        self.sh_nes = float(fwc[fwc.tx != "1214G"].mwh.sum()) / float(fwc.mwh.sum())
        self.cache_a_paper = IT.build_cache(c, drop=set(self.a_drop) | {("ID", IT.FW_CODE, "1214G")}, scale={("ID", IT.FW_CODE): self.fw_scale})
        # ---- (ii): household gasoline, rail parent -----------------------------------------------------------------------------------------
        P = pd.read_csv(cm.SCRATCH / "i1code/BASE2019_SDMX/BASE2019_SDMX_COMMODITY_BY_STEP.csv")
        hg = P[(P.account == "ResidentialFuel") & (P.commodity == "motor gasoline")].set_index("country").S5
        self.gas = {cc: float(hg.get(cc, 0.0)) for cc in ("ID", "MM")}
        # ---- items -------------------------------------------------------------------------------------------------------------------------
        S = self.S
        self.captive = {"ID": [("ID", "other", "coal", S["id_captive"]["central"]["C_kt"] * 20.29 / 3.6 * 1e3), ("ID", "other", "electricity", -S["id_captive"]["central"]["E_mwh"])],
                        "MM": [("MM", IT.NMM, "coal", S["g4_ci"]["captive_MM"]["low"]["C_kt"] * 23.26 / 3.6 * 1e3), ("MM", "other", "electricity", -S["g4_ci"]["captive_MM"]["low"]["E_mwh"])],
                        "PH": []}
        for it in S["g3_cap"]["PH"]["levels"]["central"]:
            C = it["coal_kt"] * 22.058 / 3.6 * 1e3
            self.captive["PH"].append(("PH", it["row"], "coal", C))
            if it["electricity_added"]:
                self.captive["PH"].append(("PH", it["row"], "electricity", -it["E_gwh"] * 1e3))
        self.pp_tab = IT.pp_tables()
        self.pp = {cc: IT.pp_item(cc, t, "existing") for cc, t in self.pp_tab.items()}
        self.pp_new = {cc: IT.pp_item(cc, t, "new") for cc, t in self.pp_tab.items()}
        self.pp = {k: v for k, v in self.pp.items() if v}; self.pp_new = {k: v for k, v in self.pp_new.items() if v}
        self.hvc = IT.hvc_items(S, "i2"); self.hvc_s2 = IT.hvc_items(S, "s2")
        self.meoh = IT.methanol_items(S); self.oth = IT.other_items(S)
        an = pd.read_csv(cm.DEMAND / "DEMAND_ANCHOR_AEO8_ATS.csv").set_index("country")
        self.m_v3 = {cc: float(an.at[cc, "industry_multiplier"]) for cc in cm.ASEAN}
        # ---- sensitivity inputs (session deliverables) ---------------------------------------------------------------------------------
        hc = c[(c.country == "ID") & (c.tx == "121") & (c.carrier == "coal") & (c.commodity.str.lower() == "hard coal")]
        self.id_hard_coal_kt = float(hc.quantity.sum())
        self.id_ncv_delta = self.id_hard_coal_kt * 1000.0 * (0.007167 * 3600.0 - 20.29) / 3.6     # v3 25.8012 vs decision 207 20.29 GJ/t, MWh 2019
        det = json.loads((cm.G["G0"] / "evidence/_chain_detail.json").read_text())["details"]["by_product|207"]
        last = det["8"]   # G0 main path final step (NPI Case 4-NPI, ferronickel / matte Case 3)
        self.ni_case4 = {k: float(v) for k, v in last["explicit_carriers"]["nonferrous_nickel"].items()}
        import v3_industry as v3   # noqa: E402
        ne = v3.nickel_unit_energy()
        self.niupper_scale = (v3.NI_UPPER_MWH_PER_T_NPI / v3.NI_NPI_NI_FRACTION) / (ne["electricity_mwh_per_t_ni"] + ne["fuel_mwh_per_t_ni"])
        B = {x["key"]: x["value"] for x in json.loads((cm.S2D / "s2/_biomass_evidence.json").read_text())["numbers"]}
        self.fw_m2021_km3 = float(B["3.series.industry_mean_2020_2021_km3"])
        g1 = {x["key"]: x["value"] for x in json.loads((cm.G["G1"] / "tables/_chain_evidence.json").read_text())["numbers"]}
        self.sabah_resid = float(g1["chain.sabah.industry_gas_minus_chem_central_2019"]) * 1e6
        g3 = {x["key"]: x["value"] for x in json.loads((cm.G["G3"] / "tables/_chain_evidence.json").read_text())["numbers"]}
        conv = json.loads((cm.SRC / "FROZEN_UPSTREAM_CONVERSIONS.json").read_text())["constants"]["fuels_conv_toTWh"]
        self.sg_refgas_kt = float(g3["chain.SG.refinery_gas_2019_kt.excess_over_supply"]); self.sg_refgas_mwh = self.sg_refgas_kt * conv["Refinery gas"] * 1e6

    def fw_sdmx_km3_cc(self, cc: str) -> float:
        z = self.cells[(self.cells.country == cc) & (self.cells.tx != "121") & (self.cells.code == IT.FW_CODE)]
        return float(z.quantity.sum())

    def fw_mwh_cc(self, cc: str) -> float:
        z = self.cells[(self.cells.country == cc) & (self.cells.tx != "121") & (self.cells.code == IT.FW_CODE)]
        return float(z.mwh.sum())


def hvc_item(h: dict, scale_u: float = 1.0) -> dict:
    return dict(name="hvc", row=h["row"], fuel_split=h["fuel_split"], fuel19=h["hvc19_t"] * h["fuel19_per_t"] * scale_u, el19=h["hvc19_t"] * h["el19_per_t"] * scale_u,
                v2050=IT.vec(h["vec"], h["hvc50_base_t"] * scale_u))


def vn_hybrid(cache: dict, el_rows: dict, bag_mwh: float = 0.0) -> dict:
    """G2 v4w07g2_unsd.hybrid (copied rule) on the I2 cache: UNSD explicit rows kept; the UNSD n.e.s. amount of each carrier spread over the APEC
    2022 rows that UNSD does not report for that carrier; electricity rows of iron and steel / chemicals back-cast from UNSD 2020 (G2). Bagasse
    is no longer in the cache (decision 210 item 4 a), so the G2 'bagasse to food' step is empty. Returns {carrier: {sub: MWh}}."""
    U = pd.DataFrame({r["carrier"]: {k: float(r[k]) for k in r if k not in ("country", "carrier")} for r in cache["records"] if r["country"] == "VN"})
    A = pd.read_csv(cm.IND_V3 / "APEC2022_VN_INDUSTRY_PJ.csv").set_index("cache_subsector")
    A = A[[E.APEC_COL[c] for c in cm.CARS19]].rename(columns={v: k for k, v in E.APEC_COL.items()}).reindex(U.index).fillna(0.0).astype(float)
    H = pd.DataFrame(0.0, index=U.index, columns=list(cm.CARS19))
    for c in cm.CARS19:
        explicit = [s for s in U.index if s != "other" and U.at[s, c] > 0]
        for s in explicit:
            H.at[s, c] = U.at[s, c]
        nes = U.at["other", c]
        if c == "biomass" and bag_mwh:   # G2 rule on the export base (bagasse to food and tobacco); empty on the I2 base
            H.at["food and tobacco", c] = bag_mwh; nes -= bag_mwh
            explicit = explicit + ["food and tobacco"]
        if c == "electricity":
            for s_, x in el_rows.items():
                H.at[s_, c] += x; nes -= x
            explicit = explicit + list(el_rows)
        w = A[c].copy(); w[explicit] = 0.0
        if w.sum() > 0:
            H[c] += nes * w / w.sum()
        else:
            H.at["other", c] += nes
    return {c: H[c].to_dict() for c in cm.CARS19}


def set_vn_cache(cache: dict, H: dict) -> dict:
    c2 = copy.deepcopy(cache)
    for r in c2["records"]:
        if r["country"] == "VN":
            for s in r:
                if s not in ("country", "carrier"):
                    r[s] = repr(float(H[r["carrier"]].get(s, 0.0)))
    return c2


# ============================================================================================================== step deltas
def build_steps(I: Inputs, eng: E.Engine):
    nf23 = eng.nf["nf2023"]["ID"]["nonferrous_nickel"]

    def d1_with(case, edits):
        d = case["d1"].copy()
        for k, v in edits.items():
            d[k] = d.get(k, 0.0) + v
        return d

    def s1(c):
        c = dict(c); c.update(d1=I.B.copy(), d1_s0=I.S0, anchor_mode=W08_ANCHOR_MODE, cache=I.cache_full); return c

    def s2(c):
        c = dict(c)
        ed = {IND_BIO(cc): -v for cc, v in I.a_tot.items()}
        ed[IND_BIO("ID")] = ed.get(IND_BIO("ID"), 0.0) - I.idb_sdmx
        c["d1"] = d1_with(c, ed)
        c["anchor_adj"] = {cc: v for cc, v in I.a_tot.items() if cc != "ID"}
        if W08_ID_PAPER_FW == "residue":   # W08 copy: decision 211 item 2 (= I2 sensitivity id_paper_fw_selfuse)
            c["ats_add"] = list(c.get("ats_add", [])) + [("ID", "biomass", I.idb_main * I.sh_nes, I.m_v3["ID"])]
            c["cache"] = I.cache_a_paper
        else:
            c["ats_add"] = list(c.get("ats_add", [])) + [("ID", "biomass", I.idb_main, I.m_v3["ID"])]   # 210 item 4 b: reading I = v3 ATS industry multiplier
            c["cache"] = I.cache_a
        return c

    def s3(c):
        c = dict(c)
        ed = {("ID", "Residential", "oil", "ResidentialFuel"): -I.gas["ID"], ("ID", "Transport", "oil", "RoadResidualFuel"): I.gas["ID"]}
        d = d1_with(c, ed)
        for k in [k for k in d.index if k[3] == "TransportEmbeddedFuelParent"]:
            d[k] = 0.0
        c["d1"] = d
        return c

    def s4(c):
        c = dict(c); c["moves"] = list(c.get("moves", [])) + I.captive["ID"] + I.captive["MM"] + I.captive["PH"]; return c

    def s5a(c):
        return dict(c)

    def s5b(c):
        c = dict(c); c.update(cem=dict(IT.CEMENT_USGS_2019_T), edgar_zero=["BN"], bn_iii=True); return c

    def s5c(c):
        c = dict(c); nf = copy.deepcopy(c.get("nf", {})); nf.setdefault("ID", {})["nonferrous_nickel"] = dict(nf23); c["nf"] = nf; return c

    def add_prod(c, cc, item):
        p = copy.deepcopy(c.get("products", {})); p.setdefault(cc, []).append(item); c["products"] = p

    def add_extra(c, cc, key, v):
        x = copy.deepcopy(c.get("extra", {})); x.setdefault(cc, {})[key] = v; c["extra"] = x

    def s5d(c):
        c = dict(c)
        for cc, it in I.pp.items():
            add_prod(c, cc, dict(it))
        return c

    def s5e(c):
        c = dict(c)
        for cc, h in I.hvc.items():
            if h["hvc19_t"] > 0 or h["hvc50_base_t"] > 0:
                add_prod(c, cc, hvc_item(h))
        return c

    def s5f(c):
        c = dict(c); c["meoh_drop"] = list(IT.METHANOL_DROP)
        for cc in ("MY", "ID", "BN"):
            add_prod(c, cc, {k: v for k, v in I.meoh[cc].items() if k != "src"})
        return c

    def s5g(c):
        c = dict(c)
        for cc, h in I.hvc.items():
            if h["hvc50_new_t"] > 0:
                add_extra(c, cc, "hvc_new_plants", IT.vec(h["vec"], h["hvc50_new_t"]))
        add_extra(c, "MY", "methanol_new_plants", I.meoh["MY_new"]["v2050"])
        for cc, it in I.pp_new.items():
            add_extra(c, cc, "pulp_paper_new_lines", it["v2050"])
        return c

    def s6a(c):
        c = dict(c); c["moves"] = list(c.get("moves", [])) + I.oth["my_ammonia_dup"]; return c

    def s6b(c):
        c = dict(c)
        for grp in ("glass", "alumina", "copper", "lime"):
            for cc, it in I.oth[grp].items():
                add_prod(c, cc, dict(it))
        return c

    def s6c(c):
        c = dict(c)
        H = vn_hybrid(c["cache"], I.S["vn_el_rows"])
        c["cache"] = set_vn_cache(c["cache"], H); c["vn_same_run"] = True
        return c

    def s7(c):
        c = dict(c); c["bio_cap_share"] = 0.99
        p = cm.SCRATCH / "BIOMASS_POTENTIAL_2050_I2.csv"
        if p.exists():
            c["biopot"] = p.read_bytes()
        return c

    return [("S1", "基年替换（SDMX，IId）", s1), ("S2", "锚边界对齐（残渣移出；ID 平衡表外生物质按口径 I）", s2), ("S3", "(ii) 类：ID 家庭汽油移道路、铁路父行移出（IId）", s3),
            ("S4", "(i) 类：自备电厂 (b)（口径 I）", s4), ("S5a", "钢（只换空间）", s5a), ("S5b", "水泥 (ii) / BN (iii)", s5b), ("S5c", "镍 2023 基年（Case 3）", s5c),
            ("S5d", "纸浆造纸（统一规则）", s5d), ("S5e", "HVC（2019 在运装置，5.191 / 4.627）", s5e), ("S5f", "甲醇（去欧盟份额；MY / ID / BN 显式）", s5f),
            ("S5g", "新装置（LINE、PIC、Sarawak 甲醇、龙山、No 5、LA 纸线）", s5g), ("S6a", "MY 合成氨燃料重复（中档）", s6a),
            ("S6b", "玻璃、氧化铝、铜、石灰", s6b), ("S6c", "VN 混合拆分、同一次运行", s6c), ("S7", "网络层：生物质上限 99 %、潜力调整（只影响溢出）", s7)]


# ============================================================================================================== sensitivities
def sensitivities(I: Inputs, eng: E.Engine, cases: dict, steps: list):
    """(name, label, case) on the final state; each changes one rule. Quantities from the session deliverables where a session defined the variant."""
    F = cases[steps[-1][0]]
    out = []

    def mod(**kw):
        c = dict(F); c.update(kw); return c

    out.append(("anchor_IIa", "锚构造 IIa（RAS 重解，守 C.3；残渣锚扣减不适用）", mod(anchor_mode="ras", anchor_adj=None)))
    out.append(("anchor_IIb", "锚构造 IIb（冻结 v3 各国 × 部门锚）", mod(anchor_mode="frozen", anchor_adj=None)))
    out.append(("reading_I", "全部口径 I（v3 倍数不变，新基年 × v3 倍数）", mod(anchor_mode="I", anchor_adj=None)))
    out.append(("balance_excl", "平衡表覆盖：各国平衡表都不含自用残渣（锚不扣减）", mod(anchor_adj={})))
    adj = dict(F.get("anchor_adj") or {}); adj["ID"] = adj.get("ID", 0.0) + I.id_ncv_delta
    out.append(("id_ncv_i", "ID 热值修正按 (i)（倍数不变；25.80 → 20.29）", mod(anchor_adj=adj)))
    # HVC S2 basis
    pr = copy.deepcopy(F["products"]); ex = copy.deepcopy(F["extra"])
    for cc, h in I.hvc_s2.items():
        if cc in pr:
            pr[cc] = [hvc_item(h) if it["name"] == "hvc" else it for it in pr[cc]]
        if h["hvc50_new_t"] > 0:
            ex[cc]["hvc_new_plants"] = IT.vec(h["vec"], h["hvc50_new_t"])
    out.append(("hvc_s2", "HVC 用 S2 口径（2019 3.269、2050 6.103）", mod(products=pr, extra=ex)))
    for u, nm in ((0.75, "u075"), (0.95, "u095")):
        pr = copy.deepcopy(F["products"]); ex = copy.deepcopy(F["extra"])
        for cc, h in I.hvc.items():
            if cc in pr:
                pr[cc] = [hvc_item(h, u / 0.85) if it["name"] == "hvc" else it for it in pr[cc]]
            if h["hvc50_new_t"] > 0:
                ex[cc]["hvc_new_plants"] = IT.vec(h["vec"], h["hvc50_new_t"] * u / 0.85)
        out.append((f"eth_{nm}", f"乙烯利用率 {u}", mod(products=pr, extra=ex)))
    nf = copy.deepcopy(F["nf"]); nf["ID"]["nonferrous_nickel"] = I.ni_case4
    out.append(("ni_case4", "NPI 用 Wei Case 4（G0 主线）", mod(nf=nf)))
    nf = copy.deepcopy(F["nf"]); nf["ID"]["nonferrous_nickel"] = {k: v * I.niupper_scale for k, v in F["nf"]["ID"]["nonferrous_nickel"].items()}
    out.append(("ni_upper", "镍 NIUPPER（Case 3 × 3.571）", mod(nf=nf)))
    for nm, lab, km3 in (("fw2021", "ID 燃料木材 2020–2021 年均", I.fw_m2021_km3), ("fwsdmx", "ID 燃料木材 SDMX 2019（不改）", I.fw_sdmx_km3)):
        e = km3 * I.fw_factor * 1000.0 / 3.6; add = I.idb_sdmx - I.fw_sdmx_mwh + e
        aa = [(a[0], a[1], (add if (a[0] == "ID" and a[1] == "biomass") else a[2])) + tuple(a[3:]) for a in F["ats_add"]]
        cc_ = IT.build_cache(I.cells, drop=I.a_drop, scale={("ID", IT.FW_CODE): e / I.fw_sdmx_mwh})
        if F.get("vn_same_run"):
            cc_ = set_vn_cache(cc_, vn_hybrid(cc_, I.S["vn_el_rows"]))
        out.append((nm, lab, mod(ats_add=aa, cache=cc_)))
    for cc, nm, ratio, lab in (("VN", "vnfw_export", 14725.0 / I.fw_sdmx_km3_cc("VN"), "VN 燃料木材用导出版本（14,725 千 m³，G2 主算）"),):
        dmw = I.fw_mwh_cc(cc) * (ratio - 1.0)
        d1 = F["d1"].copy(); d1[IND_BIO(cc)] = d1.get(IND_BIO(cc), 0.0) + dmw
        cc_ = IT.build_cache(I.cells, drop=I.a_drop, scale={("ID", IT.FW_CODE): I.fw_scale, (cc, IT.FW_CODE): ratio})
        if F.get("vn_same_run"):
            cc_ = set_vn_cache(cc_, vn_hybrid(cc_, I.S["vn_el_rows"]))
        out.append((nm, lab, mod(d1=d1, cache=cc_)))
    # ID fuelwood booked in the SDMX paper row (1214G) read as self-produced bark / wood waste of pulp mills (210 item 4 a) instead of (b)
    fwc = I.cells[(I.cells.country == "ID") & (I.cells.code == IT.FW_CODE) & (I.cells.tx != "121")]
    sh_nes = float(fwc[fwc.tx != "1214G"].mwh.sum()) / float(fwc.mwh.sum())
    aa = [(a[0], a[1], (a[2] * sh_nes if (a[0] == "ID" and a[1] == "biomass") else a[2])) + tuple(a[3:]) for a in F["ats_add"]]
    cc_ = IT.build_cache(I.cells, drop=set(I.a_drop) | {("ID", IT.FW_CODE, "1214G")}, scale={("ID", IT.FW_CODE): I.fw_scale})
    if F.get("vn_same_run"):
        cc_ = set_vn_cache(cc_, vn_hybrid(cc_, I.S["vn_el_rows"]))
    out.append(("id_paper_fw_selfuse", f"ID 造纸行燃料木材（SDMX 1214G，占 ID 工业燃料木材 {1 - sh_nes:.0%}）视为纸浆厂自产树皮 / 木材废料（(a) 移出）", mod(ats_add=aa, cache=cc_)))
    out.append(("my_sabah_neu", "MY 沙巴解释不了的工业用气 16.94 TWh 转 NEU（口径 I）", mod(moves=list(F["moves"]) + [("MY", "other", "gas", I.sabah_resid)])))
    out.append(("sg_refgas", "SG 化工行炼厂气超出供应 783 kt 移出（口径 I）", mod(moves=list(F["moves"]) + [("SG", IT.CHEM, "oil", I.sg_refgas_mwh)])))
    for lv in ("low", "mid", "high"):
        c = I.S["id_captive"][lv]
        mv = [m for m in F["moves"] if not (m[0] == "ID" and m[1] == "other" and m[2] in ("coal", "electricity") and m in I.captive["ID"])]
        mv += [("ID", "other", "coal", c["C_kt"] * 20.29 / 3.6 * 1e3), ("ID", "other", "electricity", -c["E_mwh"])]
        out.append((f"id_captive_{lv}", f"ID 自备煤 {lv} 档", mod(moves=mv)))
    pr = copy.deepcopy(F["products"])
    has_row = {cc for cc in cm.ASEAN if sum(float(r[IT.PAPER]) for r in I.cache_a["records"] if r["country"] == cc) > 0}
    for cc in pr:
        pr[cc] = [dict(it, spill=False) if (it["name"] == "pulp_paper" and cc in has_row) else it for it in pr[cc]]
    out.append(("pp_cap", "纸浆造纸 2019 扣除以造纸行为上限（G3 规则；只对有 UNSD 造纸行的国家）", mod(products=pr)))
    aa = [tuple(a[:3]) for a in F["ats_add"]]
    out.append(("b_items_current_mult", "ID 平衡表外生物质按当期 IId 工业倍数增长（而非 v3 倍数）", mod(ats_add=aa)))
    pr = copy.deepcopy(F["products"])
    for cc in pr:
        pr[cc] = [dict(it, v2050=dict(it["v2050"], biomass=0.0)) if it["name"] == "pulp_paper" else it for it in pr[cc]]
    out.append(("pp_literal", "纸浆造纸 2050 生物质全部单列（字面闭环）", mod(products=pr)))
    ex = copy.deepcopy(F["extra"])
    for cc in ex:
        for k in [k for k in ex[cc] if k.endswith("_new_plants") or k.endswith("_new_lines")]:
            del ex[cc][k]
    out.append(("no_new_plants", "新装置全部只作 R4 敏感性（不进主算）", mod(extra=ex)))
    pr = copy.deepcopy(F["products"]); pr["BN"] = [it for it in pr.get("BN", []) if it["name"] != "methanol"]
    out.append(("bn_meoh_out", "BN 甲醇不计入（第 202 项第 4 条）", mod(products=pr)))
    out.append(("meoh_keep", "保留欧盟权重甲醇负荷（不去份额）", mod(meoh_drop=[])))
    d1 = F["d1"].copy()
    d1[("MM", "Residential", "oil", "ResidentialFuel")] = d1.get(("MM", "Residential", "oil", "ResidentialFuel"), 0.0) - I.gas["MM"]
    d1[("MM", "Transport", "oil", "RoadResidualFuel")] = d1.get(("MM", "Transport", "oil", "RoadResidualFuel"), 0.0) + I.gas["MM"]
    out.append(("mm_gasoline", "MM 家庭汽油也移到道路", mod(d1=d1)))
    out.append(("no_f7", "生物质上限不留余量（F7 关）", mod(bio_cap_share=1.0)))
    out.append(("pot_v3", "生物质潜力不调整（F3 / F4 关）", {k: v for k, v in F.items() if k != "biopot"}))
    # residue classification variants (rebuild seed, anchor adjustment and cache)
    for nm, lab, keep in (("res_nes_purchased", "n.e.s. 行的 5150 视为外购 (c)（MM 9.42 TWh 等）", lambda r: not (r.code == "5150" and r.tx == "1214O")),
                          ("res_bagasse_kept", "蔗渣留在 T_v2（第 208 项第 1 条旧读法）", lambda r: r.code != "5120")):
        ra = I.res[(I.res.cls == "a")]; ra = ra[ra.apply(keep, axis=1)]
        a_tot = ra.groupby("country").mwh.sum().to_dict(); a_drop = {(x.country, x.code, x.tx) for x in ra.itertuples()}
        d1 = F["d1"].copy()
        for cc in cm.ASEAN:
            d1[IND_BIO(cc)] = d1.get(IND_BIO(cc), 0.0) + I.a_tot.get(cc, 0.0) - a_tot.get(cc, 0.0)
        cc_ = IT.build_cache(I.cells, drop=a_drop, scale={("ID", IT.FW_CODE): I.fw_scale})
        if F.get("vn_same_run"):
            cc_ = set_vn_cache(cc_, vn_hybrid(cc_, I.S["vn_el_rows"]))
        aadj = {cc: v for cc, v in a_tot.items() if cc != "ID"}
        if nm == "res_bagasse_kept":   # ID bagasse back in the seed: ID balance (HEESI) has no bagasse -> outside the anchor like the other ID biomass
            idb = float(I.res[(I.res.country == "ID") & (I.res.code == "5120")].mwh.sum())
            d1[IND_BIO("ID")] -= idb
            aa = [(a[0], a[1], (a[2] + idb if (a[0] == "ID" and a[1] == "biomass") else a[2])) + tuple(a[3:]) for a in F["ats_add"]]
            out.append((nm, lab, mod(d1=d1, cache=cc_, anchor_adj=aadj, ats_add=aa)))
        else:
            out.append((nm, lab, mod(d1=d1, cache=cc_, anchor_adj=aadj)))
    return out


# ============================================================================================================== serialisation
def pack(res: dict, label: str, extra: dict | None = None) -> dict:
    out = dict(label=label, countries={}, ats_sectors=res["ats_sectors"], dlog=res["dlog"], vn_dlog=res.get("vn_dlog", []), **(extra or {}))
    for cc, s in res["snap"].items():
        L = s["L"]
        out["countries"][cc] = dict(T=s["T"], other=s["other"], share=s["share"], T_car=L["T_car"], other_car=L["other"], scale=L["scale"],
                                    by_sub=L["by_sub"], parts={k: dict(v) for k, v in L["parts"].items()}, meoh_dropped=L["meoh_dropped"],
                                    **{k: s[k] for k in ("ind19", "ind19_true", "ind50_ats", "ind19_car", "prod50", "other19", "other19_car", "ind_anchor", "ind_mult", "tfec_anchor",
                                                         "overflow", "overflow_agriculture", "bio_before", "agriculture_biomass", "overflow_s30", "bio_before_s30", "pot", "gaps",
                                                         "s30_not_found")})
    out["ats_add_info"] = res.get("ats_add_info", [])
    pz = res["pz"]; pz = pz[pz.carrier == "all (see mapping shares)"]
    out["pz_dispersed"] = [dict(country=r.country, unsd_row=r.subsector, pypsa_eur_sector=str(r.method).split(" via ")[-1], mwh_2019=float(r.mwh_2019), mwh_2050=float(r.mwh_2050))
                           for r in pz.itertuples()]
    return out


def save(obj: dict, name: str):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.json").write_text(json.dumps(obj, default=float))


def main():
    quick = "--quick" in sys.argv
    t0 = time.time()
    if OUT.exists():   # results of earlier runs (e.g. a sensitivity that no longer exists) must not reach the tables
        for f in OUT.glob("*.json"):
            f.unlink()
    eng = E.Engine(); gate = eng.reproduce()
    I = Inputs()
    steps = build_steps(I, eng)
    index = [dict(name="gate", label="unmodified copy vs repository", ok=all(gate["m08b_s30_byte_identical"].values()) and all(gate["s30_byte_identical"].values()))]
    meta = dict(gate=gate, inputs=dict(check_id_bio=I.check_id_bio, a_tot=I.a_tot, fw=dict(factor_gj_m3=I.fw_factor, sdmx_km3=I.fw_sdmx_km3, sdmx_mwh=I.fw_sdmx_mwh,
                mean_km3=IT.ID_FW_MEAN_KM3, mean_mwh=I.fw_mean_mwh), id_outside_balance=dict(sdmx=I.idb_sdmx, main=I.idb_main), gasoline=I.gas,
                pp={k: {kk: vv for kk, vv in v.items() if kk != "v2050"} for k, v in I.pp.items()}, pp_new={k: {kk: vv for kk, vv in v.items() if kk != "v2050"} for k, v in I.pp_new.items()},
                hvc={k: {kk: vv for kk, vv in v.items() if kk != "vec"} for k, v in I.hvc.items()}, captive=I.captive,
                residues=I.res.to_dict("records")))
    save(meta, "meta")
    # ---- v3 ------------------------------------------------------------------------------------------------------------------------------
    r = eng.run({}); save(pack(r, "S0 v3"), "step_S0"); index.append(dict(name="step_S0", label="v3", seconds=time.time() - t0))
    # ---- cumulative ---------------------------------------------------------------------------------------------------------------------
    case = {}; cases = {"S0": {}}
    for code, label, f in steps:
        case = f(case); cases[code] = case
        r = eng.run(case); save(pack(r, f"{code} {label}"), f"step_{code}")
        index.append(dict(name=f"step_{code}", label=label, seconds=time.time() - t0))
        print(code, label, round(time.time() - t0, 1), "s", round(sum(v["T"] for v in r["snap"].values()) / 1e6, 2), flush=True)
    if quick:
        cm.write_csv(index, cm.TABLES / "I2_RUNS_INDEX.csv"); return
    # ---- singles on S1 (additivity) -----------------------------------------------------------------------------------------------------
    base1 = cases["S1"]
    for code, label, f in steps[1:]:
        c = f(dict(base1))
        if code in ("S5e", "S5g"):   # HVC new plants need nothing else; S5e alone
            pass
        r = eng.run(c); save(pack(r, f"single {code} {label}"), f"single_{code}")
        index.append(dict(name=f"single_{code}", label=label, seconds=time.time() - t0))
    print("singles done", round(time.time() - t0, 1), flush=True)
    # ---- sensitivities on the final state ----------------------------------------------------------------------------------------------
    for name, label, c in sensitivities(I, eng, cases, steps):
        try:
            r = eng.run(c); save(pack(r, f"sens {label}"), f"sens_{name}")
            index.append(dict(name=f"sens_{name}", label=label, seconds=time.time() - t0))
        except Exception as exc:   # recorded, not hidden
            index.append(dict(name=f"sens_{name}", label=label, error=str(exc)[:300]))
            print("SENS FAILED", name, exc, flush=True)
    print("sensitivities done", round(time.time() - t0, 1), flush=True)
    cm.write_csv(index, cm.TABLES / "I2_RUNS_INDEX.csv")
    (cm.SCRATCH / "final_case_keys.json").write_text(json.dumps(sorted(case.keys())))
    print("runs: m08b", eng.n_m08b, "s3_0", eng.n_s30, "seconds", round(time.time() - t0, 1))


if __name__ == "__main__":
    main()
