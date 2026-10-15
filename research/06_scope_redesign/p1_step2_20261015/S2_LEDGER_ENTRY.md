## S2 CO₂、生物质、需求 — 2026-10-15

- **范围：** S2-0（补充指令 01 数据补齐）与 S2-1 至 S2-7 在本机完成；没有正式求解（第 47 项）。分支 `codex/s2-co2-biomass-demand-20261015`（自 D1 8f977156），draft PR 叠在 D1 的 PR #22 之上。所有网络标注 `S2_SECTOR_COUPLED_SMOKE`；冒烟 `SMOKE_TEST_ONLY`；诊断 `GAP_DIAGNOSTIC_NOT_FOR_INTERCONNECTION_VALUE`。
- **S2-0（f0ad4070、f64e1fd0）：** technology-data v0.15.0 层（EUR2025 → EUR2020，ECB EA20 GDP 平减 0.833196；海底 HVDC +121%、铀 +82%、FT 单位重构）；城市垃圾有机部分改走沼气（IPCC 2006 产率，湿基，约 303 PJ）；EDGAR 2025 过程排放（2.A/2.C 入过程母线，2.B/2.D/4.C 归原料碳口径）；四国海运舱燃料 0（A 级）；伐木残余主算 0（ZERO_BY_DECISION），高生物质敏感性与 7 国木材加工残余推导；registry 937 行（A 204 / B 471 / C 262），DATA_PENDING 98 → 22。
- **S2-1：** 主算成本层切换到 v0.15.0（燃料价按第 33 项取 WEO 2025 NZE：气 13.67、油 11.62、煤 5.17 EUR2020/MWh）；SMR 启用（AEO8 C 级，11 国）；存量地热 186 MW 并入（GEM 3 台 2021/2022 投运，30 年寿命；9 台无投运年份 DATA_PENDING）；lvopt（2.79 倍为敏感性）；B6 按第 48 项；`gap_diagnostic` 模式（全部国家电力 + CO₂ 松弛，惩罚 10,000 EUR/MWh、10,000 EUR/t，默认关闭）。
- **S2-2：** 每节点 `co2 stored` 缓冲 + 每国 `co2 sequestered {ISO2}`（上限 = 潜力/50，8 国；LA/MM/SG 不建）；109 条 CO₂ 管道（19 条跨境受开关控制）；CCGT CC、SMR CC、BECCS、工业生物质 CC、过程排放 CC、DAC（电供热 COP 1）；第 20 项分国核算用跨境封存算例验证（TH → MY 13.7 Mt/168 h，TH 记减排、MY 只占上限）。
- **S2-3：** 每国固体生物质/沼气母线，107 个品类 Store（2,120.7 TWh/a），发电(+CC)/工业(+CC)/沼气提纯/BtL 全部内生；360 TWh 全区池配置删除。
- **S2-4/5：** D1 需求表 → 1,906 个 Load，归属表唯一绑定；EV 1,175.9 TWh、Astar 交通用电扣除 11.08 TWh（SG 7.26）；铁路燃油计量（U2）、航空国内/国际（开关）、工业聚合载体（U1）+ 20% 低温热母线（97 个，5 种供给）、原料碳按 PyPSA-Eur 口径（方法问题待确认）、清洁炊事（第 23 项）、农业；航运 670 TWh 推迟到 S3。
- **S2-6：** V5 新增 B2、B3、B8、B11；B1 覆盖全部排放端口（2,949 个）。
- **S2-7：** 两情景 2920×3h 与 365×24h 构建通过静态校验（峰值 RSS 0.58 GiB）；56×3h HiGHS 冒烟**两情景均不可行**。原因（未放宽约束）：① SG、VN 固定生物质终端需求超过本国固体生物质潜力（0.18 vs 0.03；208 vs 125.8 TWh/a）；② MM 无封存潜力且无跨境 CO₂ 管道（两情景）；③ 不互联下 LA/SG 无封存、KH/VN 封存上限不足（需 34.0 vs 1.7；598 vs 236 Mt/a）。`gap_diagnostic` 第 1 轮（仅电力 + CO₂ 松弛）仍不可行，第 2 轮加生物质松弛后最优：不互联 CO₂ 缺口（168 h）VN 7.79、SG 2.16、TH 2.02、ID 1.54、KH 0.83、MM 0.62、LA 0.24 Mt；一体化只剩 MM 0.62 与 VN 4.17 Mt（后者为截断时域资本成本放大的经济性缺口，结构上可行）。截断时域未缩放目标函数权重是诊断的已知局限，修正方案 PROPOSED。
- **待用户决定：** 原料碳口径（PyPSA-Eur 全量最终排放 vs EDGAR 2.B）；SG/VN 生物质需求与潜力冲突的处理；VN 2050 工业煤 962 TWh 的需求链核对；诊断运行的目标函数权重缩放；B11 对 3 个无负荷辅助节点气母线的判定；地热不凝气 CO₂ 忽略。
- **交付：** `research/06_scope_redesign/p1_step2_20261015/`（S2_REPORT.md、S2_0_DATA_TOPUP.md、S2_PROGRESS.md、S2_EVIDENCE.json、S2_TEST_RUN.json、CLOUD_RESOURCE_ESTIMATE.md §6、evidence/）；测试 364 通过 / 4 失败（基线即失败的 gate4 旧测试）。
