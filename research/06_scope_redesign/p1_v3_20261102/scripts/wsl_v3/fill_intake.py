"""Fill the file table of V3_DATA_INTAKE.md from INTAKE_FILES_SHA256.csv and copy small evidence tables."""
import csv, shutil
from pathlib import Path
MAIN = Path("/home/jin/research/SGP_ESE5004_Stage2/phase2/research_model"); P1 = MAIN / "results_project/v3/phase1"
D = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102"); E = D / "evidence"; E.mkdir(parents=True, exist_ok=True)
S = {"225_ewg": "APEC Energy Statistics 2022：21 经济体，2022、2021 两年平衡表（表为图片）", "2564_": "泰国 EPPO 能源统计 2021（泰文）", "Background_eor": "越南 EOR 技术报告 2024", "EBT 2022": "马来西亚能源平衡表 2022", "content-handbook": "印尼 HEESI 2025", "energy_consumption_sector": "DOSM 马来西亚分部门能耗 1980–2024",
     "myb3-2017-18": "USGS 亚太卷 2017–18", "myb3-2020-21-thailand": "USGS 泰国卷", "myb3-2022-philippines": "USGS 菲律宾卷", "myb3-2022-vietnam": "USGS 越南卷", "myb3-2023-indonesia": "USGS 印尼卷", "INDOPAC_GIS.gdb": "USGS 印太 GIS 地理库", "INDOPAC_GIS.png": "GIS 图", "INDOPAC_GIS_metadata": "GIS 元数据",
     "SI_INDOPAC_GIS_Data-Level_LayerPackages": "分层图层包（未用）", "SI_INDOPAC_GIS_Data-Level_Metadata": "分层元数据", "gem-download (1)": "GEM 水泥（含不用的 Ownership Tracker）", "gem-download.zip": "GEM 钢铁（含不用的 Ownership Tracker）", "DOSE_V2.11": "DOSE 省级产出", "DoseV2p11": "DOSE V2.11 变更说明", "README-ramp-cooking": "RAMP 炊事说明（不用）",
     "README-ramp-ev": "RAMP EV 说明", "ramp-cooking": "RAMP 炊事曲线（不用）", "ramp-ev-consumption": "RAMP EV 电池消耗曲线", "ramp-ev-plugin": "RAMP EV 接入率曲线", "airport-comments": "OurAirports（不用）", "airport-frequencies": "OurAirports 频率", "airports.csv": "OurAirports 机场表", "countries.csv": "OurAirports 国家（不用）", "navaids": "OurAirports（不用）", "regions.csv": "OurAirports 地区", "runways": "OurAirports 跑道"}
rows = list(csv.DictReader(open(P1 / "INTAKE_FILES_SHA256.csv", encoding="utf-8")))
L = ["| 文件 | 大小 B | SHA256 | 内容 |", "|---|---:|---|---|"]
for r in rows:
    name = r["path"]; d = next((v for k, v in S.items() if k in name), "")
    assert d, name
    L.append(f"| `{name}` | {int(r['bytes']):,} | `{r['sha256']}` | {d} |")
f = D / "V3_DATA_INTAKE.md"; t = f.read_text(encoding="utf-8")
assert "<!--FILETABLE-->" in t
f.write_text(t.replace("<!--FILETABLE-->", "\n".join(L)), encoding="utf-8")
for n in ("INTAKE_FILES_SHA256.csv", "V2_CROSS_BORDER_STOCK.csv", "V2_NETWORK_FACTS.json", "V2_SOLVED_LIQUIDS.json", "GEM_CEMENT_ASEAN_SUMMARY.csv", "GEM_STEEL_ASEAN_SUMMARY.csv", "DOSE_ASEAN_COVERAGE.csv", "ASEAN_AIRPORTS_SCHEDULED_V3.csv", "ID_NODE_TIMEZONE_PROPOSAL.csv"):
    shutil.copy(P1 / n, E / n)
print(len(rows), "rows ok")
