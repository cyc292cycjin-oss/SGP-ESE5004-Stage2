"""S4A-3 (L16, decision 39): audit of the new-build candidate potentials (`p_nom_max`) and the public sources found for them.

What the network has today (scripts_project/s1_candidates.py, configs/research/baseline.yaml):
  nuclear (large PWR)  p_nom_max = inf on every AC node except Singapore          decision 38 siting rule (grade C)
  nuclear SMR          p_nom_max = inf on every AC node                            decision 38 / 46
  geothermal, ror_new, hydro_new, PHS_new   p_nom_max = 0 on every node, DATA_PENDING   decision 39 (structure only)
  onwind / offwind-ac / offwind-dc / solar / solar rooftop   author potentials of the electric base (S4A-1 keeps the totals)

This script registers the public potential figures (official plans, agency statements, ADB / ANU / AEO8 / GEM) with grade and
status, writes the comparison table against the model p_nom_max by country, the GEM project pipeline by country / type and the
candidate cost-consistency check (decisions 46, 50, 52). NOTHING is applied to the network: p_nom_max values stay as they are
(user decision, S4A report section 3 / 5). Figures that only exist in secondary sources or could not be fetched are DATA_PENDING.

    python scripts_project/s4a_3_potentials.py [--costs results_project/<build>/integrated/costs_active_research.csv]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_json

SCRIPT = "scripts_project/s4a_3_potentials.py"
PV = ROOT / "research_inputs/potentials_v5"
SRC = ROOT / "research_inputs/registry_v5/sources"
GIPT = SRC / "GEM_GIPT_2026-09_ASEAN11.csv"
ANU = SRC / "ANU_PHES_global_summary_spreadsheet.xlsx"
CFG = ROOT / "configs/research/baseline.yaml"
PNOM = ROOT / "results_project/s4a/analysis/S4A3_CANDIDATE_PNOM_MAX_BY_COUNTRY.json"
PREPARED = ROOT / "research_inputs/cost_layers_v5/technology_data_v0.15.0_EUR2020/costs_2050_EUR2020_prepared.csv"
LAYER_B = ROOT / "research_inputs/cost_layers_v5/LAYER_B_AEO8_AUTHOR_RULE_2050.csv"
AEO8_SHA = "48c2a81913ed785cb0e14a55e332ea7bc87f912f7fabfbc8c654e09b66b11c06"   # ASEAN Energy Outlook 8 PDF (registered in S2/S3)
ACCESSED = "2026-10-16"
DEC = "L16,38,39"
ISO2 = {"Brunei": "BN", "Cambodia": "KH", "Indonesia": "ID", "Laos": "LA", "Malaysia": "MY", "Myanmar": "MM", "Philippines": "PH", "Singapore": "SG", "Thailand": "TH", "Timor-Leste": "TL", "Vietnam": "VN"}

# public documents downloaded on 2026-10-16 (kept outside git in work/p1_step4_20261016/sources_s4a3/; the ANU sheet is in the registry sources)
DOCS = [
    dict(key="DOE_RE_2024", file="doe_ph_renewable_energy.pdf", bytes=7255449, sha256="f33a274df0ab6ae15a1d9283954ff0ef53317b05bf80035976918cd871cb078e",
         title="DOE Philippines, Renewable Energy sector brief (data as of 31 Dec 2023; PDF modified 2024-05-04), 8 pages", url="https://prod-cms.doe.gov.ph/documents/d/guest/doe-renewable-energy"),
    dict(key="PEP_2023_2050", file="pep_2023_2050_vol1.pdf", bytes=13189775, sha256="f0a616c07c7defd321814aa1dc0fad46797455b6330912150de37f031628c1da",
         title="DOE Philippines, Philippine Energy Plan 2023-2050 Volume I", url="https://prod-cms.doe.gov.ph/documents/d/eppb/pep_2023-2050_-28volume_i-29-pdf"),
    dict(key="ADB_MM_2016", file="adb_myanmar_energy_assessment_2016.pdf", bytes=2525237, sha256="feb3c9382363df8cd75408497cfb2f0578c654da0720e640d8a3f4a2d22badf5",
         title="ADB (2016) Myanmar: Energy Sector Assessment, Strategy, and Road Map", url="https://www.adb.org/sites/default/files/institutional-document/218286/mya-energy-sector-assessment.pdf"),
    dict(key="KH_PDP_2022", file="cambodia_pdp_2022_2040_en.pdf", bytes=1323589, sha256="00faa26e38349a5a86d422aa2638f8e96dff81c0b370fae1d33e379748f1ff60",
         title="Royal Government of Cambodia, Power Development Master Plan 2022-2040 (English, 30 pages)", url="https://vdb-loi.com/wp-content/uploads/2023/06/Final-PDP-Cambodia-English-version.pdf"),
    dict(key="ANU_PHES", file="anu_phes_global_summary.xlsx", bytes=55383, sha256="7cbfb952b65b84293e473f3bd6e165dedf6692e44d313e98b7d7e224092c2f76", in_repo="research_inputs/registry_v5/sources/ANU_PHES_global_summary_spreadsheet.xlsx",
         title="ANU RE100 Group, Global Greenfield Pumped Hydro Energy Storage Atlas, global summary spreadsheet (Stocks, Stocks, Lu, Cheng, Blakers 2021, Joule 5(1):270-284)", url="https://re100.eng.anu.edu.au/global/ (Dropbox link, ?dl=1)"),
]
DOC_SHA = {d["key"]: d["sha256"] for d in DOCS}

# verbatim quotes from public web pages fetched on 2026-10-16 (snapshot file S4A3_WEB_QUOTES.json is the hashed source for these rows)
QUOTES = [
    dict(id="ESDM_2023_07_22", publisher="Kementerian ESDM (Indonesia), Media Center", date="2023-07-22", url="https://www.esdm.go.id/id/media-center/arsip-berita/kapasitas-terpasang-ebt-capai-127-gw-ini-gerak-cepat-pemerintah-serap-potensi-ebt",
         quote="potensi EBT yang berlimpah mencapai 3.687 GW; potensi surya sebesar 3.294 GW; potensi hidro 95 GW; potensi bioenergi 57 GW; potensi bayu 155 GW; potensi panas bumi 23 GW; potensi laut 63 GW; kapasitas terpasang ... 12.736,7 MW (Semester I 2023): PLT Air 6.738,3 MW, PLTBio 3.118,3 MW, PLT Panas Bumi 2.373,1 MW, PLT Surya 322,6 MW, PLT Bayu 154,3 MW"),
    dict(id="EBTKE_POTENSI", publisher="Direktorat Jenderal EBTKE (Indonesia), page 'Potensi' citing Buku Statistik EBTKE (year not stated)", date="n.d. (page accessed 2026-10-16)", url="https://ebtke.esdm.go.id/lintas/id/investasi-ebtke/sektor-aneka-et/potensi",
         quote="total potensi energi hidro di Indonesia mencapai 94,47 GW ... total potensi energi surya dan angin masing-masing mencapai 207,9 GW dan 60,64 GW"),
    dict(id="BADAN_GEOLOGI_2024_08_26", publisher="Badan Geologi / PSDMBP (Kementerian ESDM), Humas PSDMBP (Kolokium PSDMBP 2023, 1 Aug 2024, Bandung)", date="2024-08-26", url="https://geologi.esdm.go.id/media-center/pengungkapan-potensi-mineral-batubara-dan-panas-bumi-di-indonesia-untuk-pemenuhan-kebutuhan-industri-dan-transisi-energi",
         quote="Indonesia memiliki potensi sumber daya panas bumi sebesar 23,59 GW ... pemanfaatannya pada sektor ketenagalistrikan baru mencapai 2,3 GW"),
    dict(id="THINKGEO_2025_09_19", publisher="ThinkGeoEnergy (report on IIGCE 2025 opening by ESDM Minister Bahlil Lahadalia)", date="2025-09-19", url="https://www.thinkgeoenergy.com/indonesian-government-sets-direction-for-geothermal-growth-at-iigce-2025/",
         quote="potential estimated at about 23,742 MWe; 2,744 MWe of installed geothermal power generation capacity; 'we can only manage approximately 10 percent'"),
    dict(id="REN21_GSR2025_GEOTHERMAL", publisher="REN21 Global Status Report 2025, geothermal chapter (endnotes 29-34 not resolved on the page)", date="2025", url="https://www.ren21.net/gsr-2025/technologies/geothermal/",
         quote="Indonesia's geothermal power capacity expanded by at least 33 MW, bringing the total to approximately 2.6 GW ... 14.6 GW of proven reserves"),
    dict(id="PDP8_DECISION_500", publisher="Government of Vietnam, Decision 500/QD-TTg of 15 May 2023 (Power Development Plan VIII), full text on xaydungchinhsach.chinhphu.vn, Dieu 1 Muc III.1.b", date="2023-05-15", url="https://xaydungchinhsach.chinhphu.vn/toan-van-quy-hoach-phat-trien-dien-luc-quoc-gia-11923051616315244.htm",
         quote="Khai thac toi da tiem nang cac nguon thuy dien (tong tiem nang cua Viet Nam khoang 40.000 MW); ... thuy dien, bao gom ca thuy dien nho du kien dat 29.346 MW (2030) ... 36.016 MW (2050); thuy dien tich nang ... khoang 2.400 MW den nam 2030; dien gio tren bo ... 21.880 MW (tong tiem nang ky thuat ... khoang 221.000 MW); tiem nang ky thuat dien gio ngoai khoi (khoang 600.000 MW) ... 6.000 MW (2030) ... 70.000 - 91.500 MW (2050); Tiem nang dien mat troi cua Viet Nam khoang 963.000 MW (mat dat khoang 837.400 MW, mat nuoc khoang 77.400 MW va mai nha khoang 48.200 MW); dien sinh khoi (tiem nang khoang 7.000 MW); dien ... rac, chat thai ran (tiem nang khoang 1.800 MW)"),
    dict(id="PDP8_DECISION_768", publisher="Government of Vietnam, Decision 768/QD-TTg of 15 Apr 2025 (revised PDP VIII), as reported by baochinhphu.vn", date="2025-04-15", url="https://baochinhphu.vn/thu-tuong-chinh-phu-phe-duyet-dieu-chinh-quy-hoach-dien-viii-102250416180716025.htm",
         quote="2030 / 2050 (MW): thuy dien 33.294-34.667 / 40.624; thuy dien tich nang 2.400-6.000 / 20.691-21.327; dien hat nhan 4.000-6.400 (van hanh 2030-2035) / bo sung khoang 8.000; dien gio ngoai khoi 6.000-17.032 / 113.503-139.097; dien mat troi 46.459-73.416 / 293.088-295.646; pin luu tru 10.000-16.300 / 95.983-96.120; tiem nang: gio tren bo 221.000 MW, gio ngoai khoi 600.000 MW, mat troi 963.000 MW, thuy dien 40.000 MW"),
    dict(id="WB_PH_OSW_2022", publisher="World Bank press release, Manila (DOE / World Bank Group, ESMAP-funded Philippines Offshore Wind Roadmap)", date="2022-04-20", url="https://www.worldbank.org/en/news/press-release/2022/04/20/new-roadmap-shows-potential-for-40gw-of-offshore-wind-by-2050-in-ph",
         quote="the Philippines has 178 GW of technical offshore wind potential; low growth: 3GW of offshore wind by 2040; high growth: 21GW making up 21 percent of its electricity supply"),
    dict(id="PHILSTAR_PEP_2023_09_01", publisher="The Philippine Star (R. Mercurio), quoting DOE Undersecretary Giovanni Bacordo on the PEP 2023-2050", date="2023-09-01", url="https://www.philstar.com/business/2023/09/01/2292834/energy-roadmap-now-includes-nuclear",
         quote="nuclear: 1,200 MW by 2032, 2,400 MW by 2035, 4,800 MW by 2050 (clean energy scenario); offshore wind 19 GW (option one) / 50 GW (option two) by 2050; RE share 35% 2030, 50% 2040, >50% 2050"),
    dict(id="ASEANPOST_LAOS_2018", publisher="The ASEAN Post, 'Lao's hydropower ambitions' (citing the Ministry of Energy and Mines)", date="2018-02-23", url="https://theaseanpost.com/article/laos-hydropower-ambitions",
         quote="Lao has a theoretical hydroelectric potential of about 18,000MW excluding the mainstream of Mekong. Of this, 12,500MW comes from the major Mekong sub-basins while the remainder comes from minor Mekong or non-Mekong basins."),
    dict(id="SEDA_MYRER", publisher="SEDA Malaysia, Malaysia Renewable Energy Roadmap (MyRER) web page, resource map 'Updated as 6 October 2021' (sources SEDA; ST; SB Peninsular Malaysia; SB Sabah; SESB; SEB)", date="2021-10-06", url="https://www.seda.gov.my/reportal/myrer/",
         quote="Solar 210GW Ground-mounted, 42GW Rooftop, 17GW Floating; Large hydro 3.1GW Peninsular, 500MW Sabah, 10GW Sarawak; Small hydro 1.7GW Peninsular, 0.6GW Sabah, 0.2GW Sarawak; Bioenergy 2.3GW Biomass, 736MW Biogas, 516MW Solid Waste; Geothermal 162MW Peninsular, 67MW Sabah"),
    dict(id="RECCESSARY_TH_PHS_2024", publisher="Reccessary, 'Thailand to add 3 more large-scale pumped storage hydropower plants' (EGAT)", date="2024-11-11", url="https://www.reccessary.com/en/news/thailand-to-add-3-more-large-scale-pumped-storage-hydropower-plants",
         quote="EGAT plans to invest 90 billion Thai baht (approximately 2.6 billion USD) ... three dams ... with a total estimated capacity of 2,472 MW. The first facility is expected to begin operation by 2034."),
    dict(id="NPR_AP_2026_03_26", publisher="AP via NPR, 'Southeast Asia turns to nuclear as Iran war disrupts energy supplies'", date="2026-03-26", url="https://www.npr.org/2026/03/26/g-s1-115291/southeast-asia-turns-to-nuclear-as-iran-war-disrupts-energy-supplies",
         quote="Indonesia added nuclear to its new energy plan last year, aiming to build two small modular reactors by 2034. ... Thailand set a target last year of adding 600 megawatts of nuclear generating capacity by 2037."),
    dict(id="STIMSON_2025", publisher="Stimson Center, 'Nuclear Energy Challenges in Southeast Asia's Clean Energy Transition'", date="2025", url="https://www.stimson.org/2025/nuclear-energy-challenges-in-southeast-asias-clean-energy-transition/",
         quote="the government [Indonesia] plans to rollout 10,000 MW of nuclear energy by 2040 ... In 2024, Thailand added 600 MW of SMRS back into its draft PDP ... Malaysia's thirteenth national plan revives nuclear energy ... specific targets will be determined through future study"),
]
# PDF page citations (PDF page index) used below
PDF = {
    "DOE_RE_2024": {"table18": "p.4 Table 18 'Potential RE Capacities under CREZ' (MW): Solar PV 58,110; Wind 93,987; Geothermal 365; Hydropower 655,034; Biomass 374; total 807,870 (Luzon 360,244 / Visayas 39,333 / Mindanao 408,293)",
                    "osw": "p.4: 'total estimated technical potential of 178 GW, 160 GW of which is in deep water applicable for floating Wind turbines, while the remaining 18 GW is in shallow water'",
                    "wind": "p.5: 'CREZ ... total onshore Wind potential capacity of 93,987 MW ... Luzon 54,115 MW, Visayas 25,429 MW, Mindanao 14,443 MW'; 'in 2000, the Philippines Wind Resource Atlas Development of NREL identified a total of 76.6 GW'",
                    "solar": "p.5: 'total Solar energy potential under CREZ is estimated at 58,110 MW, with 35,031 MW coming from Luzon'; installed 1,530 MW (31 Dec 2022); PEP 2050 total 56,478 MW REF / 54,695 CES1 / 35,651 CES2",
                    "hydro": "p.6: 'Various resource assessments for Hydropower potential unveil a total potential capacity of 23,375 MW. Of this capacity, 17,366 MW is from Luzon, 2,448 MW in Visayas, and 3,569 MW in Mindanao'; PEP 2050 target 10,265 MW REF / 6,800 CES1 / 6,180 CES2; CREZ 'around 655,034 MW'",
                    "geo": "p.6: '39 Geothermal Service Contracts (GSCs) with a total installed capacity of 1,951 MW'; PEP 2050 addition 1,355 MW REF / 1,005 MW CES; 'CREZ Report also identified potentials for Geothermal energy development of around 365 MW'"},
    "PEP_2023_2050": {"nuclear": "PDF p.19-20 (Executive Summary): 'nuclear energy, which involves the commissioning of at least 4,800 MW of potential capacity by 2050'; '4,800 MW of nuclear capacity by 2050'; p.27 'entry of nuclear energy starting 2032'; p.34 '19 GW OSW capacities and the 4,800 MW nuclear capacity'",
                      "awarded": "PDF p.69 (printed p.54, Energy Situationer 2022): geothermal 24 projects 870.6 MW awarded; hydro aggregate 3,745 MW installed, 12,272.5 MW potential from 362 awarded projects; solar installed 1,530 MW, awarded 21,413.6 MW (156 projects); wind installed 427 MW, awarded 45,631 MW (21 projects)",
                      "osw": "PDF p.103: '178 GW of OSW potential capacity ... 18 GW of fixed and 160 GW of floating'"},
    "ADB_MM_2016": {"hydro": "PDF p.13 para 19: 'It is estimated that there is more than 100,000 MW of installed capacity potential. Myanmar has identified 92 large hydropower potential projects with a total installed capacity of 46,000 MW, while the current installed capacity of hydropower plants is 3,033 MW.'"},
    "KH_PDP_2022": {"targets": "PDF p.9: 2030 mix incl. 1,558 MW of Hydro (27.7%), 1,005 MW of Solar PV; 2040 mix incl. Hydro (21.4%), 3,155 MW of Solar PV (29.8%), 420 MW of BESS, 198 MW of Biomass, 3,095 MW imports from Laos; no national resource-potential statement in the 30-page English version"},
    "ANU_PHES": {"sea": "sheet 'South_Eastern_Asia Summary': Count of pairs 62,665; Total potential capacity 2,210,850 GWh; e.g. 150GWh_18h (8.3 GW per site) class A 2,703 / B 1,732 / C 1,058 / D 730 / E 363 sites; 50GWh_6h (8.3 GW) 27,851 sites; no per-country split in the summary (site KML/CSV via the atlas map, download list)"},
}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--costs", type=Path, default=ROOT / "results_project/s4a/build_check2/integrated/costs_active_research.csv")
    a = ap.parse_args(); PV.mkdir(parents=True, exist_ok=True)
    # --- snapshots ---------------------------------------------------------------------------------------------------
    qpath = PV / "S4A3_WEB_QUOTES.json"; qpath.write_text(json.dumps(dict(accessed=ACCESSED, quotes=QUOTES, pdf_citations=PDF), indent=1, ensure_ascii=False)); QSHA = sha256(qpath)
    pd.DataFrame(DOCS).to_csv(PV / "S4A3_SOURCE_FILES.csv", index=False)
    assert sha256(ANU) == DOC_SHA["ANU_PHES"], "ANU spreadsheet in the registry sources differs from the downloaded file"
    gipt_sha = sha256(GIPT); cfg_sha = sha256(CFG)
    reg = Registry(SCRIPT)

    def add(pid, desc, value, unit, tier, src, loc, sha, country="", status="REGISTERED", lo=None, hi=None):
        reg.add(pid, desc, value, unit, tier, src, loc, sha, country=country, decision_ref=DEC, status=status, sensitivity_low=lo, sensitivity_high=hi)

    # --- 1. what the model has (audit rows) --------------------------------------------------------------------------
    add("cand_nuclear_pnom_max_rule", "Large-PWR candidate p_nom_max on every AC node of the allowed countries (all except SG): unbounded (inf); siting evidence grade C; no country potential or plan cap applied", np.inf, "MW", "C",
        "configs/research/baseline.yaml research.nuclear.large_pwr; scripts_project/s1_candidates.py add_nuclear_candidates", "96 generators with p_nom_max inf in the S4A build", cfg_sha, status="REFERENCE_ONLY")
    add("cand_smr_pnom_max_rule", "SMR candidate p_nom_max on every AC node (97 incl. SG): unbounded (inf); AEO8 D.15 cost (decision 46, grade C)", np.inf, "MW", "C", "configs/research/baseline.yaml research.nuclear.smr", "97 generators with p_nom_max inf", cfg_sha, status="REFERENCE_ONLY")
    for k in ["geothermal", "ror_new", "hydro_new", "PHS_new"]:
        add(f"cand_{k}_pnom_max_today", f"Site candidate {k}: one component per AC node with p_nom_max 0 (structure only, decision 39); potentials below are registered but NOT applied (user decision)", 0.0, "MW", "C",
            "configs/research/baseline.yaml research.site_candidates", f"site_candidates.{k}.p_nom_max", cfg_sha, status="REFERENCE_ONLY")

    # --- 2. public potential figures ----------------------------------------------------------------------------------
    rows = []   # table for the report: country, tech, kind, value_mw, grade, status, source, locator

    def pot(country, tech, kind, value_mw, tier, status, src, loc, sha, pid=None, desc=""):
        pid = pid or f"potential_{tech}_{country}_{kind}".replace("-", "_").replace(" ", "_")
        add(pid, desc or f"{country} {tech} {kind} (public figure, not applied)", value_mw, "MW", tier, src, loc, sha, country=country, status=status)
        rows.append(dict(country=country, tech=tech, kind=kind, value_mw=value_mw if status != "DATA_PENDING" else np.nan, grade=tier, status=status, source=src, locator=loc))

    def pending(country, tech, note, impact):
        pid = f"potential_{tech}_{country}_DATA_PENDING".replace(" ", "_")
        add(pid, f"{country} {tech}: no official/primary potential figure found or fetched on {ACCESSED}: {note}. Impact if left at p_nom_max 0: {impact}", None, "MW", "C", "S4A-3 search log (S4A3_WEB_QUOTES.json)", note, QSHA, country=country, status="DATA_PENDING")
        rows.append(dict(country=country, tech=tech, kind="potential", value_mw=np.nan, grade="C", status="DATA_PENDING", source="not found", locator=note))

    # geothermal
    pot("ID", "geothermal", "resource_potential", 23590.0, "B", "CANDIDATE_ONLY", "Badan Geologi / PSDMBP (ESDM) 2024-08-26", "quote BADAN_GEOLOGI_2024_08_26: 'potensi sumber daya panas bumi sebesar 23,59 GW', utilisation 2.3 GW", QSHA,
        desc="Indonesia geothermal resource potential 23.59 GW (Badan Geologi/PSDMBP 2024; ESDM 2023 press: 23 GW; Minister Sept 2025: 23,742 MWe). Resource (not reserve) class; includes the 2.37-2.74 GW in operation")
    pot("ID", "geothermal", "minister_2025", 23742.0, "C", "REFERENCE_ONLY", "ESDM Minister at IIGCE 2025 via ThinkGeoEnergy 2025-09-19", "quote THINKGEO_2025_09_19", QSHA)
    pot("ID", "geothermal", "esdm_2023", 23000.0, "B", "REFERENCE_ONLY", "Kementerian ESDM press release 2023-07-22", "quote ESDM_2023_07_22: 'potensi panas bumi 23 GW'", QSHA)
    pot("ID", "geothermal", "proven_reserves_ren21", 14600.0, "C", "REFERENCE_ONLY", "REN21 GSR 2025 geothermal chapter (endnote 32, primary source not resolved)", "quote REN21_GSR2025_GEOTHERMAL: '14.6 GW of proven reserves'", QSHA)
    pot("PH", "geothermal", "crez_zones", 365.0, "B", "REFERENCE_ONLY", "DOE RE sector brief 2024 (CREZ report)", PDF["DOE_RE_2024"]["geo"], DOC_SHA["DOE_RE_2024"])
    pot("PH", "geothermal", "awarded_pipeline_2022", 870.6, "B", "CANDIDATE_ONLY", "PEP 2023-2050 Vol I (DOE)", PDF["PEP_2023_2050"]["awarded"], DOC_SHA["PEP_2023_2050"],
        desc="Philippines geothermal: 24 awarded projects with 870.6 MW potential capacity (2022); installed 1,951 MW under 39 GSCs (2023); PEP 2050 addition 1,355 MW REF / 1,005 MW CES; total resource potential not stated in the fetched DOE documents")
    pot("PH", "geothermal", "pep_2050_addition_ref", 1355.0, "B", "REFERENCE_ONLY", "DOE RE sector brief 2024 (PEP 2023-2050 REF scenario)", PDF["DOE_RE_2024"]["geo"], DOC_SHA["DOE_RE_2024"])
    pending("PH", "geothermal_total_resource", "DOE page figure ~4,160 MW seen only in a search summary (legacy.doe.gov.ph unreachable); not fetched", "2050 geothermal in PH limited to 938 MW of surviving stock (S4A-2 lifetime rule) -> more gas/solar+storage in Luzon/Visayas (INFERENCE)")
    pot("MY", "geothermal", "myrer", 229.0, "B", "CANDIDATE_ONLY", "SEDA MyRER resource map (2021-10-06)", "quote SEDA_MYRER: Geothermal 162MW Peninsular, 67MW Sabah", QSHA)
    pot("VN", "geothermal", "gem_announced", 45.0, "B", "REFERENCE_ONLY", "GEM Global Integrated Power Tracker 2026-09", "status announced, Vietnam, Type geothermal", gipt_sha)
    for c in ["TH", "KH", "LA", "MM", "BN", "SG", "TL", "VN"]:
        pending(c, "geothermal", "no official resource assessment found (VN: only a 45 MW GEM announced unit)", "none material: no geothermal stock and no plan capacity in these countries (INFERENCE)")
    # hydro (reservoir + run-of-river; the split is DATA_PENDING everywhere)
    pot("ID", "hydro", "ebtke_statistics", 94470.0, "B", "CANDIDATE_ONLY", "Direktorat Jenderal EBTKE potency page (Buku Statistik EBTKE)", "quote EBTKE_POTENSI: 'potensi energi hidro ... 94,47 GW'", QSHA,
        desc="Indonesia hydro potential 94.47 GW (EBTKE statistics; ESDM 2023 press: 95 GW); installed 6,738 MW (S1 2023). Reservoir/ROR split not given")
    pot("ID", "hydro", "esdm_2023", 95000.0, "B", "REFERENCE_ONLY", "Kementerian ESDM press release 2023-07-22", "quote ESDM_2023_07_22: 'potensi hidro 95 GW'", QSHA)
    pot("VN", "hydro", "pdp8_total_potential", 40000.0, "A", "CANDIDATE_ONLY", "Decision 500/QD-TTg (PDP VIII) 2023-05-15, Dieu 1 Muc III.1.b; confirmed in Decision 768/QD-TTg 2025", "quote PDP8_DECISION_500: 'tong tiem nang cua Viet Nam khoang 40.000 MW'", QSHA,
        desc="Vietnam total hydropower potential about 40,000 MW (PDP VIII); 2030 target 29,346 MW (33,294-34,667 in the 2025 revision), 2050 target 36,016 MW (40,624 MW in Decision 768)")
    pot("VN", "hydro", "pdp8_rev_2050_target", 40624.0, "A", "REFERENCE_ONLY", "Decision 768/QD-TTg 2025-04-15 (revised PDP VIII) via baochinhphu.vn", "quote PDP8_DECISION_768: thuy dien 2050 40.624 MW", QSHA)
    pot("PH", "hydro", "doe_resource_assessments", 23375.0, "B", "CANDIDATE_ONLY", "DOE RE sector brief 2024", PDF["DOE_RE_2024"]["hydro"], DOC_SHA["DOE_RE_2024"],
        desc="Philippines hydropower total potential 23,375 MW (Luzon 17,366 / Visayas 2,448 / Mindanao 3,569; 'various resource assessments'); PEP 2050 target 10,265 MW REF; awarded 12,272.5 MW (2022); CREZ 655,034 MW is a gross figure not usable as p_nom_max")
    pot("PH", "hydro", "pep_2050_target_ref", 10265.0, "B", "REFERENCE_ONLY", "DOE RE sector brief 2024 (PEP 2023-2050 REF)", PDF["DOE_RE_2024"]["hydro"], DOC_SHA["DOE_RE_2024"])
    pot("PH", "hydro", "awarded_pipeline_2022", 12272.5, "B", "REFERENCE_ONLY", "PEP 2023-2050 Vol I (DOE)", PDF["PEP_2023_2050"]["awarded"], DOC_SHA["PEP_2023_2050"])
    pot("PH", "hydro", "crez_gross", 655034.0, "C", "REFERENCE_ONLY", "DOE RE sector brief 2024 (CREZ report)", PDF["DOE_RE_2024"]["table18"] + "; magnitude implausible for exploitable capacity -> reference only", DOC_SHA["DOE_RE_2024"])
    pot("LA", "hydro", "aeo8_potential", 26000.0, "C", "CANDIDATE_ONLY", "ACE ASEAN Energy Outlook 8 (2024), chapter 2 text p.75 citing ref [44] (Phouthonesy)", "'Lao PDR has around 26 GW of hydropower potential, yet only 9 GW have been utilised as of 2020 [44]'", AEO8_SHA,
        desc="Laos hydropower potential ~26 GW (AEO8 secondary citation); MEM figure 18,000 MW theoretical excluding the Mekong mainstream (ASEAN Post 2018). Primary MEM document not fetched")
    pot("LA", "hydro", "mem_excl_mekong_mainstream", 18000.0, "C", "REFERENCE_ONLY", "Lao Ministry of Energy and Mines via The ASEAN Post 2018-02-23", "quote ASEANPOST_LAOS_2018", QSHA)
    pot("MM", "hydro", "adb_identified_projects", 46000.0, "B", "CANDIDATE_ONLY", "ADB (2016) Myanmar Energy Sector Assessment", PDF["ADB_MM_2016"]["hydro"], DOC_SHA["ADB_MM_2016"],
        desc="Myanmar: 92 identified large hydropower projects 46,000 MW (ADB 2016; MOEE 2015 figure 45,632 MW per World Bank SEA 2018); theoretical potential > 100,000 MW")
    pot("MM", "hydro", "adb_theoretical", 100000.0, "B", "REFERENCE_ONLY", "ADB (2016) Myanmar Energy Sector Assessment", PDF["ADB_MM_2016"]["hydro"] + " (lower bound 'more than 100,000 MW')", DOC_SHA["ADB_MM_2016"])
    pot("KH", "hydro", "pdp_2040_target", 2973.0, "B", "REFERENCE_ONLY", "Cambodia Power Development Master Plan 2022-2040 (MME)", PDF["KH_PDP_2022"]["targets"] + "; 2,973 MW hydro in 2040 (ASEAN Energy Database summary of the plan)", DOC_SHA["KH_PDP_2022"])
    pending("KH", "hydro", "the 30-page English PDP gives capacity targets (hydro 1,558 MW 2030, ~2,973 MW 2040) but no national resource potential", "new hydro limited to the plan pipeline; KH stays import-dependent (LA PPAs 3,095 MW in the plan) (INFERENCE)")
    pot("MY", "hydro", "myrer_large_hydro", 13600.0, "B", "CANDIDATE_ONLY", "SEDA MyRER resource map (2021-10-06)", "quote SEDA_MYRER: Large hydro 3.1GW Peninsular + 500MW Sabah + 10GW Sarawak = 13.6 GW; small hydro 1.7 + 0.6 + 0.2 = 2.5 GW", QSHA,
        desc="Malaysia large-hydro resource 13.6 GW and small-hydro 2.5 GW (SEDA MyRER map; sum of regional labels, our arithmetic); installed hydro 6,199 MW (GEM operating)")
    pot("MY", "hydro", "myrer_small_hydro", 2500.0, "B", "REFERENCE_ONLY", "SEDA MyRER resource map (2021-10-06)", "quote SEDA_MYRER small hydro labels", QSHA)
    pending("TH", "hydro", "only secondary academic figure (15,155 MW, 2019 review; ScienceDirect fetch 403) and EGAT PHS plans; no DEDE/EGAT resource statement fetched", "new hydro/PHS in TH limited to stock + 2,472 MW EGAT PHS plan context (INFERENCE)")
    pending("TL", "hydro", "2010 study figure 252 MW quoted in press (fetch 404); no EDTL/ADB document", "immaterial for the region (TL load < 1 TWh) (INFERENCE)")
    for c in ["BN", "SG"]:
        add(f"potential_hydro_{c}_SOURCE_ZERO", f"{c}: no hydropower units in GEM GIPT 2026-09 and no hydro resource (geography); candidate hydro/ror/PHS p_nom_max 0 is a source zero, not a data gap", 0.0, "MW", "B", "GEM Global Integrated Power Tracker 2026-09", "no Type hydropower rows for the country", gipt_sha, country=c, status="SOURCE_ZERO")
        rows.append(dict(country=c, tech="hydro", kind="potential", value_mw=0.0, grade="B", status="SOURCE_ZERO", source="GEM GIPT 2026-09 (no units) / geography", locator="no hydropower rows"))
    # pumped hydro
    pot("SEA", "PHS", "anu_atlas_regional_gwh", 2210850.0, "B", "REFERENCE_ONLY", "ANU Global Greenfield PHES Atlas summary spreadsheet (Stocks et al. 2021)", PDF["ANU_PHES"]["sea"] + " (value in GWh, not MW)", DOC_SHA["ANU_PHES"],
        pid="potential_PHS_SEA_anu_atlas_gwh", desc="South-Eastern Asia greenfield closed-loop PHES: 62,665 site pairs, 2,210,850 GWh total storage potential (ANU atlas; an order of magnitude above any plausible 2050 need); per-country split not in the summary sheet")
    pending("ALL", "PHS_per_country", "ANU atlas per-country site lists need the atlas site data (KML/CSV via the web map; download list); official PHS potentials only as plan targets (VN 20.7-21.3 GW 2050; TH 2,472 MW EGAT)", "PHS candidates stay at 0 -> storage need met by batteries/hydrogen only (INFERENCE)")
    pot("VN", "PHS", "pdp8_rev_2050_target", 21327.0, "A", "REFERENCE_ONLY", "Decision 768/QD-TTg 2025-04-15 via baochinhphu.vn", "quote PDP8_DECISION_768: thuy dien tich nang 2050 20.691-21.327 MW", QSHA)
    pot("TH", "PHS", "egat_planned", 2472.0, "C", "REFERENCE_ONLY", "EGAT via Reccessary 2024-11-11", "quote RECCESSARY_TH_PHS_2024", QSHA)
    # nuclear plans (siting rule unchanged; plan capacities for comparison with the unbounded candidates)
    pot("PH", "nuclear", "pep_2050_target", 4800.0, "B", "REFERENCE_ONLY", "PEP 2023-2050 Vol I (DOE)", PDF["PEP_2023_2050"]["nuclear"] + "; Philstar 2023-09-01: 1,200 MW 2032, 2,400 MW 2035", DOC_SHA["PEP_2023_2050"])
    pot("VN", "nuclear", "pdp8_rev_2030_2035", 6400.0, "A", "REFERENCE_ONLY", "Decision 768/QD-TTg 2025-04-15 via baochinhphu.vn", "quote PDP8_DECISION_768: dien hat nhan 4.000-6.400 MW (2030-2035), bo sung khoang 8.000 MW (2050) -> 12,000-14,400 MW by 2050", QSHA)
    pot("ID", "nuclear", "plan_2040_press", 10000.0, "C", "REFERENCE_ONLY", "Stimson 2025 (10 GW by 2040) / AP 2026-03-26 (two SMRs by 2034, RUPTL)", "quotes STIMSON_2025, NPR_AP_2026_03_26; primary RUPTL/RUKN not fetched", QSHA)
    pot("TH", "nuclear", "draft_pdp2024_smr", 600.0, "C", "REFERENCE_ONLY", "AP 2026-03-26 / Stimson 2025 (draft PDP2024)", "quotes NPR_AP_2026_03_26, STIMSON_2025: 600 MW by 2037", QSHA)
    pot("SEA", "nuclear", "aeo8_regional_2050", 10000.0, "B", "REFERENCE_ONLY", "ACE ASEAN Energy Outlook 8 (2024) p.153", "'nuclear energy will be introduced in the region after 2030, starting with an initial capacity of 3.4 GW, and potentially increasing to around 10 GW by 2050'", AEO8_SHA, pid="potential_nuclear_SEA_aeo8_2050")
    # wind / solar official potentials (the electric base already carries author potentials; comparison only)
    pot("VN", "onwind", "pdp8_technical", 221000.0, "A", "REFERENCE_ONLY", "Decision 500/QD-TTg Muc III.1.b (confirmed in 768)", "quote PDP8_DECISION_500: 'tong tiem nang ky thuat ... khoang 221.000 MW'", QSHA)
    pot("VN", "offwind", "pdp8_technical", 600000.0, "A", "REFERENCE_ONLY", "Decision 500/QD-TTg Muc III.1.b (confirmed in 768)", "quote PDP8_DECISION_500: 'tiem nang ky thuat dien gio ngoai khoi (khoang 600.000 MW)'", QSHA)
    pot("VN", "solar", "pdp8_technical", 963000.0, "A", "REFERENCE_ONLY", "Decision 500/QD-TTg Muc III.1.b (confirmed in 768)", "quote PDP8_DECISION_500: 963.000 MW = ground 837.400 + floating 77.400 + rooftop 48.200", QSHA)
    pot("VN", "solar rooftop", "pdp8_technical", 48200.0, "A", "REFERENCE_ONLY", "Decision 500/QD-TTg Muc III.1.b", "quote PDP8_DECISION_500: 'mai nha khoang 48.200 MW'", QSHA)
    pot("PH", "offwind", "doe_wb_roadmap_technical", 178000.0, "B", "REFERENCE_ONLY", "DOE / World Bank Philippines Offshore Wind Roadmap (2022)", PDF["DOE_RE_2024"]["osw"] + "; " + PDF["PEP_2023_2050"]["osw"] + "; quote WB_PH_OSW_2022", DOC_SHA["DOE_RE_2024"])
    pot("PH", "onwind", "crez_zones", 93987.0, "B", "REFERENCE_ONLY", "DOE RE sector brief 2024 (CREZ report)", PDF["DOE_RE_2024"]["wind"], DOC_SHA["DOE_RE_2024"])
    pot("PH", "onwind", "nrel_2000_atlas", 76600.0, "C", "REFERENCE_ONLY", "NREL Philippines Wind Resource Atlas 2000 via DOE RE sector brief 2024", PDF["DOE_RE_2024"]["wind"], DOC_SHA["DOE_RE_2024"])
    pot("PH", "solar", "crez_zones", 58110.0, "B", "REFERENCE_ONLY", "DOE RE sector brief 2024 (CREZ report)", PDF["DOE_RE_2024"]["solar"], DOC_SHA["DOE_RE_2024"])
    pot("ID", "solar", "esdm_2023", 3294000.0, "B", "REFERENCE_ONLY", "Kementerian ESDM press release 2023-07-22", "quote ESDM_2023_07_22: 'potensi surya sebesar 3.294 GW' (EBTKE statistics page: 207.9 GW, different basis)", QSHA)
    pot("ID", "wind", "esdm_2023", 155000.0, "B", "REFERENCE_ONLY", "Kementerian ESDM press release 2023-07-22", "quote ESDM_2023_07_22: 'potensi bayu 155 GW' (EBTKE statistics page: 60.64 GW)", QSHA)
    pot("MY", "solar", "myrer", 269000.0, "B", "REFERENCE_ONLY", "SEDA MyRER resource map (2021-10-06)", "quote SEDA_MYRER: 210 GW ground + 42 GW rooftop + 17 GW floating", QSHA)
    pot("MY", "solar rooftop", "myrer", 42000.0, "B", "REFERENCE_ONLY", "SEDA MyRER resource map (2021-10-06)", "quote SEDA_MYRER: 42GW Rooftop", QSHA)
    for c, v, lo, hi in [("ID", 655000.0, 194000.0, 655000.0), ("MY", 34000.0, None, None), ("VN", 370000.0, None, None)]:
        add(f"potential_solar_rooftop_{c}_aeo8", f"{c} rooftop PV potential per AEO8 p.140 ('Indonesia has the potential for between 194 GWp and 655 GWp ... Malaysia and Vietnam ... 34 GWp and 370 GWp respectively', refs [134], [135])", v, "MWp", "B", "ACE ASEAN Energy Outlook 8 (2024) p.140", "chapter text p.140", AEO8_SHA, country=c, status="REFERENCE_ONLY", lo=lo, hi=hi)
        rows.append(dict(country=c, tech="solar rooftop", kind="aeo8_potential", value_mw=v, grade="B", status="REFERENCE_ONLY", source="AEO8 p.140", locator="194-655 GWp (ID), 34 (MY), 370 (VN)"))

    # --- 3. GEM project pipeline (announced + pre-construction + construction) by country / type ------------------------
    g = pd.read_csv(GIPT, low_memory=False); g["cap"] = pd.to_numeric(g["Capacity (MW)"], errors="coerce"); g["iso2"] = g["Country/area"].map(ISO2)
    g["cls"] = np.where((g["Type"] == "hydropower") & (g["Technology"] == "pumped storage"), "PHS", g["Type"])
    pipe = g[g["Status"].isin(["announced", "pre-construction", "construction"])]
    pv = pipe.pivot_table(index="cls", columns="iso2", values="cap", aggfunc="sum", fill_value=0.0).round(1)
    pv = pv.loc[[c for c in ["geothermal", "hydropower", "PHS", "nuclear", "wind", "solar", "bioenergy", "coal", "oil/gas"] if c in pv.index]]
    pv.to_csv(PV / "GEM_PIPELINE_2026-09_BY_COUNTRY_TYPE.csv")
    by_status = pipe[pipe["cls"].isin(["geothermal", "hydropower", "PHS", "nuclear"])].pivot_table(index=["cls", "iso2"], columns="Status", values="cap", aggfunc="sum", fill_value=0.0).round(1)
    by_status.to_csv(PV / "GEM_PIPELINE_2026-09_GEO_HYDRO_PHS_NUCLEAR_BY_STATUS.csv")
    for cls in ["geothermal", "hydropower", "PHS", "nuclear"]:
        for c in pv.columns:
            v = float(pv.at[cls, c]) if cls in pv.index else 0.0
            if v > 0:
                add(f"pipeline_gem_{cls}_{c}", f"{c} {cls}: GEM GIPT 2026-09 projects announced + pre-construction + construction (MW); a documented lower bound for the candidate potential, not a resource assessment", v, "MW", "B",
                    "GEM Global Integrated Power Tracker 2026-09", f"Status in (announced, pre-construction, construction); Type {cls if cls != 'PHS' else 'hydropower / Technology pumped storage'}", gipt_sha, country=c, status="REFERENCE_ONLY")
                rows.append(dict(country=c, tech=cls, kind="gem_pipeline", value_mw=v, grade="B", status="REFERENCE_ONLY", source="GEM GIPT 2026-09", locator="announced+pre-construction+construction"))

    # --- 4. comparison with the model p_nom_max by country ---------------------------------------------------------------
    pn = json.loads(PNOM.read_text()); gen = pn["generators_gw"]; sto = pn["storage_gw"]
    cmp_rows = []
    def model_gw(c, tech):
        if tech == "offwind":
            return float(np.nansum([gen.get("offwind-ac", {}).get(c, np.nan), gen.get("offwind-dc", {}).get(c, np.nan)]))
        if tech in ("hydro", "PHS"):
            return float(sto.get(tech, {}).get(c, 0.0) or 0.0)
        if tech in ("nuclear",):
            return np.inf if c != "SG" else 0.0
        if tech == "wind":
            return float(np.nansum([gen.get("onwind", {}).get(c, np.nan), gen.get("offwind-ac", {}).get(c, np.nan), gen.get("offwind-dc", {}).get(c, np.nan)]))
        v = gen.get(tech, {}).get(c, np.nan); return float(v) if v is not None else np.nan
    best = {}   # best public figure per (country, tech): CANDIDATE_ONLY first, then REFERENCE_ONLY of kind technical/potential
    for r in rows:
        if r["status"] in ("CANDIDATE_ONLY",) or (r["status"] == "REFERENCE_ONLY" and r["kind"] in ("pdp8_technical", "doe_wb_roadmap_technical", "crez_zones", "esdm_2023", "myrer", "aeo8_potential")):
            k = (r["country"], r["tech"]);
            if k not in best or (best[k]["status"] != "CANDIDATE_ONLY" and r["status"] == "CANDIDATE_ONLY"):
                best[k] = r
    for (c, tech), r in sorted(best.items()):
        if c in ("SEA", "ALL"):
            continue
        mg = model_gw(c, tech)
        cmp_rows.append(dict(country=c, tech=tech, model_p_nom_max_gw=round(mg, 2) if np.isfinite(mg) else "inf", public_potential_gw=round(r["value_mw"] / 1e3, 2), kind=r["kind"], grade=r["grade"], status=r["status"],
                             ratio_model_over_public=(round(mg * 1e3 / r["value_mw"], 2) if np.isfinite(mg) and r["value_mw"] else ("inf" if not np.isfinite(mg) else np.nan)), source=r["source"]))
    cmp_df = pd.DataFrame(cmp_rows); cmp_df.to_csv(PV / "CANDIDATE_POTENTIAL_VS_MODEL_BY_COUNTRY.csv", index=False)
    pd.DataFrame(rows).to_csv(PV / "CANDIDATE_POTENTIAL_SOURCES.csv", index=False)

    # --- 5. candidate cost consistency (decisions 46 / 50 / 52) -------------------------------------------------------
    act = pd.read_csv(a.costs, index_col=0); prep = pd.read_csv(PREPARED, index_col=0)
    fx = 0.877228632573   # ECB 2020 EUR/USD used by the AEO8 layer (LAYER_B_AEO8_AUTHOR_RULE_2050.csv last column)
    cost_rows = []
    for tech, rule in [("nuclear", "TD v0.15.0 2050 EUR2020 (decision 50)"), ("hydro", "TD v0.15.0 (decision 50)"), ("ror", "TD v0.15.0 (decision 50)"), ("PHS", "TD v0.15.0 (decision 50)"), ("onwind", "TD v0.15.0 (decision 50)"), ("offwind", "TD v0.15.0 (decision 50)"), ("solar", "TD v0.15.0 (decision 50)"),
                       ("nuclear SMR", "AEO8 D.15 Nuclear SMR 9,600 kUSD/MW x FX (decision 46, grade C)"), ("geothermal", "AEO8 D.15 Geothermal average 4,100 kUSD/MW x FX (decision 52, grade C)")]:
        inv = float(act.at[tech, "investment"]); fixed = float(act.at[tech, "fixed"]); mc = float(act.at[tech, "marginal_cost"]); life = float(act.at[tech, "lifetime"]); fom = float(act.at[tech, "FOM"])
        if tech == "nuclear SMR":
            expected = 9600.0 * 1e3 * fx; ok = abs(inv - expected) < 1.0
        elif tech == "geothermal":
            expected = 4100.0 * 1e3 * fx; ok = abs(inv - expected) < 1.0
        else:
            expected = float(prep.at[tech, "investment"]); ok = abs(inv - expected) < 1e-6 * max(1.0, expected) and abs(fixed - float(prep.at[tech, "fixed"])) < 1e-6 * max(1.0, fixed)
        cost_rows.append(dict(technology=tech, rule=rule, investment_eur_per_mw=round(inv, 2), expected_eur_per_mw=round(expected, 2), consistent=bool(ok), fom_pct=round(fom, 4), lifetime_a=life, fixed_eur_per_mw_a=round(fixed, 2), marginal_cost_eur_per_mwh=round(mc, 4)))
    cost_df = pd.DataFrame(cost_rows); cost_df.to_csv(PV / "CANDIDATE_COST_CONSISTENCY.csv", index=False)
    assert cost_df.consistent.all(), cost_df[~cost_df.consistent]
    add("cand_cost_consistency_check", "Candidate technology costs in the active layer equal their decision sources: nuclear/hydro/ror/PHS/onwind/offwind/solar = technology-data v0.15.0 2050 EUR2020 prepared table (decision 50); nuclear SMR = AEO8 D.15 9,600 kUSD/MW x 0.877228632573 (decision 46); geothermal = AEO8 D.15 Geothermal average 4,100 kUSD/MW x FX (decision 52); all 9 rows consistent",
        9, "rows", "A", "results_project/.../costs_active_research.csv vs costs_2050_EUR2020_prepared.csv and LAYER_B_AEO8_AUTHOR_RULE_2050.csv", str(a.costs.relative_to(ROOT)) if a.costs.is_relative_to(ROOT) else str(a.costs), sha256(a.costs), status="REFERENCE_ONLY")

    # --- write ---------------------------------------------------------------------------------------------------------
    frag = REG_DIR / "fragments" / "potentials_s4a.csv"; reg.write(frag)
    ev = dict(script=SCRIPT, accessed=ACCESSED, documents=DOCS, web_quotes_sha256=QSHA, gipt_sha256=gipt_sha, rows=len(reg.rows), status_counts=pd.Series([r["status"] for r in reg.rows]).value_counts().to_dict(),
              model_p_nom_max_source=str(PNOM.relative_to(ROOT)), comparison=cmp_rows, cost_consistency=cost_rows, pipeline_mw=pv.to_dict(),
              files={p.name: sha256(p) for p in sorted(PV.glob("*")) if p.is_file()})
    write_json(ev, PV / "POTENTIALS_S4A_EVIDENCE.json")
    print(json.dumps(dict(rows=len(reg.rows), status=ev["status_counts"], comparison=len(cmp_rows), costs_consistent=bool(cost_df.consistent.all())), indent=1))
    print(cmp_df.to_string())


if __name__ == "__main__":
    main()
