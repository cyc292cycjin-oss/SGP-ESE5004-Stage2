"""S4F-1 data (decision 96): registry fragment s4f_1 - PyPSA-Eur individual line / link extension limit (configuration lines and code location
checked against the in-repo copies of PyPSA-Eur v2025.07.0), the switch research.network.max_extension and the APG / AIMS plan caps of the
apg_plans sensitivity (research_inputs/corridors/APG_PLAN_CAPS_S4F1.csv).

    python scripts_project/s4f_1_data.py

APG plan cap rule (apg_plans): per APG AIMS III project with a planned or projected capacity, plan cap = the larger of total_MW (existing +
ongoing + future; upper end of a range; '600/TBC' -> 600) and aims3_2040_projection_MW (#16 also carries #5 Batam - Singapore 3,400 MW, merged
into #16 by the APG table); the group = every line / DC link joining the two areas of the project (node-name prefixes); the constraint caps the
group total at max(2025 stock of the group, plan cap). Projects with no number (TBC: #8a Sarawak - Brunei; the other initiatives SG-VN, SG-KH)
are not capped beyond the PyPSA-Eur rule.
"""
from __future__ import annotations

import re

import pandas as pd

from d1_common import REG_DIR, ROOT, SRC_DIR, Registry, sha256, write_csv

SCRIPT = "scripts_project/s4f_1_data.py"
INSTRUCTION_SHA = "28d7458d47e282df6aaf5fa324e3772b886a67f9b178dd728696c5eac7216f03"
LOC = "work/p1_step4f_20261017/S4F_CLAUDE_CODE_INSTRUCTION.md"
SRC = "S4F instruction S4F-1 (user decisions 2026-10-17 14:43 SGT and the S4F-1 reply of 2026-10-17)"
CONF = SRC_DIR / "pypsa_eur_v2025.07.0_config.default.yaml"
PSN = SRC_DIR / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
APG = SRC_DIR / "APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv"
OUT = ROOT / "research_inputs/corridors/APG_PLAN_CAPS_S4F1.csv"
# APG project -> the two areas (node-name prefixes of the geographical buses); kind
AREAS = {"1": ("MY_Peninsular", "SG"), "2": ("TH", "MY_Peninsular"), "3": ("MY_Sarawak", "MY_Peninsular"), "4": ("MY_Peninsular", "ID_Sumatra"),
         "6": ("MY_Sarawak", "ID_Kalimantan"), "7": ("PH", "MY_Sabah"), "8a": ("MY_Sarawak", "BN"), "8b": ("MY_Sarawak", "MY_Sabah"), "9": ("TH", "LA"),
         "10": ("LA", "VN"), "11": ("TH", "MM"), "12": ("VN", "KH"), "13": ("LA", "KH"), "14": ("TH", "KH"), "15": ("MY_Sabah", "ID_Kalimantan"),
         "16": ("SG", "ID_Sumatra"), "17": ("LA", "MM"), "18a": ("ID_Kalimantan", "ID_Java"), "18b": ("ID_Sumatra", "ID_Java")}
MERGED = {"16": "5"}   # the APG table merges #5 Batam - Singapore into #16


def check_line(path, lineno, text):
    line = path.read_text().splitlines()[lineno - 1]
    if text not in line:
        raise ValueError(f"{path.name} line {lineno} does not hold {text!r}: {line!r}")
    return line.strip()


def upper(v: str):
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", str(v).replace(",", ""))]
    return max(nums) if nums else None


def plan_caps() -> pd.DataFrame:
    apg = pd.read_csv(APG, dtype=str, keep_default_na=False).set_index("apg_no")
    rows = []
    for no, (a, b) in AREAS.items():
        r = apg.loc[no]
        tot, proj = upper(r.total_MW), upper(r.aims3_2040_projection_MW)
        extra = upper(apg.loc[MERGED[no], "total_MW"]) if no in MERGED else None
        vals = {k: v for k, v in [("total_MW", tot), ("aims3_2040_projection_MW", proj), (f"merged #{MERGED.get(no)} total_MW", extra)] if v is not None}
        if not vals:
            continue
        key = max(vals, key=vals.get)
        rows.append(dict(apg_no=no, project=r.connection, area_a=a, area_b=b, kind=("domestic" if r.country_a == r.country_b else "cross_border"),
                         total_mw=r.total_MW, aims3_2040_projection_mw=r.aims3_2040_projection_MW, merged=(f"#{MERGED[no]} total {extra:.0f}" if extra else ""),
                         plan_cap_mw=vals[key], plan_basis=f"{key} = {vals[key]:.0f} (larger of the published figures)"))
    return pd.DataFrame(rows)


def main():
    c324 = check_line(CONF, 324, "max_extension: 20000"); c340 = check_line(CONF, 340, "max_extension: 30000")
    check_line(CONF, 313, "lines:"); check_line(CONF, 336, "links:")
    p5573 = check_line(PSN, 5573, "def limit_individual_line_extension(n, maxext):")
    p5575 = check_line(PSN, 5575, 'n.lines["s_nom_max"] = n.lines["s_nom"] + maxext')
    p5576 = check_line(PSN, 5576, 'hvdc = n.links.index[n.links.carrier == "DC"]')
    p5577 = check_line(PSN, 5577, 'n.links.loc[hvdc, "p_nom_max"] = n.links.loc[hvdc, "p_nom"] + maxext')
    p6415 = check_line(PSN, 6415, 'maxext = snakemake.params["lines"]["max_extension"]')
    for ln, txt in [(912, 'carrier="CO2 pipeline"'), (2007, 'carrier="gas pipeline new"'), (2052, 'carrier="H2 pipeline"'), (2030, 'carrier="H2 pipeline retrofitted"')]:
        check_line(PSN, ln, txt)
    if "links\"][\"max_extension\"]" in PSN.read_text() or "links.max_extension" in PSN.read_text():
        raise ValueError("prepare_sector_network.py reads links.max_extension - re-check decision 96")
    caps = plan_caps(); write_csv(caps.to_dict("records"), OUT, list(caps.columns))
    csha, psha = sha256(CONF), sha256(PSN)
    reg = Registry(SCRIPT)
    reg.add("pypsa_eur_lines_max_extension", "Decision 96: PyPSA-Eur v2025.07.0 individual extension limit per line and per DC link (MW above the existing capacity): config "
            f"'{c324}' (config.default.yaml line 324), read by prepare_sector_network.py line 6415 ('{p6415}') and applied by limit_individual_line_extension "
            f"(line 5573): '{p5575}' for every line, '{p5577}' for every link of carrier DC ('{p5576}'). One value for AC and DC; increment, not total",
            20000.0, "MW", "B", "PyPSA-Eur v2025.07.0 config.default.yaml; scripts/prepare_sector_network.py", "config line 324; prepare_sector_network.py 5573-5577, 6415-6417",
            csha, decision_ref="96")
    reg.add("pypsa_eur_links_max_extension", f"Decision 96 (reference only): PyPSA-Eur v2025.07.0 config '{c340}' (line 340) is not read by prepare_sector_network.py (the sector "
            "workflow applies lines.max_extension to DC links too); not used (user decision 2026-10-17)", 30000.0, "MW", "B", "PyPSA-Eur v2025.07.0 config.default.yaml",
            "config line 340", csha, decision_ref="96", status="REFERENCE_ONLY")
    reg.add("s4f1_pipeline_extension_caps", "Decision 96 item 2: PyPSA-Eur v2025.07.0 sets no individual extension cap on new H2 pipelines (H2_network, p_nom_extendable without "
            "p_nom_max), CO2 pipelines (add_co2_network, lines 854-913) or new gas pipelines (gas_network_connectivity_upgrade); existing gas pipes are not extendable "
            "(p_nom_max = p_nom with H2_retrofit, a retrofit limit). No pipeline cap is set in the model", "none", "flag", "B", "PyPSA-Eur v2025.07.0 scripts/prepare_sector_network.py",
            "add_co2_network 854-913; gas_network 1902-1936; new gas pipes 1986-2008; H2 retrofit 2011-2031; H2_network 2034-2053", psha, decision_ref="96",
            status="REFERENCE_ONLY")
    reg.add("s4f1_max_extension_switch", "Decision 96: research.network.max_extension = pypsa_eur (main: s_nom_max = s_nom + 20000 for every line, p_nom_max = p_nom + 20000 for "
            "every DC link; both scenarios, cross-border and domestic, stock and candidates) | none (former state, comparison) | apg_plans (conservative sensitivity, build "
            "check only: pypsa_eur caps + one constraint per APG project group, research_apg_corridor_cap hook)", "pypsa_eur|none|apg_plans", "flag", "B", SRC, LOC, INSTRUCTION_SHA,
            decision_ref="96", status="REFERENCE_ONLY")
    reg.add("s4f1_apg_plan_caps", f"Decision 96 sensitivity apg_plans: {len(caps)} APG AIMS III projects with a planned / projected capacity; plan cap = larger of total_MW "
            "(upper end of a range) and aims3_2040_projection_MW (#16 incl. merged #5 3,400 MW); group = lines / DC links joining the two areas; constraint: group total <= "
            "max(group 2025 stock, plan cap); TBC projects (#8a) and the other initiatives keep the PyPSA-Eur rule", "table", "flag", "C",
            "ACE (2024) APG Interconnections Project Profiles Table 1 (APG_AIMS3_PRIORITY_INTERCONNECTIONS_2024.csv)", "research_inputs/corridors/APG_PLAN_CAPS_S4F1.csv",
            sha256(OUT), decision_ref="96,94", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4f_1.csv")
    print(caps.to_string())


if __name__ == "__main__":
    main()
