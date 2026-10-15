"""D1 section 5 (decisions 31, 32; L12/L13): sustainable biomass supply potential 2050 by country x category.

Step 1  Replicate IRENA (2017) Table R-3/R-1a for ID, MY, PH, TH, VN: parse the residue factors and
        2010 residue tonnages from the report text (pypdf extraction of PDF pages 20-40), recompute
        the country totals (excluding the "Oil, palm fruit" and "Coconuts" rows that the report
        leaves out of its totals) and compare with Table R-1a; then redo the calculation with
        FAOSTAT 2010 production (current FAOSTAT revision, Production_Crops_Livestock_E_All_Data.zip)
        and report the error per country and crop category.
Step 2  Apply the same method to all 11 countries with FAOSTAT 2019-2023 average production, grown
        to 2050 with the IRENA (2022) rule (1.1 %/a to 2030, 0.3 %/a to 2050), harvest residues
        capped at 25 % removal (main) / 50 % (high), process residues 90 %, feed deduction from
        IRENA (2017) Table R-1c country ratios, 15 GJ/t.
Step 3  Oil palm (IRENA 2022 Box 4 mass balance: EFB 21 %, fibre 14.4 %, PKS 6.4 %, POME 58.3 % of
        FFB; trunks/fronds from Appendix A), coconut residues, wood processing residues (FAOSTAT FO
        "Wood residues", 9.14 GJ/m3), MSW organic fraction (What a Waste 3.0 2050 x food+garden share,
        IPCC 11.6 GJ/t).
Step 4  Feedstock costs (grade C, +-50 %) from public Southeast-Asian price surveys (NRI/NEDO 2024,
        ERIA/IEEJ 2024); categories without a sourced price are DATA_PENDING.
No cross-border biomass (decision 36); energy crops and natural-forest wood are excluded (IRENA 2022
sustainability principles: no land-use change, no food/feed distortion, plantation wood only).
"""
from __future__ import annotations

import io
import re
import statistics
import zipfile

import pandas as pd

from d1_common import (ASEAN, BIOMASS_DIR, FAO_NAMES, INTAKE, REG_DIR, SRC_DIR, UNIT_CONSTANTS, USD2024_TO_EUR2020,
                       Registry, read_csv, sha256, src_sha, write_csv, write_json)

SCRIPT = "scripts_project/d1_biomass.py"
BSRC = BIOMASS_DIR / "sources"
IRENA_TXT = BSRC / "IRENA2017_pdf20_40_pypdf_text.txt"
IRENA2017_PDF_SHA = "53a30811"  # prefix in SHA256SUMS.txt
IRENA2022_PDF_SHA = "bf52f40b"
QCL_ZIP = INTAKE / "raw2" / "Production_Crops_Livestock_E_All_Data.zip"
QCL_CSV = "FAOSTAT_QCL_ASEAN11_2019_2024.csv"
FO_CSV = "FAOSTAT_FO_ASEAN11_2019_2024.csv"
WAW_CSV = "WHAT_A_WASTE_3_ASEAN11_COUNTRY.csv"
NEDO_TXT = BSRC / "NEDO_NRI_2024_800028002_pdf7_8_prices_excerpt.txt"
ERIA_TXT = BSRC / "ERIA_AZEC_2024_pdf36_37_table3_8_excerpt.txt"
NEDO_PDF_SHA = "b88a3816d20ad7f14e2003cf9920203b63bcaced9b3f42317abfbab6e3d00f98"
ERIA_PDF_SHA = "2151957ca9c97f3db4f5c4424c89981bdcca1fd81c519a8995c1cba5e924e20e"
LHV_RESIDUE_GJ_T = 15.0      # IRENA 2017 p.5 / PDF 7 (moisture basis not stated)
LHV_WOOD_GJ_T = 19.0         # IRENA 2017 p.11 / PDF 13 (0 % moisture)
LHV_POME_GJ_T = 0.69         # IRENA 2022 Table 11 implied (40.8 PJ / 59.1 Mt), biogas energy
HARVEST_MAIN, HARVEST_HIGH, PROCESS = 0.25, 0.50, 0.90   # IRENA 2017 p.4-5; IRENA 2022 footnote 10 (25 % cap)
COLLECTION_2050_AGRI, COLLECTION_2050_WOODY = 0.75, 0.90  # IRENA 2022 p.43/65/86/106
GROWTH_2021_2050 = 1.011 ** 9 * 1.003 ** 20              # IRENA 2022: 1.1 %/a to 2030, 0.3 %/a 2030-2050 (base = 2019-2023 mean, centre 2021)
FEED_SHARE_2050 = {"ID": 306 / 1732, "MY": 87 / 163, "PH": 303 / 680, "TH": 226 / 1220, "VN": 426 / 861}  # IRENA 2017 Table R-1c Feed/Total
FEED_SHARE_REGIONAL = (306 + 87 + 303 + 226 + 426) / (1732 + 163 + 680 + 1220 + 861)
PALM = dict(EFB=0.21, fibre=0.144, PKS=0.064, POME=0.583)   # IRENA 2022 Box 4 (Eriza 2010), share of FFB mass
OPT_REPLANT, OPT_DENSITY, OPT_T_PER_TREE, OPF_PER_OPT = 0.04, 140.0, 2.0, 3.3  # IRENA 2022 Appendix A p.138-139 (Malaysia)
OPT_DRY_MATTER = 0.20  # IRENA 2022 Appendix A: OPT moisture content 80 %
# S2-0.2 (decision 51): MSW organic fraction -> biogas by anaerobic digestion, IPCC 2006 Vol.5 defaults, WET-weight basis
DOC_WET = {"food": (0.15, 0.08, 0.20), "garden": (0.20, 0.18, 0.22)}  # Vol.5 Ch.2 Table 2.4: DOC in % of wet waste (default, min, max)
DOCF, F_CH4, MCF_DIGESTER = 0.5, 0.5, 1.0  # Vol.5 Ch.3 §3.2.3: DOCf default 0.5; F (CH4 volume fraction) default 0.5; MCF 1 = fully anaerobic (digester)
LHV_CH4_GJ_T = 50.04  # methane LHV: NIST WebBook dHc = -890.8 kJ/mol, minus 2 x 44.0 kJ/mol H2O(l->g) = 802.8 kJ/mol / 16.043 g/mol
# S2-0.5 (decision 54): forestry residues, FAO/APFC 2001 "Trash or treasure?" (X6966E01/02.htm) and JRC98626 Table A3-3
FAO2001_SAWMILL_RECOVERY = {"KH": 0.50, "ID": 0.54, "LA": 0.40, "MY": 0.52, "MM": 0.40, "PH": 0.50, "TH": 0.50, "VN": 0.50}  # Table 12 (assumed recovery rate, %)
FAO2001_PLYWOOD_RECOVERY = {"KH": 0.47, "ID": 0.43, "LA": 0.47, "MY": 0.50, "MM": 0.47, "PH": 0.47, "TH": 0.47, "VN": 0.47}  # Table 13
FAO2001_AVG_SAWMILL, FAO2001_AVG_PLYWOOD = 0.508, 0.469  # Table 9 text: sawmills 42-60 % (avg 50.8), plywood 43-50 % (avg 46.9); used for BN, SG, TL
FAO2001_LOGGING_RESIDUE_FACTOR = {"KH": 2.0, "ID": 2.0, "LA": 2.0, "MY": 2.0, "MM": 1.5, "PH": 1.0, "TH": 1.0, "VN": 1.5}  # Table 7: m3 residue per m3 industrial roundwood
FAO2001_LOGGING_RESIDUE_FACTOR_DEFAULT = (1 - 0.55) / 0.55  # "fairly common recovery rate of about 55 percent" (BN, SG, TL not in Table 7)
JRC_LOGGING_EXTRACTION_MAX = 0.67  # JRC98626 Table A3-3 (PDF p.92): 67 % extraction on slopes <= 35 %
FAO2001_LOGGING_ECONOMIC_SHARE = 0.10  # FAO 2001 Table 7: 10 % of logging residues economically usable
R4_GROWTH_2010_2050 = {"ID": 1.011 ** 20 * 1.003 ** 20, "PH": 1.011 ** 20 * 1.003 ** 20, "VN": 1.011 ** 20 * 1.003 ** 20,
                       "MY": 1.011 ** 20 * 1.004 ** 20, "TH": 1.011 ** 20 * 1.004 ** 20}  # IRENA 2017 Table R-4
R1A = {"ID": (816, 494), "MY": (77, 44), "PH": (297, 218), "TH": (476, 429), "VN": (384, 267)}  # Table R-1a 2010 Harvest/Process PJ
S1_2050_RESIDUE_FOR_FUEL = {"ID": 1426, "MY": 76, "PH": 377, "TH": 993, "VN": 435}  # IRENA 2017 Table S-1 (25 %, after feed)
IRENA2022_COLLECTABLE_2050_PJ = {"ID": 2594.6, "TH": 978.8, "VN": 485.5, "MY": 197.0, "MM": 33.2}  # Tables 11/18/26/35/41
IRENA_COUNTRY_ORDER = ["ID", "MY", "PH", "TH", "VN"]
R3_HEADERS = {"ID": "Table R-3a Harvest and process residues in Indonesia", "MY": "Table R-3b Harvest and process residues in Malaysia",
              "PH": "Table R-3c Harvest and process residues in the Philippines", "TH": "Table R-3d Harvest and process residues in Thailand",
              "VN": "Table R-3e Harvest and process residues in Viet Nam"}
GROUPS = ["Yams & other roots", "Sweet potatoes", "Sugar cane", "Palm kernels", "Cottonseed", "Groundnut", "Stimulants", "Vegetables",
          "Treenuts", "Potatoes", "Soybeans", "Cassava", "Cotton", "Fruit", "Maize", "Pulses", "Rice", "Jute", "Wheat", "Barley",
          "Sorghum", "Millet", "Cereals", "Sesame", "Rapeseed", "Sunflower", "Oilcrops", "Oil crops", "Coconuts", "Rubber", "Tobacco", "Tea", "Coffee"]
# FAOSTAT current item name -> IRENA 2017 R-2/R-3 commodity label
FAO_TO_IRENA = {
    "Rice": "Rice, paddy", "Sugar cane": "Sugar cane", "Maize (corn)": "Maize", "Green corn (maize)": "Maize, green",
    "Cassava, fresh": "Cassava", "Oil palm fruit": "Oil, palm fruit", "Palm kernels": "Palm kernels", "Coconuts, in shell": "Coconuts",
    "Groundnuts, excluding shelled": "Groundnuts, with shell", "Soya beans": "Soybeans", "Sweet potatoes": "Sweet potatoes",
    "Bananas": "Bananas", "Pineapples": "Pineapples", "Mangoes, guavas and mangosteens": "Mangoes, mangosteens, guavas",
    "Oranges": "Oranges", "Papayas": "Papayas", "Watermelons": "Watermelons", "Potatoes": "Potatoes", "Coffee, green": "Coffee, green",
    "Tea leaves": "Tea", "Cashew nuts, in shell": "Cashew nuts, with shell", "Cabbages": "Cabbages and other brassicas",
    "Tomatoes": "Tomatoes", "Onions and shallots, dry (excluding dehydrated)": "Onions, dry", "Beans, dry": "Beans, dry",
    "Other beans, green": "Beans, green", "Cocoa beans": "Cocoa, beans", "Avocados": "Avocados",
    "Cucumbers and gherkins": "Cucumbers and gherkins", "Eggplants (aubergines)": "Eggplants (aubergines)",
    "Chillies and peppers, green (Capsicum spp. and Pimenta spp.)": "Chillies and peppers, green",
    "Chillies and peppers, dry (Capsicum spp., Pimenta spp.), raw": "Chillies and peppers, dry",
    "Other sugar crops n.e.c.": "Sugar crops not elsewhere specified", "Taro": "Taro (cocoyam)", "Yams": "Yams",
    "Sesame seed": "Sesame seed", "Sorghum": "Sorghum", "Millet": "Millet", "Wheat": "Wheat", "Barley": "Barley",
    "Seed cotton, unginned": "Seed cotton", "Cotton lint, ginned": "Cotton lint", "Cotton seed": "Cottonseed",
    "Castor oil seeds": "Castor oil seed", "Pumpkins, squash and gourds": "Pumpkins, squash and gourds", "Spinach": "Spinach",
    "Ginger, raw": "Ginger", "Lettuce and chicory": "Lettuce and chicory", "Cauliflowers and broccoli": "Cauliflowers and broccoli",
    "Carrots and turnips": "Carrots and turnips", "Asparagus": "Asparagus", "Okra": "Okra", "Strawberries": "Strawberries",
    "Grapes": "Grapes", "Lemons and limes": "Lemons and limes", "Pomelos and grapefruits": "Grapefruit (including pomelos)",
    "Tangerines, mandarins, clementines": "Tangerines, mandarins, clementines, satsumas",
    "Other tropical fruits, n.e.c.": "Fruit, tropical fresh not elsewhere specified", "Other fruits, n.e.c.": "Fruit, fresh not elsewhere specified",
    "Other vegetables, fresh n.e.c.": "Vegetables, fresh not elsewhere specified", "Other pulses n.e.c.": "Pulses not elsewhere specified",
    "Edible roots and tubers with high starch or inulin content, n.e.c., fresh": "Roots and tubers, not elsewhere specified",
    "Mushrooms and truffles": "Mushrooms and truffles", "Areca nuts": "Areca nuts", "Pepper (Piper spp.), raw": "Pepper (piper spp.)",
    "Unmanufactured tobacco": "Tobacco, unmanufactured", "Kapok fruit": "Kapok fruit", "Kapokseed in shell": "Kapokseed in shell",
    "Kapok fibre, raw": "Kapok fibre", "Coir, raw": "Coir", "Jute, raw or retted": "Jute", "Abaca, manila hemp, raw": "Manila fibre (abaca)",
    "Sisal, raw": "Sisal", "Ramie, raw or retted": "Ramie",
    "Other nuts (excluding wild edible nuts and groundnuts), in shell, n.e.c.": "Nuts not elsewhere specified",
    "Cereals n.e.c.": "Cereals not elsewhere specified", "Cow peas, dry": "Cow peas, dry", "Pigeon peas, dry": "Pigeon peas",
    "Peas, dry": "Peas, dry", "Peas, green": "Peas, green", "String beans": "String beans",
    "Leeks and other alliaceous vegetables": "Leeks, other alliaceous vegetables", "Onions and shallots, green": "Onions, shallots, green",
    "Cantaloupes and other melons": "Melons, other (Including Cantaloupes)", "Cinnamon and cinnamon-tree flowers, raw": "Cinnamon (canella)",
    "Cloves (whole stems), raw": "Cloves", "Nutmeg, mace, cardamoms, raw": "Nutmeg, mace and cardamoms", "Vanilla, raw": "Vanilla",
    "Anise, badian, coriander, cumin, caraway, fennel and juniper berries, raw": "Anise, badian, fennel, coriander",
    "Other stimulant, spice and aromatic crops, n.e.c.": "Spices not elsewhere specified", "Sunflower seed": "Sunflower seed",
    "Other oil seeds, n.e.c.": "Oilseeds not elsewhere specified", "Other berries and fruits of the genus vaccinium n.e.c.": "Berries not elsewhere specified",
    "Other citrus fruit, n.e.c.": "Fruit, citrus not elsewhere specified", "Agave fibres, raw, n.e.c.": "Agave fibres not elsewhere specified",
    "Kenaf, and other textile bast fibres, raw or retted": "Bast fibres, other", "Other fibre crops, raw, n.e.c.": "Fibre crops not elsewhere specified",
    "Canary seed": "Canary seed", "Chicory roots": "Chicory roots", "Natural rubber in primary forms": "Rubber, natural",
    "Green garlic": "Garlic", "Lentils, dry": "Lentils",
}
CATEGORY_OF = {"Rice, paddy": "rice_residues", "Sugar cane": "sugarcane_residues", "Sugar crops not elsewhere specified": "sugarcane_residues",
               "Maize": "maize_residues", "Maize, green": "maize_residues", "Cassava": "cassava_residues",
               "Coconuts": "coconut_residues", "Oil, palm fruit": "oil_palm", "Palm kernels": "oil_palm"}
NUM = r"(?:\d{1,3}(?: \d{3})*|-)"
ROW_RE = re.compile(r"(?P<text>[A-Za-z][^\n]*?)\s(?P<hf>\d+\.\d) (?P<h>" + NUM + r") (?P<pf>\d+\.\d) (?P<p>" + NUM + r")(?=\s)")


def to_num(s):
    return 0.0 if s.strip() == "-" else float(s.replace(" ", ""))


def parse_r3(text):
    """Return DataFrame(country, group, commodity, hf, h_kt, pf, p_kt) from the five R-3 tables."""
    rows = []
    bounds = [(c, text.index(R3_HEADERS[c])) for c in IRENA_COUNTRY_ORDER]
    end = text.index("Table R-4 Growth rates for crop output")
    for i, (c, start) in enumerate(bounds):
        stop = bounds[i + 1][1] if i + 1 < len(bounds) else end
        block = text[start + len(R3_HEADERS[c]):stop]
        block = re.sub(r"===== PDF PAGE \d+ =====", " ", block)
        block = re.sub(r"\(Indonesia\)|\(Malaysia\)|\(Philippines\)|\(Thailand\)|\(Viet Nam\)", " ", block)
        block = re.sub(r"Commodity\s+Group\s+Commodity\s+Harvest\s+Residue\s+Factor\s+Harvest\s+Residue\s+\(000 tonnes\)\s+Process\s+Residue\s+Factor\s+Process\s+Residue\s+\(000 tonnes\)", " ", block)
        block = re.sub(r"Source: Smeets.*?analysis", " ", block)
        block = re.sub(r"^\s*\d+\s*$", " ", block, flags=re.M)  # page numbers
        flat = re.sub(r"\s+", " ", block)
        for m in ROW_RE.finditer(flat):
            txt = m.group("text").strip()
            txt = re.sub(r"^\d+\s+", "", txt)
            group = ""
            for g in sorted(GROUPS, key=len, reverse=True):
                if txt.startswith(g + " ") and len(txt) > len(g) + 1:
                    group, txt = g, txt[len(g) + 1:].strip()
                    break
            rows.append(dict(country=c, group=group, commodity=txt, hf=float(m.group("hf")), h_kt=to_num(m.group("h")),
                             pf=float(m.group("pf")), p_kt=to_num(m.group("p"))))
    return pd.DataFrame(rows)


def parse_r2(text):
    """Rows of Table R-2 with all five country values (incomplete rows are ambiguous in the text extraction)."""
    start = text.index("Table R-2 Crop production by type and country in 2010")
    end = text.index("Table R-3 Harvest and process residues by country in 2010")
    block = text[start:end]
    block = re.sub(r"===== PDF PAGE \d+ =====|Crop \(Thousand Metric Tonnes\) Indonesia Malaysia Philippines Thailand Viet Nam|Source: FAO \(2015\)", " ", block)
    flat = re.sub(r"\s+", " ", block)
    pat = re.compile(r"(?P<name>[A-Za-z][A-Za-z,()\-/ ]*?) (?P<v>(?:(?:\d{1,3}(?: \d{3})*|-) ){4}(?:\d{1,3}(?: \d{3})*|-))(?= [A-Z])")
    out = {}
    for m in pat.finditer(flat):
        vals = [to_num(v) for v in re.findall(NUM, m.group("v"))]
        if len(vals) == 5:
            out[m.group("name").strip()] = dict(zip(IRENA_COUNTRY_ORDER, vals))
    return out


def fao_2010(zip_path):
    """FAOSTAT 2010 production (t) for the 11 countries from the raw QCL archive."""
    z = zipfile.ZipFile(zip_path)
    d = pd.read_csv(z.open("Production_Crops_Livestock_E_All_Data.csv"), encoding="latin-1",
                    usecols=["Area", "Item", "Element", "Unit", "Y2010", "Y2010F"], low_memory=False)
    d = d[d.Area.isin(FAO_NAMES) & (d.Element == "Production") & (d.Unit == "t")]
    d["country"] = d.Area.map(FAO_NAMES)
    return d


def fao_recent(csv_path):
    q = pd.read_csv(csv_path, dtype=str)
    for y in ["Y2019", "Y2020", "Y2021", "Y2022", "Y2023"]:
        q[y] = pd.to_numeric(q[y], errors="coerce")
    q["mean_2019_2023"] = q[["Y2019", "Y2020", "Y2021", "Y2022", "Y2023"]].mean(axis=1, skipna=True)
    return q


def main():
    text = IRENA_TXT.read_text(encoding="utf-8")
    r3 = parse_r3(text)
    r2 = parse_r2(text)
    irena_sha = f"IRENA_Biofuel_Potential_SE_Asia_2017.pdf:{IRENA2017_PDF_SHA}...; text:{sha256(IRENA_TXT)}"
    # ---- Step 1a: internal replication of R-1a from R-3 rows ---------------------------------------------
    rep = []
    excl = {"Oil, palm fruit", "Coconuts"}
    for c in IRENA_COUNTRY_ORDER:
        d = r3[r3.country == c]
        h_all, p_all = d.h_kt.sum() * LHV_RESIDUE_GJ_T / 1e3, d.p_kt.sum() * LHV_RESIDUE_GJ_T / 1e3
        dx = d[~d.commodity.isin(excl)]
        h, p = dx.h_kt.sum() * LHV_RESIDUE_GJ_T / 1e3, dx.p_kt.sum() * LHV_RESIDUE_GJ_T / 1e3
        rep.append(dict(country=c, rows_parsed=int(len(d)), r3_sum_all_rows_H_PJ=h_all, r3_sum_all_rows_P_PJ=p_all,
                        r3_sum_excl_palmfruit_coconut_H_PJ=h, r3_sum_excl_palmfruit_coconut_P_PJ=p,
                        r1a_doc_H_PJ=R1A[c][0], r1a_doc_P_PJ=R1A[c][1], err_H_pct=(h / R1A[c][0] - 1) * 100, err_P_pct=(p / R1A[c][1] - 1) * 100))
    rep_df = pd.DataFrame(rep)
    # factor consistency: R-3 residue vs R-2 production x factor x collection (complete R-2 rows only)
    fac = []
    for _, r in r3.iterrows():
        if r.commodity in r2:
            prod = r2[r.commodity][r.country]
            if prod > 0:
                fac.append(dict(country=r.country, commodity=r.commodity, r2_production_kt=prod, hf=r.hf, pf=r.pf,
                                h_expected=prod * r.hf * HARVEST_MAIN, h_table=r.h_kt, p_expected=prod * r.pf * PROCESS, p_table=r.p_kt,
                                h_err_pct=(r.h_kt / (prod * r.hf * HARVEST_MAIN) - 1) * 100 if r.hf else None,
                                p_err_pct=(r.p_kt / (prod * r.pf * PROCESS) - 1) * 100 if r.pf else None))
    fac_df = pd.DataFrame(fac)
    # ---- Step 1b: FAOSTAT 2010 (current revision) x IRENA factors ------------------------------------------
    f10 = fao_2010(QCL_ZIP)
    f10["irena"] = f10.Item.map(FAO_TO_IRENA)
    factors = r3.groupby("commodity").agg(hf=("hf", lambda s: statistics.mode(s)), pf=("pf", lambda s: statistics.mode(s))).to_dict("index")
    fao_rep, crop_rep = [], []
    for c in IRENA_COUNTRY_ORDER:
        d = f10[(f10.country == c) & f10.irena.notna()].copy()
        d = d[d.irena.isin(factors)]
        d["h_kt"] = d.Y2010 / 1e3 * d.irena.map(lambda k: factors[k]["hf"]) * HARVEST_MAIN
        d["p_kt"] = d.Y2010 / 1e3 * d.irena.map(lambda k: factors[k]["pf"]) * PROCESS
        dx = d[~d.irena.isin(excl)]
        h, p = dx.h_kt.sum() * LHV_RESIDUE_GJ_T / 1e3, dx.p_kt.sum() * LHV_RESIDUE_GJ_T / 1e3
        r3c = r3[r3.country == c]
        matched = set(d.irena) & set(r3c.commodity)
        fao_rep.append(dict(country=c, fao_items_mapped=int(len(d)), r3_rows=int(len(r3c)), r3_rows_matched=len(matched),
                            r3_residue_share_matched_pct=float(r3c[r3c.commodity.isin(matched)][["h_kt", "p_kt"]].sum().sum() / r3c[["h_kt", "p_kt"]].sum().sum() * 100),
                            fao2010_H_PJ_excl=h, fao2010_P_PJ_excl=p, r1a_doc_H_PJ=R1A[c][0], r1a_doc_P_PJ=R1A[c][1],
                            err_H_pct=(h / R1A[c][0] - 1) * 100, err_P_pct=(p / R1A[c][1] - 1) * 100))
        for cat in ["rice_residues", "sugarcane_residues", "maize_residues", "cassava_residues", "coconut_residues", "oil_palm"]:
            keys = [k for k, v in CATEGORY_OF.items() if v == cat]
            fv = d[d.irena.isin(keys)][["h_kt", "p_kt"]].sum().sum()
            rv = r3c[r3c.commodity.isin(keys)][["h_kt", "p_kt"]].sum().sum()
            crop_rep.append(dict(country=c, category=cat, fao2010_residue_kt=fv, irena_r3_residue_kt=rv, err_pct=(fv / rv - 1) * 100 if rv else None))
    fao_rep_df, crop_rep_df = pd.DataFrame(fao_rep), pd.DataFrame(crop_rep)
    # ---- Step 2/3: 2050 potentials for 11 countries -----------------------------------------------------------
    q = fao_recent(SRC_DIR / QCL_CSV)
    prod = q[(q.Element == "Production") & (q.Unit == "t")].copy()
    prod["irena"] = prod.Item.map(FAO_TO_IRENA)
    area = q[(q.Element == "Area harvested") & (q.Unit == "ha") & (q.Item == "Oil palm fruit")].set_index("ISO2").mean_2019_2023
    fo = pd.read_csv(SRC_DIR / FO_CSV, dtype=str)
    for y in ["Y2019", "Y2020", "Y2021", "Y2022", "Y2023"]:
        fo[y] = pd.to_numeric(fo[y], errors="coerce")
    fo["mean"] = fo[["Y2019", "Y2020", "Y2021", "Y2022", "Y2023"]].mean(axis=1, skipna=True)
    wood_res = fo[(fo.Item == "Wood residues") & (fo.Element == "Production") & (fo.Unit == "m3")].set_index("ISO2")["mean"]

    def fo_series(item):
        return fo[(fo.Item == item) & (fo.Element == "Production") & (fo.Unit == "m3")].set_index("ISO2")["mean"]
    sawn, ply, indrw = fo_series("Sawnwood"), fo_series("Plywood and LVL"), fo_series("Industrial roundwood")
    fao2001_src = "FAO/APFC 2001 Trash or treasure? Logging and mill residues in Asia and the Pacific (X6966E01/02.htm, text copies in biomass_v5/sources)"
    waw = {r["ISO2"]: r for r in read_csv(SRC_DIR / WAW_CSV)}
    qcl_sha, fo_sha, waw_sha = src_sha(QCL_CSV), src_sha(FO_CSV), src_sha(WAW_CSV)
    zip_sha = sha256(QCL_ZIP)
    costs = feedstock_costs()
    out, reg = [], Registry(SCRIPT)
    ref_src = f"IRENA 2017 (pdf {IRENA2017_PDF_SHA}...), IRENA 2022 (pdf {IRENA2022_PDF_SHA}...), FAOSTAT QCL extraction:{qcl_sha}"
    for c in ASEAN:
        feed = FEED_SHARE_2050.get(c, FEED_SHARE_REGIONAL)
        feed_tier = "B" if c in FEED_SHARE_2050 else "C"
        d = prod[(prod.ISO2 == c) & prod.irena.notna() & prod.irena.isin(factors)].copy()
        d["hf"] = d.irena.map(lambda k: factors[k]["hf"]); d["pf"] = d.irena.map(lambda k: factors[k]["pf"])
        d["cat"] = d.irena.map(CATEGORY_OF).fillna("other_crop_residues")
        d["p2050_t"] = d.mean_2019_2023.fillna(0.0) * GROWTH_2021_2050
        ffb = float(d[d.irena == "Oil, palm fruit"].p2050_t.sum())
        for cat in ["rice_residues", "sugarcane_residues", "maize_residues", "cassava_residues", "coconut_residues", "other_crop_residues"]:
            dd = d[d.cat == cat]
            if dd.empty or dd.p2050_t.sum() <= 0:
                continue
            h_main = float((dd.p2050_t * dd.hf).sum()) * HARVEST_MAIN
            h_high = float((dd.p2050_t * dd.hf).sum()) * HARVEST_HIGH
            p_main = float((dd.p2050_t * dd.pf).sum()) * PROCESS
            mass_main = (h_main + p_main) * (1 - feed)
            mass_high = (h_high + p_main) * (1 - feed)
            e = lambda m: m * LHV_RESIDUE_GJ_T / 3.6
            cst = costs.get(cat, costs["other_crop_residues"])
            out.append(row(c, cat, "solid_biomass", e(mass_main), e(mass_main) * COLLECTION_2050_AGRI, e(mass_high), mass_main, LHV_RESIDUE_GJ_T,
                           "B" if c in FEED_SHARE_2050 else "C",
                           f"FAOSTAT 2019-2023 mean production x {GROWTH_2021_2050:.4f} growth x IRENA RPR (harvest {HARVEST_MAIN}, process {PROCESS}) x (1 - feed share {feed:.3f} [{feed_tier}]) x 15 GJ/t; low = x{COLLECTION_2050_AGRI} collection (IRENA 2022 2050); high = harvest {HARVEST_HIGH}",
                           ref_src, cst, "REGISTERED", f"crops: {', '.join(sorted(set(dd.irena)))}"))
        if ffb > 0:
            for part, share in PALM.items():
                mass = ffb * share
                if part == "POME":
                    out.append(row(c, "oil_palm_pome", "biogas", mass * LHV_POME_GJ_T / 3.6, mass * LHV_POME_GJ_T / 3.6 * COLLECTION_2050_AGRI,
                                   mass * LHV_POME_GJ_T / 3.6, mass, LHV_POME_GJ_T, "C",
                                   f"FFB 2050 x {share} (IRENA 2022 Box 4) x {LHV_POME_GJ_T} GJ/t (IRENA 2022 Table 11 implied biogas energy per t POME)",
                                   ref_src, costs["oil_palm_pome"], "REGISTERED", "mill effluent; biogas feedstock"))
                else:
                    avail = mass * PROCESS
                    out.append(row(c, f"oil_palm_{part.lower()}", "solid_biomass", avail * LHV_RESIDUE_GJ_T / 3.6, avail * LHV_RESIDUE_GJ_T / 3.6 * COLLECTION_2050_AGRI,
                                   mass * LHV_RESIDUE_GJ_T / 3.6, avail, LHV_RESIDUE_GJ_T, "C",
                                   f"FFB 2050 x {share} (IRENA 2022 Box 4 mass balance) x process collection {PROCESS} x 15 GJ/t (IRENA convention; moisture basis caveat); high = 100 %",
                                   ref_src, costs[f"oil_palm_{part.lower()}"], "REGISTERED",
                                   "PKS and fibre are largely used as in-mill fuel today (competing use)" if part in ("PKS", "fibre") else ""))
            ha = float(area.get(c, 0.0)) if c in area.index else 0.0
            if ha > 0:
                opt = ha * OPT_REPLANT * OPT_DENSITY * OPT_T_PER_TREE
                opf = opt * OPF_PER_OPT
                m_main = opt * HARVEST_MAIN  # old trunks only (IRENA 2022 counts "old trunk"; fronds are pruned mulch)
                out.append(row(c, "oil_palm_trunk", "solid_biomass", m_main * LHV_RESIDUE_GJ_T / 3.6,
                               m_main * OPT_DRY_MATTER * LHV_RESIDUE_GJ_T / 3.6, (opt + opf) * HARVEST_MAIN * LHV_RESIDUE_GJ_T / 3.6, m_main, LHV_RESIDUE_GJ_T, "C",
                               f"FAOSTAT oil palm area harvested {ha:,.0f} ha x {OPT_REPLANT} replanting x {OPT_DENSITY:g} trees/ha x {OPT_T_PER_TREE:g} t OPT (IRENA 2022 Appendix A, Malaysian parameters); harvest cap {HARVEST_MAIN}; 15 GJ/t on reported mass; low = dry matter {OPT_DRY_MATTER} (80 % moisture, Appendix A); high = trunks + fronds (OPF = {OPF_PER_OPT} x OPT) at {HARVEST_MAIN}",
                               ref_src, costs["oil_palm_trunk"], "REGISTERED", f"fronds excluded from main (soil mulch); cross-check IRENA 2017 harvest factor 3.0 x FFB x 0.25 = {ffb * 3.0 * 0.25:,.0f} t incl. fronds"))
        gj_m3 = UNIT_CONSTANTS["conv_gj_per_m3_wood_residues"][0]
        s_m3 = float(sawn.get(c, 0.0)) if c in sawn.index and sawn.get(c) == sawn.get(c) else 0.0
        p_m3 = float(ply.get(c, 0.0)) if c in ply.index and ply.get(c) == ply.get(c) else 0.0
        rs = FAO2001_SAWMILL_RECOVERY.get(c, FAO2001_AVG_SAWMILL); rp = FAO2001_PLYWOOD_RECOVERY.get(c, FAO2001_AVG_PLYWOOD)
        derived_m3 = (s_m3 / rs - s_m3) + (p_m3 / rp - p_m3)
        own_use = ("mill self-consumption is not deducted here: it is part of the UNSD industry biomass demand (D1 IndustryFinalEnergy biomass), "
                   "which draws from the same national biomass bus; deducting it from supply as well would count it twice")
        wr = float(wood_res.get(c, float("nan"))) if c in wood_res.index else float("nan")
        if wr == wr and wr > 0:
            e_main = wr * COLLECTION_2050_WOODY * gj_m3 / 3.6
            out.append(row(c, "wood_processing_residues", "solid_biomass", e_main, e_main * 0.5 / COLLECTION_2050_WOODY, wr * gj_m3 / 3.6,
                           wr * COLLECTION_2050_WOODY, gj_m3, "B",
                           f"FAOSTAT FO Wood residues production 2019-2023 mean {wr:,.0f} m3 (held constant) x {COLLECTION_2050_WOODY} collection (IRENA 2022 woody 2050) x 9.14 GJ/m3 (UNSD); low = 2030 collection rate 50 % (IRENA 2022); high = 100 %",
                           f"FAOSTAT FO extraction:{fo_sha}; UNSD 2014 NCV", costs["wood_processing_residues"], "REGISTERED",
                           f"reported processing residues; FAO 2001 recovery-rate derivation gives {derived_m3:,.0f} m3 (sawnwood {s_m3:,.0f} m3 / {rs}, plywood {p_m3:,.0f} m3 / {rp}) as cross-check; " + own_use))
        elif derived_m3 > 0:
            e_main = derived_m3 * COLLECTION_2050_WOODY * gj_m3 / 3.6
            tier = "B" if c in FAO2001_SAWMILL_RECOVERY else "C"
            out.append(row(c, "wood_processing_residues", "solid_biomass", e_main, e_main * 0.5 / COLLECTION_2050_WOODY, derived_m3 * gj_m3 / 3.6,
                           derived_m3 * COLLECTION_2050_WOODY, gj_m3, tier,
                           f"S2-0.5: residues = sawnwood {s_m3:,.0f} m3 / recovery {rs} - sawnwood + plywood {p_m3:,.0f} m3 / recovery {rp} - plywood (FAO/APFC 2001 Tables 12-13{'' if c in FAO2001_SAWMILL_RECOVERY else ', 10-country averages Table 9 for ' + c}) = {derived_m3:,.0f} m3; FAOSTAT FO 2019-2023 means; x {COLLECTION_2050_WOODY} collection x 9.14 GJ/m3; low = 50 % collection; high = 100 %",
                           f"FAOSTAT FO extraction:{fo_sha}; {fao2001_src}", costs["wood_processing_residues"], "REGISTERED", own_use))
        else:
            out.append(row(c, "wood_processing_residues", "solid_biomass", None, None, None, None, gj_m3, "C",
                           "FAOSTAT FO has neither Wood residues nor sawnwood/plywood production for this country", f"FAOSTAT FO extraction:{fo_sha}", costs["wood_processing_residues"], "DATA_PENDING", ""))
        irw = float(indrw.get(c, 0.0)) if c in indrw.index and indrw.get(c) == indrw.get(c) else 0.0
        lf = FAO2001_LOGGING_RESIDUE_FACTOR.get(c, FAO2001_LOGGING_RESIDUE_FACTOR_DEFAULT)
        log_high = irw * lf * JRC_LOGGING_EXTRACTION_MAX * gj_m3 / 3.6
        log_econ = irw * lf * FAO2001_LOGGING_ECONOMIC_SHARE * gj_m3 / 3.6
        out.append(row(c, "logging_residues", "solid_biomass", 0.0, 0.0, log_high, 0.0, gj_m3, "C",
                       f"main = 0 by decision 54 (IRENA 2022 p.41/63/84/105: only plantation and processing wood; decision 32); high-biomass sensitivity = FAOSTAT industrial roundwood {irw:,.0f} m3 x FAO 2001 Table 7 residue factor {lf:.3g} x JRC98626 Table A3-3 extraction {JRC_LOGGING_EXTRACTION_MAX} x 9.14 GJ/m3 = {log_high:,.0f} MWh; FAO 2001 10 % economically usable = {log_econ:,.0f} MWh",
                       f"{fao2001_src}; JRC98626 pdf p.92 Table A3-3 (raw6, sha e6e0d90b...); FAOSTAT FO extraction:{fo_sha}", costs["wood_processing_residues"], "ZERO_BY_DECISION",
                       "not counted in the main biomass potential; sensitivity only"))
        w = waw.get(c)
        if w:
            msw = float(w["MSW generation - projected 2050 (t/y)"])
            food = w["Composition - food  (% weight MSW)"]; garden = w["Composition - garden/green/horticultural (% weight MSW)"]
            if food not in ("", "nan", "NaN"):
                has_garden = garden not in ("", "nan", "NaN")
                frac = {"food": float(food), "garden": float(garden) if has_garden else 0.0}
                mass = msw * (frac["food"] + frac["garden"])
                ch4 = lambda which: sum(msw * frac[f] * DOC_WET[f][which] * DOCF * MCF_DIGESTER * F_CH4 * 16.0 / 12.0 for f in frac)  # t CH4 (IPCC Vol.5 Eq. 3.2-3.3, MCF = 1)
                e_main, e_low, e_high = (ch4(i) * LHV_CH4_GJ_T / 3.6 for i in (0, 1, 2))
                out.append(row(c, "msw_organic_biogas", "biogas", e_main, e_low, e_high, mass, (e_main * 3.6 / mass) if mass else 0.0, "C",
                               f"S2-0.2 (decision 51): What a Waste 3.0 MSW 2050 {msw:,.0f} t x (food {frac['food']:.3f}{' + garden ' + str(round(frac['garden'], 3)) if has_garden else ', garden share not reported'}) -> anaerobic digestion CH4 = wet mass x DOC(wet; IPCC Vol.5 Table 2.4: food 0.15 [0.08-0.20], garden 0.20 [0.18-0.22]) x DOCf 0.5 x MCF 1 x F 0.5 x 16/12 (Vol.5 Ch.3 Eq. 3.2-3.3) x methane LHV {LHV_CH4_GJ_T} GJ/t; wet-weight basis; low/high = DOC range",
                               f"WaW extraction:{waw_sha}; IPCC 2006 Vol.5 Ch.2 Table 2.4 and Ch.3 §3.2.3 (sources/IPCC2006_V5_Ch2_WasteData.pdf, IPCC2006_V5_Ch3_SWDS.pdf)", costs["msw_organic_biogas"], "REGISTERED",
                               "technology-data v0.15.0 has no MSW digestion yield (biogas rows carry only costs/efficiency), so IPCC defaults are used; enters the biogas route (biogas upgrading -> gas), not the solid biomass bus; collection/treatment split not applied"))
            else:
                out.append(row(c, "msw_organic_biogas", "biogas", None, None, None, None, None, "C",
                               f"What a Waste 3.0 MSW 2050 {msw:,.0f} t but no composition data", f"WaW extraction:{waw_sha}", costs["msw_organic_biogas"], "DATA_PENDING", "composition missing"))
    # ---- outputs -----------------------------------------------------------------------------------------------
    cols = ["country", "category", "feedstock_group", "potential_main_mwh", "potential_low_mwh", "potential_high_mwh", "mass_main_t", "lhv_gj_per_t",
            "potential_tier", "potential_method", "potential_sources", "cost_eur2020_per_mwh", "cost_low_eur2020_per_mwh", "cost_high_eur2020_per_mwh",
            "cost_tier", "cost_source", "status", "notes"]
    out.sort(key=lambda r: (r["country"], r["category"]))
    write_csv(out, BIOMASS_DIR / "BIOMASS_POTENTIAL_2050.csv", cols)
    # cross-checks against IRENA
    xc = []
    for c in ASEAN:
        rows_c = [r for r in out if r["country"] == c and r["potential_main_mwh"] not in (None, "")]
        tot_pj = sum(r["potential_main_mwh"] for r in rows_c) * 3.6 / 1e6
        crop_pj = sum(r["potential_main_mwh"] for r in rows_c if r["category"] in ("rice_residues", "sugarcane_residues", "maize_residues", "cassava_residues", "other_crop_residues")) * 3.6 / 1e6
        pk = r3[(r3.country == c) & (r3.commodity == "Palm kernels")][["h_kt", "p_kt"]].sum().sum() * LHV_RESIDUE_GJ_T / 1e3 * R4_GROWTH_2010_2050.get(c, 1.0) if c in R4_GROWTH_2010_2050 else None
        s1_adj = (S1_2050_RESIDUE_FOR_FUEL[c] - pk) if c in S1_2050_RESIDUE_FOR_FUEL else None
        xc.append(dict(country=c, total_main_PJ=tot_pj, crop_residues_excl_palm_coconut_PJ=crop_pj,
                       irena2017_S1_2050_residue_for_fuel_PJ=S1_2050_RESIDUE_FOR_FUEL.get(c),
                       irena2017_palm_kernel_rows_in_S1_PJ_2050=pk,
                       ratio_to_S1=crop_pj / S1_2050_RESIDUE_FOR_FUEL[c] if c in S1_2050_RESIDUE_FOR_FUEL else None,
                       ratio_to_S1_excl_palm_kernels=(crop_pj / s1_adj) if s1_adj and s1_adj > 0 else None,
                       irena2022_collectable_2050_PJ=IRENA2022_COLLECTABLE_2050_PJ.get(c),
                       ratio_main_to_irena2022=tot_pj / IRENA2022_COLLECTABLE_2050_PJ[c] if c in IRENA2022_COLLECTABLE_2050_PJ else None))
    write_csv(xc, BIOMASS_DIR / "BIOMASS_CROSSCHECK_IRENA.csv", list(xc[0].keys()))
    write_csv(rep_df.to_dict("records"), BIOMASS_DIR / "REPLICATION_R3_VS_R1A.csv", list(rep_df.columns))
    write_csv(fao_rep_df.to_dict("records"), BIOMASS_DIR / "REPLICATION_FAOSTAT2010_VS_R1A.csv", list(fao_rep_df.columns))
    write_csv(crop_rep_df.to_dict("records"), BIOMASS_DIR / "REPLICATION_FAOSTAT2010_VS_R3_BY_CATEGORY.csv", list(crop_rep_df.columns))
    write_csv(fac_df.to_dict("records"), BIOMASS_DIR / "REPLICATION_R3_FACTOR_CONSISTENCY.csv", list(fac_df.columns))
    write_csv(r3.to_dict("records"), BIOMASS_DIR / "sources" / "IRENA2017_TABLE_R3_PARSED.csv", list(r3.columns))
    # registry rows
    for r in out:
        key = f"biomass_potential_{r['country']}_{r['category']}"
        pending = r["status"] == "DATA_PENDING"
        status = r["status"] if r["status"] in ("DATA_PENDING", "ZERO_BY_DECISION") else "REGISTERED"
        reg.add(key, f"{r['country']} {r['category']} sustainable potential 2050 ({r['feedstock_group']}); {r['potential_method'][:160]}",
                None if pending else r["potential_main_mwh"], "MWh/a", r["potential_tier"], r["potential_sources"], r["potential_method"][:200],
                qcl_sha, country=r["country"], sensitivity_low=None if pending else r["potential_low_mwh"],
                sensitivity_high=None if pending else r["potential_high_mwh"], decision_ref="31,32,36" + (",54" if r["category"] == "logging_residues" else ",51" if r["category"] == "msw_organic_biogas" else ""),
                status=status)
        cost_pending = r["cost_eur2020_per_mwh"] in (None, "")
        reg.add(key.replace("potential", "cost"), f"{r['country']} {r['category']} feedstock cost (grade C, +-50 %); {r['cost_source'][:200]}",
                None if cost_pending else r["cost_eur2020_per_mwh"], "EUR2020/MWh", "C", r["cost_source"], "see BIOMASS_POTENTIAL_2050.csv",
                qcl_sha, country=r["country"], sensitivity_low=None if cost_pending else r["cost_low_eur2020_per_mwh"],
                sensitivity_high=None if cost_pending else r["cost_high_eur2020_per_mwh"], decision_ref="L13", status="DATA_PENDING" if cost_pending else "REGISTERED")
    for pid, val, unit, desc, loc in [
        ("biomass_constraint_no_land_use_change", 1, "flag", "No land-use change for feedstock production: energy crops (yield-gap and food-waste land) excluded", "IRENA 2022 p.15-16, p.30"),
        ("biomass_constraint_harvest_residue_removal_max", HARVEST_MAIN, "fraction", "Harvest residues removable (soil quality/biodiversity)", "IRENA 2022 footnotes 10/17/21; IRENA 2017 p.4-5"),
        ("biomass_constraint_process_residue_collection", PROCESS, "fraction", "Process residue collection", "IRENA 2017 p.5"),
        ("biomass_constraint_collection_rate_2050_agri", COLLECTION_2050_AGRI, "fraction", "Collection rate 2050 agricultural residues (low layer)", "IRENA 2022 p.43/65/86"),
        ("biomass_constraint_collection_rate_2050_woody", COLLECTION_2050_WOODY, "fraction", "Collection rate 2050 woody biomass", "IRENA 2022 p.106/118"),
        ("biomass_constraint_natural_forest_excluded", 1, "flag", "Only plantation/processing wood; natural forest wood and current fuelwood not counted", "IRENA 2022 p.41, 63, 84, 105"),
        ("biomass_constraint_feed_deduction_regional", FEED_SHARE_REGIONAL, "fraction", "Feed share deducted for countries outside IRENA 2017 (five-country total)", "IRENA 2017 Table R-1c"),
        ("biomass_growth_factor_2021_2050", GROWTH_2021_2050, "ratio", "Crop output growth 1.1 %/a to 2030 then 0.3 %/a (base 2019-2023 mean)", "IRENA 2022 p.43/65/85; IRENA 2017 Table R-4"),
        ("biomass_lhv_residues", LHV_RESIDUE_GJ_T, "GJ/t", "Residue energy content (moisture basis not stated by source)", "IRENA 2017 p.5"),
        ("biomass_cross_border", 0, "flag", "No cross-border biomass trade (decision 36)", "S2 instruction decision 36"),
        ("biomass_msw_ch4_yield_food_wet", DOC_WET["food"][0] * DOCF * MCF_DIGESTER * F_CH4 * 16.0 / 12.0, "tCH4/t wet food waste", "Anaerobic-digestion CH4 yield of food waste = DOC 0.15 x DOCf 0.5 x MCF 1 x F 0.5 x 16/12 (wet basis); range from DOC 0.08-0.20", "IPCC 2006 Vol.5 Ch.2 Table 2.4; Ch.3 Eq. 3.2-3.3, §3.2.3"),
        ("biomass_msw_ch4_yield_garden_wet", DOC_WET["garden"][0] * DOCF * MCF_DIGESTER * F_CH4 * 16.0 / 12.0, "tCH4/t wet garden waste", "Anaerobic-digestion CH4 yield of garden/park waste = DOC 0.20 x 0.5 x 1 x 0.5 x 16/12 (wet basis); range from DOC 0.18-0.22", "IPCC 2006 Vol.5 Ch.2 Table 2.4; Ch.3"),
        ("biomass_methane_lhv", LHV_CH4_GJ_T, "GJ/t CH4", "Methane lower heating value derived from NIST WebBook standard enthalpy of combustion (-890.8 kJ/mol) minus water vaporisation (2 x 44.0 kJ/mol), / 16.043 g/mol", "NIST Chemistry WebBook, methane condensed-phase thermochemistry"),
        ("biomass_logging_residues_decision", 0, "flag", "Logging residues = 0 in the main potential (decision 54; IRENA 2022 counts plantation and processing wood only); FAO 2001 x JRC 67 % as high-biomass sensitivity", "IRENA 2022 p.41, 63, 84, 105; S2 supplement 0.5"),
        ("biomass_logging_extraction_rate_sensitivity", JRC_LOGGING_EXTRACTION_MAX, "fraction", "Maximum logging-residue extraction rate on slopes <= 35 % (JRC98626 Table A3-3, current/medium/high scenarios)", "JRC98626 PDF p.92 Table A3-3"),
        ("biomass_wood_residue_own_use_treatment", 1, "flag", "Mill self-consumption of processing residues is not deducted from supply: it is already a demand (UNSD industry biomass in D1) served from the same national biomass bus", "S2 supplement 0.5; UNSD 2019 has only TH Fuelwood - Consumption by wood and wood products (33.1 thousand m3)"),
    ]:
        tier = "C" if "msw_ch4" in pid or "extraction_rate" in pid else ("A" if "constraint" in pid or "lhv" in pid or "decision" in pid or "own_use" in pid else "B")
        lo = hi = None
        if pid.endswith("removal_max"):
            lo, hi = 0.5, HARVEST_HIGH
        elif pid == "biomass_msw_ch4_yield_food_wet":
            lo, hi = (DOC_WET["food"][1] * DOCF * F_CH4 * 16 / 12, DOC_WET["food"][2] * DOCF * F_CH4 * 16 / 12)
        elif pid == "biomass_msw_ch4_yield_garden_wet":
            lo, hi = (DOC_WET["garden"][1] * DOCF * F_CH4 * 16 / 12, DOC_WET["garden"][2] * DOCF * F_CH4 * 16 / 12)
        elif pid == "biomass_logging_extraction_rate_sensitivity":
            lo, hi = FAO2001_LOGGING_ECONOMIC_SHARE, JRC_LOGGING_EXTRACTION_MAX
        src_name = "IRENA 2017/2022 (extraction BIOMASS_EXTRACTION.md)" if "msw" not in pid and "logging" not in pid and "own_use" not in pid else ("IPCC 2006 Vol.5; NIST WebBook" if "msw" in pid or "methane" in pid else "S2 supplement 01; FAO/APFC 2001; JRC98626; IRENA 2022")
        reg.add(pid, desc, val, unit, tier, src_name, loc, src_sha("BIOMASS_EXTRACTION.md"), decision_ref="31,32,36,51,54", sensitivity_low=lo, sensitivity_high=hi)
    for _, r in rep_df.iterrows():
        reg.add(f"biomass_replication_r3_vs_r1a_{r.country}", f"IRENA 2017 replication: R-3 rows summed (excl. oil palm fruit, coconuts) vs Table R-1a; "
                f"H err {r.err_H_pct:+.2f} %, P err {r.err_P_pct:+.2f} %", r.err_H_pct, "% error (harvest)", "B", "IRENA 2017 Tables R-1a, R-3", "PDF 22, 27-36",
                irena_sha, country=r.country, sensitivity_low=r.err_P_pct, decision_ref="31", status="REFERENCE_ONLY")
    for _, r in fao_rep_df.iterrows():
        reg.add(f"biomass_replication_faostat2010_vs_r1a_{r.country}", f"FAOSTAT 2010 (current revision) x IRENA factors vs Table R-1a: H err {r.err_H_pct:+.1f} %, "
                f"P err {r.err_P_pct:+.1f} %; {r.r3_rows_matched}/{r.r3_rows} R-3 rows matched ({r.r3_residue_share_matched_pct:.1f} % of residue mass)", r.err_H_pct,
                "% error (harvest)", "B", "FAOSTAT QCL all-data zip; IRENA 2017", f"zip:{zip_sha}", irena_sha, country=r.country, sensitivity_low=r.err_P_pct,
                decision_ref="31", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "biomass.csv")
    write_json(dict(script=SCRIPT, irena_text_sha256=sha256(IRENA_TXT), faostat_zip_sha256=zip_sha, qcl_csv_sha256=qcl_sha, fo_csv_sha256=fo_sha,
                    waw_sha256=waw_sha, growth_2021_2050=GROWTH_2021_2050, feed_share_regional=FEED_SHARE_REGIONAL, r2_complete_rows=len(r2),
                    r3_rows=int(len(r3)), replication_r3_vs_r1a=rep_df.to_dict("records"), replication_faostat2010=fao_rep_df.to_dict("records"),
                    crosscheck=xc, costs=costs), REG_DIR / "fragments" / "biomass.json")
    print(rep_df.round(2).to_string(index=False))
    print(fao_rep_df.round(2).to_string(index=False))
    print(crop_rep_df.round(1).to_string(index=False))
    print("factor consistency rows", len(fac_df), "max |h err| %", fac_df.h_err_pct.abs().max() if len(fac_df) else None, "max |p err| %", fac_df.p_err_pct.abs().max() if len(fac_df) else None)
    print(pd.DataFrame(xc).round(1).to_string(index=False))


def row(c, cat, grp, main, low, high, mass, lhv, tier, method, sources, cost, status, notes):
    return dict(country=c, category=cat, feedstock_group=grp, potential_main_mwh=main, potential_low_mwh=low, potential_high_mwh=high,
                mass_main_t=mass, lhv_gj_per_t=lhv, potential_tier=tier, potential_method=method, potential_sources=sources,
                cost_eur2020_per_mwh=cost["eur"] if cost else None, cost_low_eur2020_per_mwh=cost["eur"] * 0.5 if cost and cost["eur"] is not None else None,
                cost_high_eur2020_per_mwh=cost["eur"] * 1.5 if cost and cost["eur"] is not None else None, cost_tier="C",
                cost_source=cost["source"] if cost else "", status=status, notes=notes)


def feedstock_costs():
    """Grade C feedstock costs from public Southeast-Asian price surveys (USD2024 or IDR 2024 per tonne -> EUR2020/MWh)."""
    fx = USD2024_TO_EUR2020
    idr = 15565.0  # IDR per USD, 7 Nov 2024 (NEDO/NRI deck p.6); ERIA/IEEJ prices are 2024 Indonesian values
    mwh_t = LHV_RESIDUE_GJ_T / 3.6
    nedo = f"NRI/NEDO 2024 'Promising Biomass Materials' purchasing prices incl. transport (pdf p.6-8, interviews Nov 2024; sha {NEDO_PDF_SHA[:8]})"
    eria = f"ERIA/IEEJ 2024 AZEC bioenergy supply chain Table 3.8 (Indonesia, Rp/kg; sha {ERIA_PDF_SHA[:8]})"

    def per_mwh(usd_t, lhv_gj_t):
        return usd_t / (lhv_gj_t / 3.6) * fx

    bagasse = statistics.mean([31.0, 32.0])            # ID 31; TH 29-35 (NEDO)
    husk = statistics.mean([290e3 / idr, 237e3 / idr])  # ID rice husk Rp290/kg (ERIA T3.8); straw collection to roadside Rp237/kg (Pen Consulting 2021 in ERIA)
    cob = statistics.mean([63.0, 53.0])                 # ID 63, TH 53 (NEDO)
    pks = statistics.mean([74.0, 63.5, (825e3 + 960e3) / 2 / idr])  # TH 74, MY 59-68, ID Rp825-960/kg
    efb = statistics.mean([11.0, 3.5, (45e3 + 68e3) / 2 / idr])     # TH 11, MY 3-4, ID Rp45-68/kg
    sawdust = (350e3 + 600e3) / 2 / idr                # ID Rp350-600/kg, NCV ~2,450 kcal/kg (ERIA T3.8)
    agri_proxy = statistics.mean([bagasse, husk, cob])
    return {
        "sugarcane_residues": dict(usd_t=bagasse, eur=per_mwh(bagasse, LHV_RESIDUE_GJ_T), source=f"bagasse {bagasse:.0f} USD/t ({nedo}); 15 GJ/t"),
        "rice_residues": dict(usd_t=husk, eur=per_mwh(husk, LHV_RESIDUE_GJ_T), source=f"rice husk Rp290/kg and straw roadside collection Rp237/kg -> {husk:.1f} USD/t ({eria}); 15 GJ/t"),
        "maize_residues": dict(usd_t=cob, eur=per_mwh(cob, LHV_RESIDUE_GJ_T), source=f"maize cob {cob:.0f} USD/t ({nedo}); 15 GJ/t"),
        "cassava_residues": dict(usd_t=agri_proxy, eur=per_mwh(agri_proxy, LHV_RESIDUE_GJ_T), source=f"proxy: mean of bagasse, rice husk, maize cob prices {agri_proxy:.1f} USD/t (no sourced cassava stalk price)"),
        "coconut_residues": dict(usd_t=agri_proxy, eur=per_mwh(agri_proxy, LHV_RESIDUE_GJ_T), source=f"proxy: mean of bagasse, rice husk, maize cob prices {agri_proxy:.1f} USD/t (no sourced coconut husk/shell price)"),
        "other_crop_residues": dict(usd_t=agri_proxy, eur=per_mwh(agri_proxy, LHV_RESIDUE_GJ_T), source=f"proxy: mean of bagasse, rice husk, maize cob prices {agri_proxy:.1f} USD/t"),
        "oil_palm_pks": dict(usd_t=pks, eur=per_mwh(pks, 3500 * 4.1868 / 1e3), source=f"PKS {pks:.1f} USD/t (TH 74, MY 59-68 NEDO; ID Rp825-960/kg ERIA); NCV 3,500 kcal/kg (ERIA T3.8)"),
        "oil_palm_efb": dict(usd_t=efb, eur=per_mwh(efb, LHV_RESIDUE_GJ_T), source=f"EFB {efb:.1f} USD/t (TH 11, MY 3-4 NEDO; ID Rp45-68/kg ERIA); 15 GJ/t"),
        "oil_palm_fibre": dict(usd_t=efb, eur=per_mwh(efb, LHV_RESIDUE_GJ_T), source=f"proxy = EFB price {efb:.1f} USD/t (mesocarp fibre has no market price; in-mill fuel)"),
        "oil_palm_pome": dict(usd_t=0.0, eur=0.0, source="mill effluent, no feedstock price (capture cost sits in the biogas plant CAPEX; IRENA 2022 Box 8)"),
        "oil_palm_trunk": None,
        "wood_processing_residues": dict(usd_t=sawdust, eur=per_mwh(sawdust, 2450 * 4.1868 / 1e3), source=f"sawdust Rp350-600/kg -> {sawdust:.1f} USD/t at NCV 2,450 kcal/kg ({eria}); wood chips 50-250 USD/t (NEDO) as upper context"),
        "msw_organic_biogas": dict(usd_t=0.0, eur=0.0, source="negative or zero gate fee (tipping fee 17 USD/t, Cilacap RDF, IRENA 2022 Table 49); set to 0; digester CAPEX sits in the biogas plant"),
    }


if __name__ == "__main__":
    main()
