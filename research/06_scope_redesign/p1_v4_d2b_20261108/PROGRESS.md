# D2b 进度（V4_D2B_INSTRUCTION.md v1，SHA256 bdd67b0fcdf809914d8e53dbc24037dd19eaed4251c2afd22699f6959fbf303c 已核对，与 V4_D2B_SHA256.txt 一致；开工 2026-11-09 00:00 SGT）

- 执行：Claude Code，模型 Opus 5.5（`claude-opus-5-5`，开工时确认）；effort 由会话设定，本会话无法自查是否为 Xhigh（报告中注明）。
- 分支 `codex/v4-d2b-20261108`，起点 `385bdff08e932afef79755be5b1af7ebb2839350` = `codex/v4-d2a-20261107` 头（fetch 核过，本地 = 远端）；`15533817` 是其祖先，二者之间只改了 `research/06_scope_redesign/p1_v4_d2a_20261107/` 下 3 个文件（PROGRESS.md、REPORT.md、evidence/REVIEW_ZIP_MANIFEST_15533817.txt），交付目录之外 0 个。
- worktree `/home/jin/wt_v4_d2b`；临时目录 `/home/jin/v4d2b`；主检出 `results_project/v4d2b/`（构建与冒烟输出，不入库）。
- 交付目录 `work/p1_v4_d2b_20261108/` = 仓库 `research/06_scope_redesign/p1_v4_d2b_20261108/`（zip 不入库）。
- 求解额度：至多 2 次（第 6 节）；已用 0 / 2。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| D2b-1 | 第 1 节：分支、worktree、祖先核实 | 完成 | （随 D2b-2 提交） |
| D2b-2 | 第 2 节：生物质能量基准全面核对、新主集潜力 `v4_adjusted_t05`、S7 检查点 | 完成：树干判"不一致"（IRENA 2 t/株 = 鲜重；每翻种公顷 280 t 对文献树干鲜重约 205 / 干重 37–42 t DM；每 t FFB 0.65 对 0.43 鲜 / 0.086 干）→ 干物质 × 干基 LHV，系数 0.3135（含水 0.708、LHV_dry 16.12），区间 0.147–0.375；EFB / 纤维沿用 T04；稻、玉米、甘蔗、木材加工、PKS、两类沼气判一致保留；木薯、椰子、其他作物判"无法判定"保留 + 区间交审阅端；东盟固体潜力 1,448.09 → 1,289.32 TWh；检查点 main_t05 16 步 / iid_t05 15 步对 T05 参照逐国 0 差；`BIOMASS_BASIS_AUDIT.csv`、`tables/BIOMASS_T05_CHANGE_BY_COUNTRY_CATEGORY.csv` | 与 D2b-3 / D2b-4 同一提交（见下） |
| D2b-3 | 第 3 节：F-02 旁注（source_band 份额按产品后生物质） | 完成：开关键 `source_band_basis: post_product`（主集）/ `s30`；VN 高温带 0.1544 → 0.1428 等；`test_v4_d2b_band.py` | 同上 |
| D2b-4 | 第 4 节：文献可得的数据升级 | 完成：LNG 再气化替换 1.26 → 2.0507 EUR2020/MWh（开关键 `lng_regas_adder: asean_tariffs`）；CO₂ 船运、EV / ICE、封存潜力、MY 屋顶、VN 海风系数（0.896，0.849–1.042，不应用）只登记区间；封存价格年推断 2020；WACC 只写说明；`DATA_UPGRADES.csv`；注册表 2,436 → 2,463 行（+27 新行、49 行区间整行替换） | 同上 |
| D2b-5 | 第 5 节：重建 56 时段网络与静态检查 | 完成：前两次构建失败（`s3_layers` NameError → D2b-5a `5571cb19`；燃料价断言读配置加价 → D2b-5b `c7178a6b`），第三次构建（`c7178a6b`）一体化 `6f027c26…`、`no_new_xb` `7bf008dd…`；C1–C6、C10–C12 通过；C8 对 D2a 两网两分辨率差异全部在事先登记的 (a) 树干池 5 个 / (b) LNG 边际成本 16 台 / (c) VN 溢出有用热负荷 24 个，无 UNEXPECTED；零松弛门两网通过；F-05 网络台账测试在 D2b 构建上通过 | 哈希刷新 D2b-4b `f6b0c28c`；修正 `5571cb19`、`c7178a6b`；结果随 D2b-5/6a 提交 |
| D2b-6 | 第 6 节：报警线登记后 2 次冒烟 | 完成：登记（报警线 R1 +10,006.63 M、R2 +9,436.56 M EUR）后求解 2 / 2 次；两次 optimal、ACCEPTED_LAYER2、C1 a/b/c 接受、失败门 = D2a（并集内）；ΔV +11,478.3 / +11,988.5 M EUR，高于报警线；56 时段 B6 12.8414 bn（D2a 12.3311） | 登记 `0b02cfe8`（D2b-5/6a，求解前）；结果 D2b-6b |
| D2b-7 | 第 7 节：W19 候选刷新（不求解） | 完成：D2a 重排脚本（方法不变）+ 本分支注册表区间（37 对刷新，其中 D2b 新增 27 对）+ 清单覆盖 2 行（VN 海风 alpha −15.1 % / +4.2 %、封存价格年 0.952–1.0）；缓存只读复用 D2a `cache/`；276 行排序，前 30 与 D2a 重合 29、Spearman 0.9995；EV 能效 5 → 2、LNG 6 → 4、海风 alpha 2 → 5（方向翻转）、ID 树干 10 → 22；`W19_CANDIDATES_D2B.csv` 27 项（19 项标 changed_by_d2b） | 与 D2b-6b 同一提交（交付目录整体同步） |
| D2b-8 | 第 8 节：报告、证据、审阅包、推送 | 完成：`REPORT.md`（第 0 节结论 9 条 + 待决 10 条）、`LEDGER_ENTRY_DRAFT.md`、`EVIDENCE.json`（30 条）、`DOWNLOAD_CANDIDATES.csv`（19 条）；全量 `tests/research` 868 过 / 3 败 / 56 跳过（补齐被忽略的 WACC 输入后 870 过 / 1 既有失败）；审阅包、泄露扫描与推送见 D2b-8b | D2b-8（本行所在提交）、D2b-8b |

续做点：D2b-2（文献子代理 4 个在跑：树干、其余农残、第 4 节 A / B 组；证据 JSON 在会话 scratchpad `lit/`，完成后复制到 `evidence/`）。

已做（未提交）：
- 代码：`v4_common`（`biomass_potential` 新取值 `v4_adjusted_t05` = 新主集，t04 保留；新开关键 `source_band_basis: post_product | s30`，`source_band_shares()`，阈值 1 MWh）、`v4_outputs.write_tables`（产品后重算三带份额，s3_0 值记入 `V4_SWITCHES.json`）、`v4_industry.s7`（t05 文件）、`v4_biomass_potential`（`basis_factors("t05")` 读 `BIOMASS_BASIS_T05.csv`，`low_rule` basis / scale；`main()` 另写 T05 两表）、`baseline.yaml`（两键）。
- 测试：`tests/research/test_v4_d2b_band.py`（规则单元、开关、主集表 = 规则、s30 目录保留 s3_0 份额）；A2 回退测试通过（`logs/ut_a2_pre.txt`）。
- 探针（`scripts/band_probe.sh`，`logs/band_probe.txt`）：t04 潜力 + 新带份额，只有三带份额列变化；VN 高温带 0.1544 → 0.1428，LA 1 → 0.368，MY 1 → 0.425，TH 0.1259 → 0.1123，PH 0.2994 → 0.2741，MM 0.5564 → 0.4921；ID / KH 不变；BN 为 3.5e-8 MWh 尘埃（加 1 MWh 阈值后保留 s3_0）。
- 树干链条核算（`tables/TRUNK_CHAIN_CHECK.csv`，`scripts/d2b_trunk_chain.py`）：每翻种公顷 280 t（140 × 2 t），每收获公顷每年 11.2 t；每吨 FFB 0.65（ID）/ 0.61（MY）/ 0.62（TH）t（收获上限前），上限 0.25 后 0.162 / 0.152 / 0.155 t。
- 脚本：sync / ut / commit / run_registry / regen_tables / build / 参照引擎与检查点 / 重排（D2a 副本改路径），`d2b_basis_table.py` 骨架。
