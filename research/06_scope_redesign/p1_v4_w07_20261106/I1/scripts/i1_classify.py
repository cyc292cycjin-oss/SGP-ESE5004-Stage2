"""I1-2d: classification of the confirmed corrections (decisions 204-209) into decision 208 item 7 classes and the ID industry deviation from
the AEO8 anchor under the growth readings.

    PYTHONHASHSEED=0 /home/jin/miniforge3/envs/pypsa-earth/bin/python scripts/i1_classify.py

Classes (decision 208 item 7): (i) the same error is in the national statistics AEO8 used (AMS Energy Balance Tables, AEO8 PDF p.54 / printed
p.52); (ii) only in our UNSD extraction or in the model chain; (iii) a UNSD estimate that the national statistics do not have; 'structural' =
not a 2019 base error but a 2050 rule (physical output, explicit product, boundary) that does not move the RAS seed; 'n/a' = supply side.
Readings: I = ATS multiplier unchanged; II = AEO8 anchor absolute unchanged; for II the anchor construction variant is named (IIa RAS re-solved,
IIb frozen country x sector anchors, IId fixed v3 RAS column factors = country TFEC from AEO8, own-seed sector split, no cross-country transfer).
ID deviation: G0 main path step values (G0/ID_OTHER_SHARE_STEPS.csv, NCV 207, reading I) + the scratch-chain case G0seedII (NCV and fuelwood
seed changes) under IIa / IIb / IId (tables/I1_CHAIN_RESULTS.csv).
Writes CORRECTION_CLASSIFICATION.csv, tables/I1_2_ID_AEO8_DEVIATION.csv, evidence/I1_2_classify.json.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import i1_common as cm  # noqa: E402

G0 = cm.W07 / "G0" / "ID_OTHER_SHARE_STEPS.csv"
ANCHOR_V3 = 2027.967299      # ID RAS industry anchor 2050 (TWh), repository
M_V3 = 2.618610501046449     # ID industry multiplier, repository

C = [  # id, decision, correction, countries, national_stats_same_error, evidence, class, reading, variant, effect_ref, status, grade
    ("C01", "204-1/2", "captive-power coal moved out of industry, generation booked as industrial electricity (option b)", "ID (central), MM (low), PH (b/b')",
     "yes: HEESI 2025 t.5.1.1 ID industry coal 2019 39,860 kt = UNSD industry hard coal 39,770 kt (captive included); 2022 86,587 kt",
     "HEESI 2025 p.44 (text p060); UNSD SDMX 0100/121; AEO8 p.52 (EBT is the primary source)", "(i)", "I", "-", "G0 -90.45 T_v2; ID industry FE -105.98 (I)", "VERIFIED (ID), INFERENCE (MM, PH)", "B"),
    ("C02", "207 / 208-2", "coal NCV: v3 frozen dictionary (hard 25.80, brown 14.0 GJ/t) replaced by UNSD country values (ID 20.29 by decision 207)",
     "ID, VN, MM, PH, KH, TH, MY, LA", "no for the dictionary default (one value for all countries, only in our extraction); ID: national 2019 basis 24.67 (4.2 BOE/t), 2022 basis 20.29 (3.4554 BOE/t) - which one AEO8 used for its 2022 base is not printed",
     "HEESI 2025 t.5.1.2 (2019 167,412 kBOE / 39,860 kt = 4.200 BOE/t; 2022 299,191 / 86,587 = 3.4554); SDMX CONVERSION_FACTOR (ID consumption 26.1)", "(ii)", "II", "IId",
     "G0 -140.89 T_v2 under I; tables/I1_CHAIN_RESULTS.csv G0seedII", "VERIFIED factors, INFERENCE class for ID", "B"),
    ("C03", "206-1", "ID industrial fuelwood: UNSD 2019 n.e.s. row (export 166.1 TWh) to the 2010-2017 mean (74.95 TWh); SDMX current 54.4 TWh",
     "ID (MM, KH, VN similar estimates)", "no: HEESI 2025 industrial biomass 2019 = 217 kt (0.9 TWh); UNSD row is an Estimate (footnote / SDMX OBS_STATUS E)",
     "HEESI 2025 t.5.1.1/5.1.2; SDMX 5110/121 E; S2 section 3", "(iii)", "II", "IId", "G0 -214.18 T_v2 under I; SDMX vintage -111.6 TWh (2019)", "VERIFIED (ID)", "B"),
    ("C04", "206-1 / 208", "household fuelwood vintage (UNdata export vs SDMX current)", "ID (-49.6 TWh 2019), VN, MM, TH",
     "ID: HEESI household traditional biomass 2019 23,108 kBOE = 37.7 TWh vs SDMX 35.7 and export 85.4 TWh", "HEESI 2025 t.5.2.2; BASE2019_DIFF.csv", "(ii)", "II", "IId",
     "BASE2019_DIFF data_version rows", "VERIFIED (ID)", "B"),
    ("C05", "W12 F5 / 208", "VN diesel restored (UNdata export truncated at 100,000 rows)", "VN (115.7 TWh 2019: road 58.9, industry 36.0, agriculture 16.0, commerce 4.2, rail 0.6)",
     "no: the cut is in our download; UNSD and the national balance carry VN diesel", "EXPORT_TRUNCATION_SCAN.csv; SDMX 4670", "(ii)", "II", "IId",
     "VN T_v2: I +86.0, IIa -36.4 (others +71.9), IIb +20.3, IId -54.9", "VERIFIED", "A"),
    ("C06", "W12 F5 / 208-1", "commodities absent from the export: other vegetal residues 5150, other oil products n.e.c., other kerosene, municipal waste",
     "ID, TH, VN, MM, PH, MY, SG", "no for the download gap; 5150 industry is mostly closed-loop residue (decision 208 item 1)", "BASE2019_DIFF.csv missing_commodity",
     "(ii) (5150 industry: boundary)", "II", "IId", "S2 step: +205.0 TWh 2019 energy use (industry +138.7, of which 5150 ID 46.3, TH 33.6, MM 9.4, PH 5.1)", "VERIFIED", "A"),
    ("C07", "208 (base version)", "all other SDMX data-version revisions (same commodity / flow, revised value)", "11 countries",
     "UNSD current database = UNSD's own revision; national balances are the questionnaire source", "BASE2019_DIFF.csv data_version", "(ii)", "II", "IId",
     "S3 step -172.1 TWh 2019 energy use", "VERIFIED", "A"),
    ("C08", "W12 F6 / I1 section 4", "ID household motor gasoline 16,011.6 kt (196.9 TWh) moved to road", "ID (MM 479 kt as sensitivity)",
     "no: HEESI 2025 books all gasoline in transport (35.33 M kL), household table has no gasoline column", "ID_GASOLINE_CHECK.csv", "(ii)", "II", "IId",
     "IId: ID land fuel +434.3, EV +131.2, residential fuel -166.0, T_v2 -175.4 TWh (2050)", "VERIFIED (ID), INFERENCE (MM)", "B"),
    ("C09", "W12 F2", "rail parent account removed from the D1 table (option b)", "ID, KH, MM, TH, PH",
     "no: model-chain duplication (reconstruct_base_accounts.py keeps parent + child)", "W12 section 3", "(ii)", "II", "IId (W12 measured IIa)", "W12 IIa: EV net -0.84 TWh_el", "VERIFIED", "A"),
    ("C10", "206-3 / 208-1", "sugar-mill bagasse moved out of T_v2 (closed loop)", "TH (-93.71), PH (-10.30); ID, MM, LA as sensitivity",
     "probably yes (EPPO / DEDE count bagasse in industrial renewable energy) - TH national balance not on this machine", "G3 section 0 item 5", "(i) (INFERENCE)", "I", "-",
     "G3 under I", "INFERENCE", "C"),
    ("C11", "206-3 / 208-1", "pulp & paper closed loop (black liquor equivalent listed separately)", "ID, TH, VN, MY, PH, MM, LA", "structural (2050 explicit product, purchased energy only)",
     "G0 4.1, G3, G2", "structural", "I = II", "-", "G0 -8.49 T_v2", "PROPOSED", "C"),
    ("C12", "204 / G0", "nickel 2023 base year and unit energy (Case 3 / Case 4)", "ID", "structural (physical output rule)", "G0 section 3", "structural", "I = II", "-",
     "T_v2 0 (conservation); 'other' -112.68 / -171.58", "PROPOSED", "C"),
    ("C13", "204-3 / G0-G4", "cement correction (ii): grinding electricity on USGS cement; BN (iii) grinding only", "ID, VN, MY, TH, PH, MM, KH, LA, BN",
     "structural (EDGAR clinker = USGS cement x 0.786, not independent)", "G2 item 8, G4 item 5", "structural", "I = II", "-", "ID +3.97, VN +6.92, ...", "PROPOSED", "C"),
    ("C14", "203 / 208-6", "ethylene / HVC explicit (incl. LINE, PIC as R4), 2050 vector", "ID, MY, TH, SG, PH (VN R4)", "structural; see HVC_VECTOR_CHECK.csv",
     "I1 section 3", "structural", "I = II", "-", "(a)->(b): ID -6.42, MY -9.59, TH -15.32, SG -16.31, PH -2.46 TWh", "PROPOSED", "C"),
    ("C15", "G1", "MY ammonia SMR fuel left in 'other' while the ammonia product load exists", "MY", "no: model-chain double count", "G1 item 5", "(ii) model chain / structural", "I = II", "-",
     "MY -7.96 T_v2", "PROPOSED", "C"),
    ("C16", "G1", "MY Sabah unexplained industrial gas 16.94 TWh to NEU (sensitivity)", "MY", "if NEU: same in NEB (the data are NEB's) -> (i)", "G1 item 6", "(i) if confirmed", "I", "-",
     "MY -21.05 T_v2 (sensitivity)", "INFERENCE", "C"),
    ("C17", "G3", "SG refinery gas in the chemicals row above supply (783 kt, cracker off-gas)", "SG", "probably also in EMA statistics (UNSD questionnaire)", "G3 item 7", "(i) (INFERENCE)", "I", "-",
     "SG -8.16 T_v2 (sensitivity)", "INFERENCE", "C"),
    ("C18", "G2", "VN hybrid split of the industry n.e.s. row", "VN", "structural (split only)", "G2 item 3", "structural", "I = II", "-", "T_v2 unchanged by construction", "PROPOSED", "C"),
    ("C19", "s3_0 / I1 3", "EU27-weight methanol share of UNSD chemicals rows", "ID, TH, VN, SG, PH, MM, BN", "no: model chain (EU structure)", "tables/I1_3_METHANOL_LOAD_CHECK.csv",
     "(ii) model chain / structural", "I = II", "-", "ASEAN 3.76 TWh methanol carrier 2050", "VERIFIED", "A"),
    ("C20", "W12 F1", "gas production cap on marketed instead of gross production", "ID, MY, TL, VN, BN, TH, MM", "supply side", "W12 section 2", "n/a", "n/a", "-", "caps -298 TWh", "PROPOSED", "B"),
    ("C21", "W12 F3 / F4", "bagasse NCV on the supply side; closed-loop residues netted from the biomass potential", "TH, ID, MY, PH, MM, VN", "supply side", "W12 sections 4, 6",
     "n/a", "n/a", "-", "potential -26 to -55 (bagasse), up to -238 TWh (ID residues)", "PROPOSED", "B"),
]
COLS = ["id", "decision", "correction", "countries", "national_statistics_have_same_error", "evidence", "class", "recommended_reading", "anchor_variant_for_II",
        "quantified_effect", "status", "grade"]


def deviation(ev: cm.Evidence) -> pd.DataFrame:
    g = pd.read_csv(G0)
    m = g[(g.path == "main") & (g.ncv_scheme.astype(str) == "207")].reset_index(drop=True)
    by = {r.step_label: r for r in m.itertuples()}
    i19 = list(m.industry_2019_twh)
    base_v3 = i19[0]
    d_ncv = i19[1] - i19[0]; d_capt = i19[2] - i19[1]; d_pulp = i19[7] - i19[6]; d_eth = i19[8] - i19[7]; d_fw = i19[9] - i19[8]
    prod_pulp = float(m.products_2050_twh[7]); prod_eth = float(m.products_2050_twh[8] - m.products_2050_twh[7])
    R = pd.read_csv(cm.TABLES / "I1_CHAIN_RESULTS.csv")
    rows = []
    # reading I for everything (G0)
    dev_I = float(m.anchor_dev_twh.iloc[-1])
    rows.append(dict(variant="all corrections reading I (G0 main, NCV 207)", industry_fe_2050_twh=ANCHOR_V3 + dev_I, deviation_twh=dev_I, deviation_pct=dev_I / ANCHOR_V3 * 100,
                     note="G0 ID_OTHER_SHARE_STEPS.csv last main row"))
    for mode in ("IIb", "IId", "IIa"):
        r = R[(R["mode"] == mode) & (R.case == "G0seedII") & (R.country == "ID")].iloc[0]
        A, mlt = float(r.industry_anchor_twh), float(r.industry_multiplier)
        capt = d_capt * mlt; pulp = d_pulp * mlt + prod_pulp; eth = d_eth * mlt + prod_eth
        dev = (A - ANCHOR_V3) + capt + pulp + eth
        rows.append(dict(variant=f"recommended classes: captive (i) reading I at the reading-II multiplier; NCV (ii) + fuelwood (iii) reading II {mode}; pulp, ethylene structural",
                         industry_fe_2050_twh=ANCHOR_V3 + dev, deviation_twh=dev, deviation_pct=dev / ANCHOR_V3 * 100,
                         note=f"anchor {A:.2f} (v3 {ANCHOR_V3:.2f}), multiplier {mlt:.4f}; anchor move {A - ANCHOR_V3:.2f}, captive {capt:.2f}, pulp {pulp:.2f}, ethylene {eth:.2f}"))
        # alternative: NCV treated as (i) (AEO8 base carries the same over-high NCV), fuelwood (iii) II
    for mode in ("IIb", "IId"):
        # NCV reading I at the fuelwood-only multiplier is not run; first-order: NCV seed change x reading-II multiplier
        r = R[(R["mode"] == mode) & (R.case == "G0seedII") & (R.country == "ID")].iloc[0]
        mlt = float(r.industry_multiplier)
        rows.append(dict(variant=f"sensitivity: NCV also class (i) (reading I), fuelwood (iii) {mode} - first order",
                         industry_fe_2050_twh=None, deviation_twh=float(rows[1 if mode == "IIb" else 2]["deviation_twh"]) + d_ncv * mlt,
                         deviation_pct=(float(rows[1 if mode == "IIb" else 2]["deviation_twh"]) + d_ncv * mlt) / ANCHOR_V3 * 100,
                         note=f"adds NCV seed change {d_ncv:.2f} x {mlt:.4f} (first order; INFERENCE)"))
    T = pd.DataFrame(rows)
    cm.write_csv(T.to_dict("records"), cm.TABLES / "I1_2_ID_AEO8_DEVIATION.csv")
    ev.add("g0.seed_changes_2019_twh", dict(ncv=d_ncv, captive=d_capt, pulp=d_pulp, ethylene=d_eth, fuelwood=d_fw, base_v3=base_v3), "TWh (2019)", "EXACT", "C",
           "G0/ID_OTHER_SHARE_STEPS.csv main 207 industry_2019_twh", "")
    for r in T.itertuples():
        ev.add("id_deviation." + r.variant[:60].replace(" ", "_"), dict(deviation_twh=r.deviation_twh, deviation_pct=r.deviation_pct), "TWh (2050)",
               "EXACT" if "first order" not in r.variant else "INFERENCE", "C", "tables/I1_2_ID_AEO8_DEVIATION.csv", r.note)
    return T


def main():
    ev = cm.Evidence("I1_2_classify")
    rows = [dict(zip(COLS, c)) for c in C]
    cm.write_csv(rows, cm.I1 / "CORRECTION_CLASSIFICATION.csv", COLS)
    for r in rows:
        ev.add(f"class.{r['id']}", dict(cls=r["class"], reading=r["recommended_reading"], variant=r["anchor_variant_for_II"]), "class", "PROPOSED", r["grade"], r["evidence"], r["correction"][:120])
    T = deviation(ev)
    p = ev.write()
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 160)
    print(T.round(2).to_string())
    print("evidence", p, len(ev.rows))


if __name__ == "__main__":
    main()
