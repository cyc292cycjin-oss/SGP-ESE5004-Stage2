"""V4 W11 section 1 (and the reference matrix of section 2): conversion-factor inventory, constants of the research chain, call chain,
upstream handling issues, download list, country reference matrix.

    python scripts/v4ncv_inventory.py --work <work dir>

Every file:line reference is checked against the worktree (the line, or one of the next 3 lines, must contain the stated text); a row whose
check fails is written with verified=False and printed (nothing is taken on trust from the search notes).
Outputs in ncv/: NCV_COEFF_INVENTORY.csv, NCV_OTHER_CONSTANTS.csv, NCV_CALL_CHAIN.csv, NCV_UPSTREAM_HANDLING_ISSUES.csv, NCV_DOWNLOAD_LIST.csv,
NCV_COUNTRY_REFERENCE_MATRIX.csv, _inventory_evidence.json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v4ncv_common as cm   # noqa: E402
import v4ncv_unsd_implied as ui   # noqa: E402


def check(rel: str, line: int, text: str, root: Path) -> bool:
    p = (root / rel) if not rel.startswith("/") else Path(rel)
    lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
    return any(text in lines[i] for i in range(max(0, line - 1), min(len(lines), line + 3)))


CONSTANTS = [  # (file, line, text that must appear, value, unit, stated source, used for, flows into)
    ("scripts_project/reconstruct_base_accounts.py", 79, "D('0.9')", 0.90, "NCV/GCV", "UNSD 05.pdf: natural gas TJ on GCV basis x 0.90", "UNSD natural gas TJ -> MWh NCV", "D1 2019 base (all sectors)"),
    ("scripts_project/reconstruct_base_accounts.py", 80, "D('0.0036')", 0.0036, "TJ/MWh", "-", "TJ rows (biomass, coal gases, heat) taken as NCV", "D1 2019 base"),
    ("scripts_project/reconstruct_base_accounts.py", 82, "frozen commodity-specific TWh/kton", None, "TWh/kt", "FROZEN_UPSTREAM_CONVERSIONS.json = pypsa-asean get_conv_factors", "kt rows", "D1 2019 base"),
    ("scripts_project/reconstruct_base_accounts.py", 84, "frozen0.00254TWh/1000m3", 0.00254, "TWh per 10^3 m3", "upstream (UNSD 9.135 GJ/m3 rounded)", "fuelwood", "D1 2019 base"),
    ("scripts_project/reconstruct_base_accounts.py", 90, "('hard coal',{'anthracite','coking coal','other bituminous coal'})", None, "-", "-",
     "coal hierarchy: parent kept, children excluded", "D1 2019 base"),
    ("scripts_project/s3_0_industry.py", 153, "e19 = {car: float(d[d.carrier == car].base_2019_mwh.sum())", None, "MWh", "-", "industry 2019 total per carrier = D1 base", "T_v2"),
    ("scripts_project/s3_0_industry.py", 158, "sub19[s_][car] = e19[car] * ((float(col[s_]) / tot)", None, "share", "industry_cache.json", "within-carrier sub-sector shares", "T_v2 split, other bucket"),
    ("scripts_project/d1_common.py", 127, "11.63", 11.63, "MWh/toe", "IEA toe", "AEO8 Mtoe anchors, EU27 ktoe", "2050 anchors"),
    ("scripts_project/d1_common.py", 133, "0.29307107", 0.29307107, "MWh/MMBtu", "NIST", "gas price, LNG regas adder", "costs"),
    ("scripts_project/d1_common.py", 137, "25.1208", 25.1208, "GJ/t", "WEO T2.3 (6,000 kcal/kg)", "coal price $/t -> $/MWh", "costs"),
    ("scripts_project/d1_common.py", 142, "0.9", 0.90, "NCV/GCV", "UNSD 05.pdf", "gas production, pipelines", "supply caps"),
    ("scripts_project/d1_common.py", 147, "42.3", 42.30, "GJ/t", "UNSD standard", "crude production", "supply caps"),
    ("scripts_project/d1_common.py", 150, "44.2", 44.20, "GJ/t", "UNSD standard", "NGL production", "supply caps"),
    ("scripts_project/d1_common.py", 153, "25.8", 25.80, "GJ/t", "UNSD standard", "hard coal production", "supply caps"),
    ("scripts_project/d1_common.py", 156, "14.0", 14.00, "GJ/t", "UNSD standard", "brown coal production", "supply caps"),
    ("scripts_project/d1_common.py", 162, "48.0", 48.0, "GJ/t", "IPCC T1.2 natural gas", "LNG Mtpa -> MWh", "LNG terminal capacity"),
    ("scripts_project/d1_common.py", 171, "9.14", 9.14, "GJ/m3", "UNSD standard", "wood processing residues", "biomass potential"),
    ("scripts_project/d1_biomass.py", 47, "LHV_RESIDUE_GJ_T = 15.0", 15.0, "GJ/t", "IRENA 2017 p.5 (moisture basis not stated)", "crop residues incl. bagasse", "biomass potential and cost"),
    ("scripts_project/d1_biomass.py", 486, "15 GJ/t", 15.0, "GJ/t", "IRENA 2017", "sugarcane residues price per MWh", "biomass cost"),
    ("scripts_project/d1_biomass.py", 492, "3500 * 4.1868", 14.65, "GJ/t", "ERIA T3.8 (3,500 kcal/kg)", "palm kernel shell price per MWh", "biomass cost"),
    ("scripts_project/d1_biomass.py", 497, "2450 * 4.1868", 10.26, "GJ/t", "ERIA T3.8 (2,450 kcal/kg)", "sawdust price per MWh", "biomass cost"),
    ("scripts_project/m08b_demand.py", 64, "10.8", 10.8, "MWh CH4 per t NH3", "PyPSA-Eur config", "ammonia feedstock gas deducted from NEU gas", "NEU gas 2050"),
    ("scripts_project/d1_fossil_production.py", 5, "Natural gas gross production (TJ GCV) x 0.90", 0.90, "NCV/GCV", "UNSD", "gas production cap uses GROSS production", "supply caps"),
    ("scripts_project/d1_fossil_production.py", 28, '("Natural gas", "gross production"): "gas"', None, "-", "-", "gross production selected (marketed row exists in the export)", "supply caps"),
]

CHAIN = [  # (step, file, line, text, reads, writes)
    (1, "scripts_project/reconstruct_base_accounts.py", 72, "def convert", "UNSD_2019_SOURCE_CAPSULE.json (UNdata 2025-05-02 rows), FROZEN_UPSTREAM_CONVERSIONS.json",
     "BASE_RECONSTRUCTION.json (accounts, selected_rows, nonenergy_reference)"),
    (2, "scripts_project/d1_demand_2050.py", 171, "BaseMWh", "BASE_RECONSTRUCTION.json, ASSEMBLY_V1_BLEND_BASELINE.json, electricity.json",
     "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv (base_2019_mwh)"),
    (3, "scripts_project/m08b_demand.py", 229, "dem = pd.read_csv(RATIO_TABLE", "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER.csv (RAS seeds, carrier shares), AEO8 anchors",
     "DEMAND_2050_BY_COUNTRY_SECTOR_CARRIER_ATS_ANCHOR.csv (base copied, value_2050 = anchor-based)"),
    (4, "scripts_project/s3_0_industry.py", 153, "e19 =", "ATS anchor table (Industry base x multiplier), industry_cache.json (within-carrier shares)",
     "INDUSTRY_2050_SUMMARY_aeo8_ats_anchor_OTHER_USEFUL_HEAT_BANDS.csv (T_v2), INDUSTRY_2050_OTHER_BUCKET.csv"),
    (5, "scripts_project/v3_industry.py", 158, "T = float(sum(v2.at[c, col(x)] for x in CARRIERS))", "s3_0 summary, nickel / non-ferrous tables",
     "INDUSTRY_2050_SUBSECTOR_CARRIER_V3.csv (v3 other bucket by conservation)"),
    (6, "scripts_project/s2_layers.py", 24, "TFEC_SECTORS", "ATS anchor table value_2050_mwh, v3 industry tables", "network loads (constant p_set)"),
]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, default=cm.WORK); a = ap.parse_args()
    out = a.work / "ncv"
    conv, lists = cm.upstream_dicts()
    car = {c: k.replace("_fuels", "") for k, v in lists.items() for c in v}
    E, _ = ui.export_2019()
    D = pd.read_csv(out / "NCV_BASE_ROWS_2019.csv")
    d1 = D.groupby("commodity").v3_mwh.sum() / 1e6
    # ---- 1. upstream dictionary ------------------------------------------------------------------------------------------------------
    rows = []
    std_alias = {"Fuelwood": "Fuelwood (TJ per 10^3 m3)"}
    for com, f in conv.items():
        ref = cm.COMMODITY_REF.get(com, (None, None, None))
        std_key = std_alias.get(com, ref[0])
        std = cm.UNSD_STD.get(std_key) if std_key else None
        if com in ("Other bituminous coal", "Anthracite", "Coking coal"):
            std = None   # UNSD standard is given for the parent 'Hard coal' only
        if com in ("Lignite", "Sub-bituminous coal"):
            std = None
        ip = cm.IPCC.get(ref[1]) if ref[1] else None
        gj = f * 3600
        present = sorted(set(E[E.commodity == com].country))
        rows.append(dict(commodity=com, upstream_twh_per_unit=f, gj_per_unit=gj, unit=("10^3 m3" if com == "Fuelwood" else ("t NH3" if com == "ammonia" else "t")),
                         model_carrier=car.get(com, ""), unsd_standard=std, diff_vs_unsd_pct=((gj / std - 1) * 100 if std else None),
                         ipcc_default=(ip[0] if ip else None), ipcc_lower=(ip[1] if ip else None), ipcc_upper=(ip[2] if ip else None),
                         diff_vs_ipcc_pct=((gj / ip[0] - 1) * 100 if ip else None), country_specific=False, year_specific=False,
                         present_in_asean_2019_export=";".join(present), d1_2019_twh=float(d1.get(com, 0.0)),
                         used_in="build_base_industry_totals.py / build_base_energy_totals.py (upstream); reconstruct_base_accounts.py via FROZEN_UPSTREAM_CONVERSIONS.json (D1)"))
    I = pd.DataFrame(rows)
    I.to_csv(out / "NCV_COEFF_INVENTORY.csv", index=False, float_format="%.6g")
    # ---- 2. constants and call chain (file:line verified) ----------------------------------------------------------------------------
    C = pd.DataFrame([dict(file=f, line=l, check_text=t, value=v, unit=u, stated_source=s, used_for=w, flows_into=fl, verified=check(f, l, t, cm.REPO))
                      for f, l, t, v, u, s, w, fl in CONSTANTS])
    C.to_csv(out / "NCV_OTHER_CONSTANTS.csv", index=False)
    K = pd.DataFrame([dict(step=s, file=f, line=l, check_text=t, reads=r, writes=w, verified=check(f, l, t, cm.REPO)) for s, f, l, t, r, w in CHAIN])
    K.to_csv(out / "NCV_CALL_CHAIN.csv", index=False)
    # ---- 3. upstream handling issues (quantified from the export) --------------------------------------------------------------------
    P = pd.read_csv(out / "UNSD_COAL_PARENT_CHECK.csv")
    R = pd.read_csv(out / "NCV_CACHE_RATIOS_2019.csv")
    raw = cm.unsd_export(); raw = raw[raw.Year.eq("2019")]
    def q_of(com, tr_sub):
        z = raw[(raw.commodity == com) & raw.transaction.str.lower().str.contains(tr_sub)]
        return ";".join(f"{r.country}:{r.transaction}={r.q:g}" for r in z.itertuples())
    issues = [
        dict(issue="coal parent and children both summed in the upstream industry totals (industry_cache.json)", where="pypsa-asean build_base_industry_totals.py:155-175 (coal_fuels list holds parents and children)",
             evidence=f"UNdata parents equal the sum of their children in all {len(P)} country-flow pairs checked (max |diff| {P.diff_kt.abs().max():g} kt); cache KH non-metallic coal 2.38744 TWh = Brown coal 252.8 kt x 14.0 + Sub-bituminous 252.8 kt x 20.0",
             effect="cache only gives within-carrier shares (s3_0_industry.py:158); D1 base de-duplicates (reconstruct :87-100); x_cache_dedup case: T_v2 TH -0.12 TWh, others 0",
             status="VERIFIED", in_ncv_scope="hierarchy"),
        dict(issue="'Other bituminous coal' rows dropped by the upstream", where="build_base_industry_totals.py:135-137", evidence="TH, SG report OBC as a child of 'Hard coal' (parent present in every flow) -> drop avoids a double count",
             effect="none on D1 (parent kept); none on shares beyond the double count above", status="VERIFIED", in_ncv_scope="hierarchy"),
        dict(issue="one NCV per commodity for all countries and years", where="_helpers.py:1837-1907", evidence="UNSD's own 2019 balances use country values (ID 24.48, VN 23.45, MM 23.26, PH 22.06, KH 19.88 GJ/t)",
             effect="see section 3", status="VERIFIED", in_ncv_scope="yes"),
        dict(issue="child factors inconsistent with parent factors", where="_helpers.py:1874-1881", evidence="Hard coal 25.8 but its children Other bituminous 20.0, Anthracite 18.0 (IPCC 25.8, 26.7); Brown coal 14.0 vs Sub-bituminous 20.0",
             effect="children only used where no parent is reported (not in the 2019 D1 rows of the 11 countries)", status="VERIFIED", in_ncv_scope="yes"),
        dict(issue="natural gas TJ (GCV) not multiplied by 0.90 in the upstream", where="build_base_industry_totals.py:43-45, build_base_energy_totals.py:122-125",
             evidence="D1 / industry_cache = 0.900 for gas in every country (D1 applies x0.90, reconstruct :79)", effect="cache gas cells uniformly 11.1 % high -> shares unchanged; energy_cache not on the D1 chain",
             status="VERIFIED", in_ncv_scope="yes (no model effect)"),
        dict(issue="spelling variants dropped by the upstream (commodity not in the dictionary / fuel lists)", where="build_base_industry_totals.py:32-36, 54",
             evidence=f"Motor gasoline: {q_of('Motor gasoline', '')}; Blast furnace gas: {q_of('Blast furnace gas', 'consumption')}; 'Natural gas': {q_of('Natural gas', 'production')}",
             effect="cache only; reconstruct normalises case (commodity()) and keeps them", status="VERIFIED", in_ncv_scope="naming"),
        dict(issue="commodities absent from the UNdata export (not an NCV issue)", where="pypsa-asean data/demand/unsd/data (52 files)",
             evidence="no 'Other vegetal material and residues', 'Other kerosene', municipal / industrial wastes rows for the 11 countries; UN Energy Balances 2019 biofuels / (export x UNSD standard) = 2.36 ID households, 1.43 ID FEC, 1.69 PH manufacturing (vintage-consistent countries)",
             effect="possible under-coverage of biomass (households, industry) and kerosene; not quantified here", status="VERIFIED (ratio) / INFERENCE (cause)", in_ncv_scope="no: coverage"),
        dict(issue="gas production caps use gross production although the export has a marketed-production row", where="d1_fossil_production.py:5-6, 28",
             evidence="2019 'Natural gas - Gross production' vs 'Natural gas (including LNG) - production' TJ: ID 2,910,311 vs 2,374,248 (+22.6 %), MY 3,398,101 vs 2,858,440 (+18.9 %), TL +33.7 %; BN balance primary production 383,975 TJ = marketed 426,638.6 x 0.9",
             effect="supply caps (upper bounds) too high; demand unaffected", status="VERIFIED", in_ncv_scope="no: flow choice"),
        dict(issue="bagasse NCV differs between demand and biomass supply/cost", where="reconstruct (7.72 GJ/t, 0.002144 TWh/kt) vs d1_biomass.py:47, 486 (15 GJ/t)",
             evidence="UNSD 7.72 GJ/t is at ~50 % moisture; IRENA 15 GJ/t basis not stated; APEC 2022 PH bagasse 17.8 MJ/kg, TH 7.53", effect="cost per MWh and potential of crop residues; not on the demand chain",
             status="VERIFIED", in_ncv_scope="yes (supply side)"),
        dict(issue="rail fuel loaded twice in the network (not an NCV issue)", where="reconstruct_base_accounts.py:227-234 adds RailNonElectric and keeps TransportEmbeddedFuelParent; s2_layers.py:25 (parent in LAND_TRANSPORT_ACCOUNTS) and :789-803 (tuple at :790) (RailNonElectric loaded)",
             evidence="ATS table ID Transport RailNonElectric oil 2,483,734.92 MWh and TransportEmbeddedFuelParent unclassified_fuel 2,483,734.92 MWh (same 2019 value)",
             effect="code reading only; not run; magnitude 2019 ID 2.48, KH 2.70, MM 0.97, TH 0.86 TWh x transport multiplier", status="INFERENCE (code reading)", in_ncv_scope="no: account mapping"),
    ]
    pd.DataFrame(issues).to_csv(out / "NCV_UPSTREAM_HANDLING_ISSUES.csv", index=False)
    # ---- 4. download list ------------------------------------------------------------------------------------------------------------
    sdmx = "https://data.un.org/WS/rest/data/UNSD,DF_UNDATA_ENERGY,/A.{area}.{commodities}.{transactions}/?startPeriod=2019&endPeriod=2019"
    dl = [
        dict(item="UNSD SDMX energy series with CONVERSION_FACTOR attribute, 2019, 11 countries, all solid / liquid commodities (coal parents and children, coke, BKB, fuelwood, charcoal, bagasse, oil products)",
             purpose="UNSD's own country NCV per commodity for the data vintage of the export (replaces the publication-derived values; resolves MY, TH, LA, KH)",
             how=sdmx + " (same API as research_inputs/assembly_v1/sources/unsd_targeted/; commodity codes in DSD_Energy.xml / codelists.json)", priority=1),
        dict(item="UN Energy Statistics Yearbook / Energy Balances 2022-2023 edition (PDF), 'Net calorific values' annex if published", purpose="UNSD country NCV tables after 2014 (the 2019 edition prints only standard values)", how="unstats.un.org energy publications", priority=3),
        dict(item="Philippines: DOE 'Philippine Energy Statistics' or energy balance with conversion factors (2019)", purpose="(c) for PH (now APEC 2022 proxy)", how="doe.gov.ph", priority=2),
        dict(item="Viet Nam: national energy statistics / energy balance with conversion factors (2019), e.g. MOIT / Institute of Energy", purpose="(c) for VN (now APEC 2022 proxy)", how="user", priority=2),
        dict(item="Myanmar: Myanmar Energy Statistics (ERIA) 2019-2020 with conversion factors", purpose="(c) for MM (none on disk)", how="eria.org", priority=3),
        dict(item="Lao PDR: Lao Energy Statistics (ERIA) with conversion factors", purpose="(c) for LA (none on disk)", how="eria.org", priority=3),
        dict(item="Cambodia: Cambodia Energy Statistics conversion-factor annex (the copy on disk gives firewood 3,820 kcal/kg, HFO 10,105 kcal/kg, no coal factor)", purpose="(c) for KH coal", how="eria.org", priority=3),
        dict(item="HEESI coal production / sales by calorific class (MEMR / ESDM), 2019", purpose="ID coal rank mix for (d) and a direct 2019 NCV of industrial coal", how="esdm.go.id", priority=2),
        dict(item="Thailand DEDE 'Energy Balance of Thailand 2019' conversion table (imported coal by rank)", purpose="TH sub-bituminous vs bituminous imports (EPPO gives one 'coal import' value)", how="dede.go.th", priority=2),
    ]
    pd.DataFrame(dl).to_csv(out / "NCV_DOWNLOAD_LIST.csv", index=False)
    # ---- 5. country reference matrix (coal) ------------------------------------------------------------------------------------------
    X = pd.read_csv(out / "NCV_FACTOR_SCHEMES.csv")
    S = pd.read_csv(out / "UNSD_IMPLIED_COAL_NCV_2019.csv")
    Rf = pd.read_csv(out / "NCV_REFERENCE_VALUES.csv")
    G = pd.read_csv(out / "GIPT_COAL_RANK_CAPACITY.csv").set_index("Country/area")
    gname = {"BN": "Brunei", "KH": "Cambodia", "ID": "Indonesia", "LA": "Laos", "MY": "Malaysia", "MM": "Myanmar", "PH": "Philippines", "TH": "Thailand", "VN": "Vietnam"}
    mrows = []
    for cc in cm.ISO:
        e = E[(E.country == cc) & (E.flow == "Manufacturing,const.,mining")]
        coal = {c: float(q) for c, q in zip(e.commodity, e.q) if c in ("Hard coal", "Brown coal", "Lignite", "Sub-bituminous coal", "Other bituminous coal", "Anthracite")}
        def xs(s, com):
            z = X[(X.country == cc) & (X.scheme == s) & (X.commodity == com)]
            return float(z.gj_per_unit.iloc[0]) if len(z) else None
        u19 = S[(S.country == cc) & S.status.str.startswith("VERIFIED")]
        r14 = Rf[(Rf.country == cc) & Rf.source.str.contains("2014")]
        ap = Rf[(Rf.country == cc) & Rf.source.str.startswith("APEC") & Rf.item.str.contains("coal|Anthracite|Lignite", case=False)]
        gr = G.loc[gname[cc]] if cc in gname and gname[cc] in G.index else None
        mrows.append(dict(country=cc, manufacturing_coal_kt_2019=";".join(f"{k}={v:g}" for k, v in coal.items()),
                          v3_hard=25.8012, v3_brown=14.0004,
                          unsd_2019_implied=";".join(f"{r.commodity}={r.implied_gj_per_t:.3f}" for r in u19.itertuples()),
                          unsd_2014_country=";".join(f"{r.item}={float(r.gj_per_unit):g}" for r in r14.itertuples()),
                          scheme_b=";".join(f"{c}={xs('b', c):.3f}" for c in ("Hard coal", "Brown coal") if xs('b', c)),
                          national_handbook_c=";".join(f"{c}={xs('c', c):.3f}" for c in ("Hard coal", "Brown coal", "Lignite", "Sub-bituminous coal", "Other bituminous coal", "Anthracite") if xs('c', c)),
                          apec_2022=";".join(f"{r.item}={r.gj_per_unit:.3f}" for r in ap.itertuples()),
                          ipcc_d=";".join(f"{c}={xs('d', c):.1f}" for c in ("Hard coal", "Brown coal", "Lignite", "Sub-bituminous coal", "Other bituminous coal", "Anthracite") if xs('d', c)),
                          gipt_operating_coal_mw_by_rank=(";".join(f"{k}={gr[k]:g}" for k in ("anthracite", "bituminous", "subbituminous", "lignite", "unknown") if k in gr.index and gr[k] > 0) if gr is not None else "")))
    M = pd.DataFrame(mrows)
    M.to_csv(out / "NCV_COUNTRY_REFERENCE_MATRIX.csv", index=False)
    ev = dict(constants_verified=int(C.verified.sum()), constants_total=len(C), chain_verified=int(K.verified.sum()), chain_total=len(K),
              unverified=C[~C.verified][["file", "line", "check_text"]].to_dict("records") + K[~K.verified][["file", "line", "check_text"]].to_dict("records"))
    (out / "_inventory_evidence.json").write_text(json.dumps(ev, indent=1) + "\n")
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60); pd.set_option("display.max_rows", 100)
    print(json.dumps(ev, indent=0))
    print(I[["commodity", "gj_per_unit", "unsd_standard", "diff_vs_unsd_pct", "ipcc_default", "diff_vs_ipcc_pct", "present_in_asean_2019_export", "d1_2019_twh"]].round(3).to_string())
    print(M.to_string())


if __name__ == "__main__":
    main()
