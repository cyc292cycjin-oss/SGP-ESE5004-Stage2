
### S4R 补充 01（第 129 项：审阅修正）— 2026-10-20

- **范围：** `S4R_SUPPLEMENT_01.md`（SHA256 c533c960…4984，核对一致）；同一分支、同一 draft PR #43；仍只读（未求解、未连云、未调用 Gurobi、未改生产代码与注册表）。
- **R1.3 产量：** 11 国严格同一规则 2050 = min(基年 × G^((2050−基年)/28 × ε), 人均饱和 × 人口, 国家规划上限)，规划只作上限；基年改为 2024（worldsteel WSIF 2025；USGS MCS 2025 仅列 ID / VN，其余 USGS 年鉴 DATA_PENDING，过渡值标注）；ε = 0.5 与饱和 1.0 / 0.6 t/人登记为假设（C 级，敏感性 0.3–0.8、0.6–1.2 / 0.4–0.8；文献只给饱和证据：Bleischwitz 2018、van Ruijven 2016、Pauliuk 2013）。VN 水泥 107.0 Mt（人均上限绑定）、钢 40.7 Mt（增长规则；原 70 Mt 把规划当下限，撤销）；11 国水泥 1,290 → 410、钢 152 → 97 Mt。
- **R1 电力锚：** 只锚活动量——基础负荷 = ATS 国家电力（C.8 × D.1）× 归一化部门权重中的建筑 + 农业及其他份额（权重 = 2019 部门电力 × ATS 部门增长代理）；11 国 1,032 → 966 TWh（VN 184、ID 311、TH 170），全部非负；居民电力校验 428 vs AEO8 ATS 386 TWh（+11 %）；工业电力内生不锚定（M08-5 原"ATS 电力 − 路线电力"撤销）；交通锚服务量（模型交通终端能耗为 ATS 锚的 1.1–3.2×）。
- **R2：** 主算只改光伏密度 4.6 → 5.1（上限 × 1.109，按比例缩放，不重算栅格）；开阔林 121–126 作上界敏感性，触发规则：修正后 365×24h 某国光伏上限绑定且影子价格 × 绑定容量 ≥ 1 bn 则升级。比值 0.18–0.57 的分解：密度参数占对数差 6–18 %，保护区口径上界 17–84 %，林地与其他判据 ≥ 33–71 %（世行 WDI 保护区 / 森林占比）——口径与 PyPSA-Eur 同型，非输入错误。作者缓存已有 Copernicus LC100 全球文件、natura（WDPA 2020 栅格）、GEBCO 2025、EEZ v11；下载清单分为主算必需（航运密度栅格 535 MB、USGS 年鉴水泥表、worldsteel 2024 SG / MM、UN WPP TL、Eurostat HICP）与仅敏感性。
- **R8：** 保持 k = 10，`GATES_V6.md` 不改；新建 `GATES_V6_NOTES.md`：barrier 无 crossover 时 56×3h 优化成功运行的对偶符号误差 ≈ 40–240 × BarConvTol，365×24h 解约 1e-2 量级；D2 为诊断，不影响验收。
- **R7 补充：** VN 封存上限 236 → 106 Mt/a 后约 130 Mt/a 改走区域内船运（到 MY，+14–15 EUR/t，两情景各 +1.9–2.0 bn/a）；不互联情景 VN 船运升至约 225 Mt/a（约 2/3 封存量经海运）；若船运算互联则不互联 +5.5 bn/a。作面谈议题 (b) 依据。
- **清单：** 面谈 9 项；用户待办 2 项（下载清单、注册表行 42 行）。影响合并区间放宽为 B6 ≈ 25–50 bn，VN 份额 55–70 %。
- **交付：** 更新 `S4R_PLAN.md`、`DEMAND_ANCHOR_COMPARISON.*`、`POTENTIAL_COMPARISON.*`、`IMPLEMENTATION_PLAN.md`、`USER_DOWNLOAD_LIST.md`、`REGISTRY_ROWS_PROPOSED.csv`、`UNIFICATION_CHECKLIST.*`、`EXTERNAL_SOURCES_S4R.md`、`S4R_EVIDENCE.json`、`S4R_PROGRESS.md`；新建 `GATES_V6_NOTES.md`；提交见进度文件"收尾记录（补充 01）"。
