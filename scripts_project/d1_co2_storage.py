"""D1 section 1: CO2 geological storage potential and annual injection caps (decisions 28-30).

Main values follow the D1 instruction: ERIA (2024) P50 storage resource for MY, ID, BN, TH
(saline P50 + oil & gas fields net, both from ERIA Chapter 1 tables); PH from IEA (2021)
(ADB 2013 data); VN from IEA (2021)/ADB (2013); KH and TL from OGCI CO2 Storage Resource
Catalogue cycle 5 (2025); LA, MM, SG = 0 (no assessed resource). Low/high are the minimum
and maximum national totals reported across the three/four sources captured in
work/p2_data_intake/extraction/CO2_STORAGE_EXTRACTION.md and CO2_STORAGE_OGCI_EXTRACTION.md.
Annual injection cap = potential / 50 years (decision 28).
"""
from __future__ import annotations

import re

from d1_common import ASEAN, REG_DIR, SRC_DIR, Registry, src_sha, write_json

SCRIPT = "scripts_project/d1_co2_storage.py"
GT_TO_T = 1e9
YEARS = 50.0


def raw_shas():
    """name -> sha256 from the intake SHA256SUMS files copied to sources/."""
    out = {}
    for name in ["SHA256SUMS.txt", "SHA256SUMS_raw2.txt", "SHA256SUMS_raw3.txt", "SHA256SUMS_raw4.txt"]:
        for line in (SRC_DIR / name).read_text(encoding="utf-8").splitlines():
            m = re.match(r"([0-9a-f]{64})\s+\*?(.+)$", line.strip())
            if m:
                out[m.group(2).strip().split("/")[-1]] = m.group(1)
    return out


# Document identities (raw PDFs are read-only in work/p2_data_intake/raw)
ERIA = "ERIA (2024) Ch.1 Geological Storage Potential of CO2 in Southeast Asia"
IEA = "IEA (2021) CCUS: The Opportunity in Southeast Asia"
ADB = "ADB (2013) Prospects for Carbon Capture and Storage in Southeast Asia"
OGCI = "OGCI/CSRC Cycle 5 (2025) Appendix B Asia"
ERIA_PDF = "1_Chapter-1-Geological-Storage-Potential-of-CO2-in-Southeast_Asia.pdf"
IEA_PDF = "CarbonCaptureUtilisationandStorage_TheOpportunityinSoutheastAsia.pdf"
ADB_PDF = "carbon-capture-storage-southeast-asia.pdf"
OGCI_PDF = "CSRC_Cycle_5_Appendix_B_Asia-_August_2025.pdf"
EXT = "CO2_STORAGE_EXTRACTION.md"
EXT_OGCI = "CO2_STORAGE_OGCI_EXTRACTION.md"

# country: dict(main components [(label, Gt, source, locator)], low (Gt, source, locator), high (...))
TABLE = {
    "ID": dict(
        main=[("saline P50", 49.0, ERIA, "Table 1.6 p.23 (Kutei 35, East Java 8, Central Sumatra 6)"),
              ("oil and gas fields net", 2.275, ERIA, "Tables 1.4-1.5 p.21-22 (12 basins)")],
        low=(8.4, IEA, "p.35 table (South Sumatra 7.65 + Java 0.386 + Tarakan 0.130 + Central Sumatra 0.229)"),
        high=(75.0 + 2.275, ERIA, "Table 1.6 P10 saline 75 + O&G net 2.275; note ERIA Table 1.6 header P10/P90 appears reversed, P50 unaffected"),
    ),
    "MY": dict(
        main=[("saline P50", 127.0, ERIA, "Table 1.9 p.26 (Malay 83 + Sarawak 44; Sabah not assessed)"),
              ("oil and gas fields net", 1.773, ERIA, "Table 1.7 p.26")],
        low=(80.0, IEA, "p.35 table (Malay Basin 80)"),
        high=(197.0 + 1.773, ERIA, "Table 1.9 P10 saline 197 + O&G net 1.773"),
    ),
    "BN": dict(
        main=[("saline P50", 18.0, ERIA, "Table 1.12 p.35 (Baram Delta P90 13 / P50 18 / P10 25)"),
              ("oil and gas fields net", 0.5793, ERIA, "Table 1.10 p.35 (Baram Delta net 579.3 Mt)")],
        low=(0.558, OGCI, "aggregated BN 0.558 Gt (CO2_STORAGE_OGCI_EXTRACTION.md)"),
        high=(25.0 + 0.5793, ERIA, "Table 1.12 P10 saline 25 + O&G net 0.5793"),
    ),
    "TH": dict(
        main=[("saline P50", 15.0, ERIA, "Table 1.14 p.40 (Pattani 13 + Malay-Thailand 2)"),
              ("oil and gas fields net", 1.024, ERIA, "Table 1.13 p.40")],
        low=(10.0, ADB, "Appendix 3 p.99: saline 8.9 + oil and gas 1.3 = about 10 Gt theoretical"),
        high=(22.0 + 1.024, ERIA, "Table 1.14 P10 saline 22 + O&G net 1.024"),
    ),
    "PH": dict(
        main=[("saline (theoretical, Cagayan + Central Luzon)", 22.0, IEA, "p.35 table (from ADB 2013)"),
              ("gas fields (effective)", 0.3, IEA, "p.35 table (from ADB 2013)")],
        low=(0.0672, ERIA, "Table 1.18 p.53: North Palawan O&G net 67.2 Mt only; no saline data"),
        high=(23.318, OGCI, "aggregated PH 23.318 Gt"),
    ),
    "VN": dict(
        main=[("deep saline (theoretical)", 10.4, IEA, "p.35 table (ADB 2013 Figure 4.2, efficiency factor 0.001)"),
              ("depleted oil and gas fields", 1.4, IEA, "p.35 table (ADB 2013)")],
        low=(5.0 + 0.3034, ERIA, "Table 1.17 p.47 saline P50 5 (Cuu Long Bach Ho) + Table 1.15 O&G net 0.3034"),
        high=(21.75, OGCI, "aggregated VN 21.75 Gt"),
    ),
    "KH": dict(
        main=[("undiscovered saline (text: about 85 Mt)", 0.085, OGCI, "KH text: ~85 Mt saline undiscovered; ERIA p.56: no analysis completed")],
        low=(0.0, ERIA, "p.56 storage potential unknown, no analysis completed; Table 1.19 Panjang = Possible"),
        high=(0.132, OGCI, "aggregated KH 0.132 Gt (sub-commercial 0.047 + undiscovered 0.085)"),
    ),
    "TL": dict(
        main=[("OGCI aggregated", 0.250, OGCI, "aggregated TL 0.250 Gt")],
        low=(0.0, ERIA, "no Timor-Leste country analysis; Figure 1.2 Viqueque = Possible, Bonaparte = Highly suitable (map reading only)"),
        high=(0.250, OGCI, "aggregated TL 0.250 Gt"),
    ),
    "LA": dict(main=[("unassessed", 0.0, ERIA, "p.56: storage potential unknown as no analysis has been completed; Table 1.19 Greater Korat = Suitable, no estimate; OGCI 0")],
               low=(0.0, ERIA, "p.56"), high=None),
    "MM": dict(main=[("unassessed", 0.0, ERIA, "p.56: no analysis completed; Table 1.19 Central Myanmar = Possible, no estimate; OGCI 0")],
               low=(0.0, ERIA, "p.56"), high=None),
    "SG": dict(main=[("no storage potential", 0.0, ERIA, "p.56: geology indicates no storage potential; IEA p.32: no known geological storage resources; OGCI 0")],
               low=(0.0, ERIA, "p.56"), high=(0.0, IEA, "p.32")),
}

SOURCE_PDF = {ERIA: ERIA_PDF, IEA: IEA_PDF, ADB: ADB_PDF, OGCI: OGCI_PDF}


def main():
    shas = raw_shas()
    ext_sha = src_sha(EXT)
    ogci_sha = src_sha(EXT_OGCI)
    reg = Registry(SCRIPT)
    summary = {}
    for c in ASEAN:
        t = TABLE[c]
        main_gt = sum(v for _, v, _, _ in t["main"])
        for label, v, src, loc in t["main"]:
            key = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
            pdf = SOURCE_PDF[src]
            reg.add(f"co2_storage_component_{c}_{key}", f"{c} CO2 storage component: {label}", v, "GtCO2",
                    "A", f"{src}; extraction {EXT}/{EXT_OGCI}", loc,
                    f"{pdf}:{shas.get(pdf, 'NA')}; extraction:{ext_sha if src != OGCI else ogci_sha}",
                    country=c, decision_ref="28,29,30",
                    status="REGISTERED" if v > 0 else "SOURCE_ZERO")
        low = t["low"][0] if t["low"] else None
        high = t["high"][0] if t["high"] else None
        main_src = "; ".join(sorted({s for _, _, s, _ in t["main"]}))
        reg.add(f"co2_storage_potential_{c}", f"{c} national CO2 storage potential, main value (sum of registered components)",
                main_gt, "GtCO2", "B" if len(t["main"]) > 1 else "A", main_src,
                "sum of co2_storage_component_* rows; low = " + (f"{t['low'][1]}: {t['low'][2]}" if t["low"] else "n/a")
                + "; high = " + (f"{t['high'][1]}: {t['high'][2]}" if t["high"] else "n/a (unassessed, DATA_PENDING)"),
                ext_sha, country=c, sensitivity_low=low, sensitivity_high=high, decision_ref="28,29,30",
                status="REGISTERED" if main_gt > 0 else "SOURCE_ZERO")
        reg.add(f"co2_injection_cap_{c}", f"{c} annual CO2 injection cap = potential / {YEARS:g} years",
                main_gt * GT_TO_T / YEARS, "tCO2/a", "B", "derived from co2_storage_potential_" + c,
                f"potential_Gt x 1e9 / {YEARS:g}", ext_sha, country=c,
                sensitivity_low=None if low is None else low * GT_TO_T / YEARS,
                sensitivity_high=None if high is None else high * GT_TO_T / YEARS,
                decision_ref="28", status="REGISTERED" if main_gt > 0 else "SOURCE_ZERO")
        summary[c] = dict(main_gt=main_gt, low_gt=low, high_gt=high, cap_t_per_year=main_gt * GT_TO_T / YEARS)
    for c in ["LA", "MM"]:
        reg.add(f"co2_storage_potential_unassessed_{c}", f"{c}: no published storage estimate in ERIA/IEA/ADB/OGCI; "
                "treated as 0 (decision 30) until a national assessment is downloaded", None, "GtCO2", "C",
                ERIA, "p.56; Table 1.19", f"{ERIA_PDF}:{shas.get(ERIA_PDF, 'NA')}", country=c,
                decision_ref="30", status="DATA_PENDING")
    # Reference: transport & storage cost from the only source that reports national values
    reg.add("co2_ts_cost_reference_ID_2011USD", "ADB 2013 natural-gas-processing CCS transport+storage reference: "
            "pipeline 11 + injection well 6 USD2011/tCO2 (150 km onshore pipeline assumption); not a model input",
            17.0, "USD2011/tCO2", "A", ADB, "Appendix 1 p.87 (PDF 122); Figure 6.4 p.52",
            f"{ADB_PDF}:{shas.get(ADB_PDF, 'NA')}", country="ID", decision_ref="11", status="REFERENCE_ONLY")
    out = reg.write(REG_DIR / "fragments" / "co2_storage.csv")
    write_json(dict(script=SCRIPT, summary=summary, rows=len(reg.rows)), REG_DIR / "fragments" / "co2_storage.json")
    print(out, len(reg.rows), "rows")
    for c, s in summary.items():
        print(f"  {c}: main {s['main_gt']:.3f} Gt (low {s['low_gt']}, high {s['high_gt']}) cap {s['cap_t_per_year']:.3e} t/a")


if __name__ == "__main__":
    main()
