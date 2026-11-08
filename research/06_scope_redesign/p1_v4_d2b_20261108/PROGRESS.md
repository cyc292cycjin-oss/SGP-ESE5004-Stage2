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
| D2b-5 | 第 5 节：重建 56 时段网络与静态检查 | 未开始 | |
| D2b-6 | 第 6 节：报警线登记后 2 次冒烟 | 未开始 | |
| D2b-7 | 第 7 节：W19 候选刷新（不求解） | 未开始 | |
| D2b-8 | 第 8 节：报告、证据、审阅包、推送 | 未开始 | |

续做点：D2b-2（文献子代理 4 个在跑：树干、其余农残、第 4 节 A / B 组；证据 JSON 在会话 scratchpad `lit/`，完成后复制到 `evidence/`）。

已做（未提交）：
- 代码：`v4_common`（`biomass_potential` 新取值 `v4_adjusted_t05` = 新主集，t04 保留；新开关键 `source_band_basis: post_product | s30`，`source_band_shares()`，阈值 1 MWh）、`v4_outputs.write_tables`（产品后重算三带份额，s3_0 值记入 `V4_SWITCHES.json`）、`v4_industry.s7`（t05 文件）、`v4_biomass_potential`（`basis_factors("t05")` 读 `BIOMASS_BASIS_T05.csv`，`low_rule` basis / scale；`main()` 另写 T05 两表）、`baseline.yaml`（两键）。
- 测试：`tests/research/test_v4_d2b_band.py`（规则单元、开关、主集表 = 规则、s30 目录保留 s3_0 份额）；A2 回退测试通过（`logs/ut_a2_pre.txt`）。
- 探针（`scripts/band_probe.sh`，`logs/band_probe.txt`）：t04 潜力 + 新带份额，只有三带份额列变化；VN 高温带 0.1544 → 0.1428，LA 1 → 0.368，MY 1 → 0.425，TH 0.1259 → 0.1123，PH 0.2994 → 0.2741，MM 0.5564 → 0.4921；ID / KH 不变；BN 为 3.5e-8 MWh 尘埃（加 1 MWh 阈值后保留 s3_0）。
- 树干链条核算（`tables/TRUNK_CHAIN_CHECK.csv`，`scripts/d2b_trunk_chain.py`）：每翻种公顷 280 t（140 × 2 t），每收获公顷每年 11.2 t；每吨 FFB 0.65（ID）/ 0.61（MY）/ 0.62（TH）t（收获上限前），上限 0.25 后 0.162 / 0.152 / 0.155 t。
- 脚本：sync / ut / commit / run_registry / regen_tables / build / 参照引擎与检查点 / 重排（D2a 副本改路径），`d2b_basis_table.py` 骨架。
