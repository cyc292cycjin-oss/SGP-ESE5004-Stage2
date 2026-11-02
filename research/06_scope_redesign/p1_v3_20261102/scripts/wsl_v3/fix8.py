from pathlib import Path
f = Path("/home/jin/wt_v3_20261102/research/06_scope_redesign/p1_v3_20261102/V3_DATA_INTAKE.md"); t = f.read_text(encoding="utf-8")
add = """
## 12. 阶段 2 补记（2026-11-02）

### 12.1 APEC 表两次独立读取（D163-1 附）

用到的 APEC 数只有 VN，表在 PDF 第 161 页（书页 148），`p161_0_Image20.png`。

| 项 | 结果 |
|---|---|
| 第一次读取 | 原图，读合计列 |
| 第二次读取 | 裁剪工业部分放大 2 倍，读全部载体列 |
| 合计列 | 两次完全一致 |
| 子部门行合计 | 1,541.3 PJ，印刷工业合计 1,542 PJ |
| 列合计 | 煤 687.7 / 687、油 152.3 / 152、气 41.0 / 41、其他可再生 215 / 214、电 447.2 / 448（读数 / 印刷） |
| 行内合计 | 与印刷总计差 ≤ 1 PJ（四舍五入） |

矩阵见 `research_inputs/industry_v3/APEC2022_VN_INDUSTRY_PJ.csv`。

### 12.2 Wei et al. 2020（D163-2）

MDPI 对 curl 返回 403，改用内置浏览器读取。

| 项 | 值 |
|---|---|
| 文献 | Wei et al., Energies 13(21):5664，CC BY 3.0 |
| PDF | 1,312,606 B，SHA256 `8695d6c485b6c9e17d3cb575c636250e8925035c9aa82aa80ff9e5e106640d36`（浏览器内取得字节后计算） |
| 本地 PDF | **未能落盘**（浏览器下载未保存），只保留 SHA256 与表 8 摘录 `research_inputs/industry_v3/NICKEL_ENERGY_WEI2020.csv` |

### 12.3 船速来源（D161-2）

查 technology-data 条目所引原文献，均未取得：Runge et al. 2020（SSRN，人机验证页，未绕过）；Cihlar et al. 2020（欧盟出版局，Azure WAF 拦截）。按决定用 15 节 / 8,000 h（C 级）。

### 12.4 其他输入

| 文件 | 内容 |
|---|---|
| `pypsa-asean/data/temp_hard_coded/transport_data.csv` | PyPSA-Earth 各国车辆数，东盟合计约 2.65 亿，只作车队代理的量级对照 |
| `research_inputs/corridors/CORRIDOR_APG_CROSSCHECK_2024.csv` | APG existing，存量核查基准 |
| iScience 2025 SI Table S8、PNAS Nexus SI Table S4 | 存量核查对照 |

USGS 亚太卷表 3 第一栏核对：列为氧化铝、铝土矿、原铝，MY 原铝 750 kt（估计），解决第 2 节"列位待核"。
"""
assert "## 12." not in t
f.write_text(t.rstrip() + "\n" + add, encoding="utf-8")
g = Path("/home/jin/v3/commit.sh"); s = g.read_text()
a = "git add -f research_inputs/industry_v3 research_inputs/transport_v3 2>/dev/null || true"
assert a in s
s = s.replace(a, "git add -f research_inputs/industry_v3 research_inputs/transport_v3 research_inputs/liquids_v3 research_inputs/registry_v5/fragments/v3.csv 2>/dev/null || true")
b = "grep -E 'registry_v5/(DATA_REGISTRY|DATA_PENDING|fragments/v3)'"
assert b in s
s = s.replace(b, "grep -E 'registry_v5/(DATA_REGISTRY|DATA_PENDING|D1_EVIDENCE)'")
g.write_text(s)
