# v4 W08 独立审查：独立阶段发现表（FINDINGS_PRE；台账 W14 前置）

- **指令：** `V4_FABLE_W08_INSTRUCTION.md` v1，SHA256 `046beb55…c186`，`APPENDIX_REVIEWER_214.md` SHA256 `0290dc28…2569`，均与 `V4_FABLE_W08_SHA256.txt` 一致（2026-11-07 开工前核对）。
- **对象：** `codex/v4-w08-20261106` 头提交 `7aa356e49d284749d27c79fbdc75ade85f62866a`（含 `bd890bf9`，含起点 `aad8e476`；远端同头），相对 `aad8e476` 的全部改动（190 个文件；`scripts_project` 6 个修改 + 10 个新模块，10 个新测试文件，`research_inputs` 新输入与 `out_ras` / `out_iid` 表，注册表 +69 行）。
- **执行：** 模型 Claude Fable 5.1；分支 `codex/v4-fable-w08-20261107`，worktree `/home/jin/wt_v4_fable`（从 `7aa356e4` 新开）；所有运行在仓库外的临时副本 `/home/jin/v4fable/`（`repo/`、`a2/`、`tests_copy/`，共 ≈ 0.6 GB）中完成；**求解器 0 次**；不连 HPC；不下载数据；仓库中的代码、输入、配置、注册表与网络未改动；本分支只写 `work/p1_v4_fable_w08_20261107/` 的镜像目录。
- **独立性声明（必须披露）：** 开工核对 SHA256 时，我用同一条 `cat` 命令把 `APPENDIX_REVIEWER_214.md` 全文一并打印了出来，违反了"只在第 4 节读取"的要求。该内容无法撤回；本文件第 1–3 节的全部判断只依据规格、代码、输入与我自己的复现运行形成，每条发现都附可独立复现的证据（脚本 + JSON）。W08 的 `REPORT.md`、`SMOKE56_V4.md`、`HPC_V4_PLAN_DRAFT.md` 在本文件提交前未读。另外，会话自动加载的记忆索引中含一行 W08 实施会话的摘要（冒烟成本差等数字），同样未用于本文件的判断。
- **等级：** VERIFIED（读到的文件、回执）、EXACT（逐项可复现的计算）、INFERENCE（机制解释、估计）、PROPOSED（建议）。严重度：S1 致命 / S2 重要（某国或东盟量偏差 ≥ 1 TWh 或违反已确认决策）/ S3 次要 / S4 建议。

## 0. 结论摘要

1. **没有 S1。** 开关全关时，`m08b_demand.py` 与 `s3_0_industry.py` 默认运行写出的 **全部 56 个文件**（不只是规格的 8 个）与 v3.1 `d3b9a3bc` 逐字节相同（A2，自己跑，`evidence/a2_compare.txt`）；主算与 IId 的 S7 检查点在干净副本中复现，11 国 `T_v2`、"其他"、12 个载体、溢出、上限、陆运与 EV 与 `REFERENCE_V4_MAIN.csv` / `REFERENCE_V4_IID.csv` 的最大差 5e-10 TWh（A0）；`out_ras` / `out_iid` 共 24 个表重生成后逐字节相同（可复现、确定性）。
2. **2 条 S2。** (F-01) 决策 211 第 2 条写"ID 造纸行燃料木材 41.59 TWh 按自产残渣移出"，W08 实际移出的是 2010–2017 年均 74.88 TWh 的 2019 年造纸行份额 76.4 %（57.21 TWh），平衡表外 (b) 项只剩 17.67 TWh；按字面读法（74.88 − 41.59 = 33.29 TWh）ID 2050 年 `T_v2` **+36.89 TWh**（EXACT，主算与 IId 相同）。两种读法都是推断，需审阅端定夺。(F-02) 表中与参照表报告的 VN 生物质溢出（主算 29.95、IId 20.93 TWh）是 s3_0 在产品 2050 向量加入**之前**算的；网络对守恒层之后的全部 `T_v2` 生物质施加 0.99 上限，实际溢出 **41.10 / 32.07 TWh**，差 11.15 TWh 恰等于 VN 纸浆造纸的外购生物质 2050 向量。`T_v2`、"其他"、潜力与网络本身不受影响，但报告量错误。
3. **5 条 S3、11 条 S4**（第 1 节）。规格第 1–10 节与指令第 0 节两处修改逐项核对：除 F-01 的读法问题与几处有记录的实现位置偏离（第 1 节 F-13）外全部实现一致；各步东盟 `T_v2` 增量与规格中 I2 的数值逐项相符（IId 参照）。
4. **可复现与一致性全部通过：** 从 UNSD SDMX 原始 XML 用自写解析器手算 21 条数据链（ID / VN / TH / MY / KH；煤、燃料木材、柴油、汽油、天然气、残渣、蔗渣、电），与 `SDMX_INDUSTRY_CELLS_2019.csv`、`D1_BASE2019_SDMX.csv`、`HOUSEHOLD_GASOLINE_2019.csv`、`out_ras` ATS 表（2050 = 基数 × 倍数）全部一致（最大差 1e-8 MWh）；注册表 67 个文件行 SHA256 与字节数全部一致、`d1_registry.py` 重组后 `DATA_REGISTRY.csv` 逐字节相同、无删除或改动的原有行；许可字符串扫描无 IEA / Calliope 命中；已构建 2920×3h 网络（主算与 IId）的工业电、四个热负荷、煤 / 氢 / 氨 / 甲醇负荷、EV、铁路、过程排放输入、气上限、逸散因子、生物质池与表一致（≤ 1e-6 MWh），铁路父行 0，曲线年电量不变、各曲线均值精确为 1、连续流程平线、UTC+7 与 UTC+8 曲线相差整 1 小时，365×24h 网络是 3h 网络的日均聚合。
5. **建议：** 可以进入打包前的收尾，但先（a）由审阅端裁定 F-01 的读法并写入决策清单，（b）把 F-02 的溢出量改在守恒层之后计算并补一条"网络溢出 = 表溢出"的测试，（c）处理第 1 节的 S3。详见第 3 节建议。

## 1. 发现表

| 编号 | 维度 | 严重度 | 结论 | 证据 | 影响量 | 建议修改 |
|---|---|---|---|---|---|---|
| F-01 | 1 规格符合性 / 4 守恒 | **S2** | 决策 211 第 2 条（指令第 0 节第 2 条）写"ID 造纸行燃料木材 41.59 TWh（SDMX，16,389 千 m³）按自产残渣 (a) 移出需求与潜力，(b) 项相应只剩非造纸部分"。W08 的实现：缓存中丢掉 1214G 行的燃料木材并把其余燃料木材按 74.88 / 54.43 = 1.3755 放大（`v4_industry_cache.py:112-116, 119-127`），(b) 项 = 74.88 × 非造纸份额 0.2360 = 17.67 TWh（`v4_industry.py:535-536`，`share_non_paper` = 12.85 / 54.43）。即从 2010–2017 年均中移出的是 57.21 TWh（= 76.4 % × 74.88），不是决策文字中的 41.59 TWh。字面读法：(b) = 74.88 − 41.59 = 33.29 TWh。两种读法都把 2019 年的造纸份额外推到 2010–2017 年均，谁更合理没有数据可判（2010–2017 年没有分行）。 | SDMX ID 5110：121 = 21,451.48 千 m³（54.433 TWh）、1214G = 16,388.58 千 m³（41.586 TWh），因子 9.135 GJ/m³（`evidence/CHAIN_CHECK.json` 第 2、3 链）；`FUELWOOD_OUTSIDE_BALANCE.csv` 29,510 千 m³ → 74.880 TWh；`scripts/sens_paper_fuelwood.py` 用仓库 `run_case` 在副本中跑两种读法 → `evidence/SENS_PAPER_FUELWOOD.json` | **EXACT：** ID 2050 `T_v2` 主算 1,483.78 → 1,520.67（+36.89 TWh），IId 1,326.86 → 1,363.75（+36.89）；"其他" +36.89；东盟同量；生物质潜力 0（树皮不在潜力表） | 审阅端裁定读法并写入决策清单；把读法做成开关值（`id_paper_fuelwood: residue_share | residue_literal | purchased`），落选读法作敏感性登记；`V4_SWITCHES.json` 与报告中写明实际移出量 57.21 TWh |
| F-02 | 4 守恒 / 6 网络层 | **S2** | VN 生物质溢出：`INDUSTRY_2050_SUMMARY_V4.csv`（`biomass_overflow_industry_mwh`）、`SNAPSHOT.json`、`REFERENCE_V4_*.csv`、`CHECKPOINTS` 中的溢出是 `s3_0_industry.py:383-387` 对**s3_0 自己的链生物质**（主算 137.49 TWh）算的；守恒层随后加入产品 2050 向量（VN 纸浆造纸外购生物质 11.146 TWh，`PRODUCT_ITEMS_V4.csv` S5d VN `v2050_biomass_mwh`）并把 `pe_biomass_mwh` 覆写为 148.64 TWh（`v4_outputs.py:173-176`），但溢出列未重算。网络（`s2_layers.py:914-921`）对 148.64 + 农业 11.62 施加 0.99 × 120.37 = 119.16 的上限 → 溢出 41.10 TWh（IId：138.20 + 13.04 − 119.16 = 32.07）。参照引擎与仓库同一定义，所以 A0 / A1 的"0 差"不能发现它。v3.1 中两者一致（无产品向量）。 | `evidence/NET_CHECK_main.json` / `NET_CHECK_iid.json` 的 `biomass_overflow_ledger.VN`（`overflow_industry_mwh` 41,097,220 / 32,073,768）；表值 29,951,239 / 20,927,788；差 11,145,980 = VN pulp_paper `v2050_biomass_mwh`（EXACT 相等） | **EXACT：** VN 溢出报告值低 11.15 TWh（主算 29.95 → 41.10；IId 20.93 → 32.07）；对应有用热负荷（效率 0.9）36.99 / 28.87 TWh 而非表意味的 26.96 / 18.83；`T_v2`、"其他"、潜力、网络 LP 不变（网络以自身计算为准） | 在 `v4_outputs.write_tables` 中用守恒层后的生物质重算溢出与 `pe_biomass_mwh` 后的列（或改 `s3_0 --only-mode` 为输出"溢出前"量并把溢出算在层后）；`REFERENCE_V4_*.csv`、`SNAPSHOT.json`、W08 / I2 报告中的"VN 溢出 20.9 / 29.95"改为网络值；增加测试"网络溢出台账 = 表溢出" |
| F-03 | 3 单位 / 8 数据版本 | S3 | F3（蔗渣 R2）与 F4c（蔗渣自用份额）用 W12 的 UNdata **导出**表（TH 产量 46,878、工业终端消费 22,534 千 t），需求侧用 UNSD SDMX **当前库**（TH 产量 51,674、消费 24,839、1214F 24,806 千 t，高 10.2 %）。份额完全相同（0.4807），F4c 不受影响；但 R2 对齐"每吨甘蔗能量与 UNSD 2019"用的是导出量，两侧数据版本不一致。 | `evidence/CHAIN_CHECK.json`（TH 5120 1214F 24,806 千 t）；本次 XML 探查：TH 5120 交易 01 = 51,674、12 / 121 = 24,839、08 = 26,835；`W12_UNSD_BAGASSE_2019.csv` TH 行 | **INFERENCE：** 若 F3 / F4c 改用 SDMX 量，TH 蔗渣部分能量 +10 %，潜力变动量级 ≤ 5 TWh（方向取决于 R2 的定义，未重算） | W12 的两张蔗渣表改由 SDMX 胶囊重生成（同一数据版本）；或在注册表注明版本差异 |
| F-04 | 4 守恒（残渣两侧对称） | S3 | 需求侧移出的自产残渣按工业倍数增长（2019 × m），潜力侧的 F4 扣减按作物增长并以 UNSD 份额或厂内假设为依据：TH 需求侧 78.33 → 179.35 TWh（2050）对潜力侧 −49.31；VN 33.74 对 −4.27；ID 192.18（不扣锚）对 −195.37（全部来自油棕纤维 100 % / PKS 50 % 假设，与 UNSD 记录无关）；MY 0.02 对 −73.81。不是重复计算（两侧都移出），但两侧增长基准与证据来源不同；VN 潜力中的蔗渣部分（IRENA 基础 5.41 TWh，15 GJ/t）小于 UNSD 2019 已记录的工业蔗渣消费 11.67 TWh。 | `evidence/CONSERVATION_CHECK.json` `residue_symmetry`；`BIOMASS_POTENTIAL_ADJ_V4.csv`；`W12_BAGASSE_SUPPLY_OVERESTIMATE.csv` VN `bagasse_mwh_15` 5,406,666 | **INFERENCE：** 不改变 B6 模型量（两侧均在模型外）；VN 甘蔗潜力相对 UNSD 低估 ≥ 6 TWh（v3 既有） | 报告中并列两侧数字与各自依据；VN 蔗渣潜力按 UNSD 产量校核（W10 / 数据到位后） |
| F-05 | 8 测试质量 | S3 | 测试缺口：(i) 无"网络溢出 = 表溢出"的测试（能发现 F-02）；(ii) `v4_outputs.process_and_feedstock`（过程排放 × v4 倍数、BN 2.A.1 = 0 路径、原料碳重算）无任何测试；(iii) `v4_common.v4_tables` 对开关 SHA 不符的拒绝无测试；(iv) A2 测试只比 8 个文件（默认运行实际写 56 个，本审查全部核对一致）；(v) 对照类测试（`test_v4_captive / products / transport_accounts / industry_cache / profiles(weights)`）以 W08 自己改写的 I2 引擎输出为参照，属"与同源参照一致"，不是独立参照。性质类测试（守恒、回退、残渣扣减性质、IId = v3 锚、曲线均值与电量、注册表 SHA、配置哈希）是实在的。 | `tests/research/test_v4_*.py`（本次通读）；`grep -ln "rerun v4_industry|process_and_feedstock|PROCESS_EMISSIONS" tests/research/test_v4_*.py` 为空 | — | 补 (i)–(iii)；A2 测试改为比对默认运行写出的全部文件 |
| F-06 | 7 注册表 | S3 | `v4_pks_in_mill_share` 登记 tier C，描述写"I2 central assumption (grade D)"，等级不一致；`v4_biomass_overflow_cap_share` 的 `source_sha256` 是整个 `configs/research/baseline.yaml` 的 SHA（任何配置改动都会失效，且 `test_v4_registry` 不校验非 `file:` 定位的行）；m08b 残渣重拟合的收敛记录（迭代数、行 / 列误差）只在 W08 工作目录的 m08b 证据 JSON 中，`out_<mode>/` 没有复制。 | `fragments/v4_w08.csv`；`v4_registry.py:82-86`；`v4_outputs.py:162-165` 只复制 4 张 m08b 表 + C3 偏离表 | — | tier 改 D 或描述改 C；上限份额的定位改为 `file: configs/research/baseline.yaml` 并由测试校验；把 `DEMAND_ANCHOR_M08B_EVIDENCE.json` 复制进 `out_<mode>/` |
| F-07 | 1 规格 / 4 守恒 | S3 | BN 甲醇能源用途从 NEU 气扣减：规格要求"2019 3.45 / 2050 × 增长"；`v4_outputs.bn_neu_methanol` 只改 `value_2050_mwh`（5.736 → 1.712 TWh，扣 4.024），`base_2019_mwh`（5.459 TWh）未扣 3.452。网络只用 2050 值，无模型影响；但 2050 扣减用产品增长 1.166（GDP 规则），NEU 行自身倍数 1.051，表内 2019 / 2050 口径不一致。 | `evidence/CONSERVATION_CHECK.json` `bn_neu_gas_rows`；`v4_outputs.py:106-116` | 模型 0；表内 2019 NEU 列高 3.45 TWh | 同步改 2019 基数并在 `growth_method` 注明两种倍数 |
| F-08 | 1 规格（文档数字） | S4 | 规格第 4 节写 ID 家庭汽油"S5p 196.94 TWh"；实际 SDMX 基年 16,011.611 千 t × 44.3 GJ/t / 3.6 = 197.032 TWh（d207 模式对所有质量行用 SDMX 因子；196.94 对应冻结因子 0.0123 TWh/kt）。W08 实现正确，规格数字过时。 | `CHAIN_CHECK.json` 第 5 链；`HOUSEHOLD_GASOLINE_2019.csv` | 2050 ID 交通 ≈ +0.26 TWh（相对规格数字），`T_v2` 0 | 规格 / 报告中改写 |
| F-09 | 4 守恒（表的一致性） | S4 | `INDUSTRY_2050_SUMMARY_V4.csv` 只覆写了 12 个 `pe_*_mwh` 载体列（守恒层合计）；`bas_*`、`other_*`、`other_mechanical_*`、`biomass_overflow_*`、`td_*` 等列仍是 s3_0 对自身链的结果，与覆写后的列不同源。构建只读 `pe_*` 与 `biomass_source_band_*_share`（本次核对），无模型影响；读表的人会混用。 | `v4_outputs.py:167-182`；`s2_layers.py` 对 summary 列的读取（`grep` 本次） | 0 | 文档注明或删除 / 重算未覆写列 |
| F-10 | 2 回退 | S4 | 开关全关时唯一执行到的 v4 路径是 `s3_layers.py:88-91`（`v4_tables` 返回 None 后仍写入 `led["production_caps_table"]`）与 `s2_layers.land_transport_accounts`（返回原集合）；v3.1 回退网络的 meta 多一个键 `production_caps_table`，配置哈希因新键而不同（B12 设计如此）。数值层面：第 2.2 节的开关全关构建与 v3.1 包网络 10 类组件逐值相同（VERIFIED）。 | `git diff aad8e476 7aa356e4 -- scripts_project/s3_layers.py`；`evidence/OFF_BUILD_VS_V31.json` | 0 | 可接受；文档注明 |
| F-11 | 2 回退 / 1 规格 | S4 | `research.demand.anchor_mode` 在 `v4.enabled: false` 时被读取但无效（`v4_common.switches` 直接取 V31 集），用户设 `anchor_mode: iid` 而不开 v4 会静默得到 v3.1 表。 | `v4_common.py:49-62` | 0 | `enabled: false` 且 `anchor_mode != ras` 时报错或警告 |
| F-12 | 6 网络层 | S4 | `v4_profiles.Shapes.shape_3h` 只接受 8760 或 2920 个快照；365×24h 网络由 3h 网络日均聚合得到（本次核对两条负荷逐日相等、年电量相等），所以现在没有问题；直接按其他分辨率构建会抛错。 | `v4_profiles.py:118-129`；本次探查 `_checks3.sh` 输出 | 0 | 允许任意整除 8760 的分辨率（按时长平均） |
| F-13 | 1 规格（实现位置偏离，可接受） | S4 | 规格第 1 节要求改 `reconstruct_base_accounts.Reconstruction.convert`、`d1_demand_2050.py` 与 `FROZEN_UPSTREAM_CONVERSIONS.json`；W08 保持 v3.1 模块与冻结文件不动，改为 `v4_base_sdmx.Recon` 子类 + `SDMX_DICTIONARY_EXTENSION.json`（有记录）。规格第 8 节的 `test_v4_gas_caps.py` 并入 `test_v4_biomass_potential.py`。这些偏离使 A2 更稳，没有数值影响。 | `v4_base_sdmx.py:9-11, 269-294`；`SDMX_DICTIONARY_EXTENSION.json` | 0 | 文档注明即可 |
| F-14 | 4 守恒 | S4 | s3_0 的上限 `solid_pot` 对潜力表所有非 biogas 行求和，网络只装载 status 非 DATA_PENDING / ZERO_BY_DECISION 的行：MY 差 793 MWh、BN 856、SG 473、TL 664（v3.1 既有）。 | `NET_CHECK_main.json` `biomass_pools` | ≤ 0.001 TWh | s3_0 同样过滤 status |
| F-15 | 6 网络层 / 5 锚 | S4 | (b) 项 ID 平衡表外燃料木材在 ATS 表的 `base_2019_mwh` 是"虚拟基数"（17.67 × 2.6186 / 3.2034 = 14.45 TWh）而非真值（规格允许，真值在 SNAPSHOT `ind19_true`）；s3_0 的 2019 可用量与 2019 份额由此低估 3.2 TWh，本次没有产品从 ID 生物质行扣减，无影响。 | `v4_industry.py:380-386, 431` | 0 | 文档注明 |
| F-16 | 4 守恒（HVC / NEU） | S4 | HVC 2019 扣 5.191 MWh/t（燃料 4.918 从化工行按燃料结构、电 0.272），2050 向量 (b) 4.627（电 2.454、低温热 0.182、甲烷 1.819、氢 0.173）均不含原料；原料留在 NEU 行并按工业倍数增长（DFX F1.2），而 HVC 产量按装置增长（ID ×1.82、MY ×1.78 含新装置）：能源用途与原料的增长基准不同，是 v3 既有设计，不是 W08 的重复或遗漏。 | `v4_products.py:39-43, 115-130`；`PRODUCT_ITEMS_V4.csv` | 0 | 记录在 HPC 计划的口径说明中 |
| F-17 | 3 单位 | S4（无问题，记录） | 21 条数据链全部一致：TN（UNIT_MULT 3 → 千 t）× SDMX 因子（或 ID 例外 20.29 / 28.20）× 1000 / 3.6；M3 × 9.135 × 1000 / 3.6；TJ / 0.0036（天然气 TJ GCV × 0.9，`reconstruct_base_accounts.convert`，与供给侧 `v4_gas_caps` 的 0.9 / 0.0036 一致）；GWh × 1000。VN 电力在 SDMX 中已是 GWh（111,934.11）。2050 = 基数 × 倍数（≤ 6e-8 MWh）。 | `evidence/CHAIN_CHECK.json` | — | — |
| F-18 | 5 锚构造 | S4（无问题，记录） | RAS 容差 1e-10 相对、最多 1000 次（`m08b_demand.py:71`）。`out_ras`：各国行和 = AEO8 TFEC − R_c × m_c（残差 ≤ 0.09 MWh），非工业列和 = C.3 × k（偏差 0），工业列 −252.14 TWh = Σ R_c m_c（LA、MM、MY、PH、TH、VN）；`out_iid`：行和同样精确，`tfa_cs /(seed_s σ_s)` 在每国的非工业部门为常数（IId 定义成立）；v3 RAS 解秩一（σ_s 与国别无关，比值 1.000000000）；IIb / external 的实现与文档一致，external 为接口桩（测试：用冻结表喂 external = ras 输出）。 | `evidence/ANCHOR_PROFILE_CHECK.json` | — | — |
| F-19 | 6 网络层 | S4（无问题，记录） | G5 曲线 584 条、均值与 1 的最大偏差 6.7e-16、最小值 0.139、无负值；MAIN 中连续流程为平线（钢、水泥、氨、镍、原铝、HVC、甲醇、纸浆等共用一条平线）；非平线曲线 UTC+7 与 UTC+8 相差整 1 小时（残差 ≤ 1.9e-3）；ID 三个时区按子部门节点份额分配（`INDUSTRY_CURVE_WEIGHTS_V4.csv`）；网络中 95 条工业电负荷与 4 × 95 条热负荷全部带曲线，年电量与静态 p_set × 8760 相对差 0；峰均比 电 1.08–1.24、热 1.04–1.05。 | `ANCHOR_PROFILE_CHECK.json` `profiles` / `zone_shift_check`；`NET_CHECK_main.json` `curves` | — | — |

## 2. 量化（S1 / S2）

| 编号 | 量 | 国家 | 2050 `T_v2` | "其他" | 生物质潜力 | 东盟 `T_v2` | 等级 / 方法 |
|---|---|---|---|---|---|---|---|
| F-01 | 字面读法 − W08 读法 | ID | +36.89 TWh（主算 1,483.78 → 1,520.67；IId 1,326.86 → 1,363.75） | +36.89 | 0 | +36.89 | EXACT：仓库 `v4_industry.run_case`，只改 `ats_add` 的 ID 生物质量 17.673 → 33.296 TWh（`evidence/SENS_PAPER_FUELWOOD.json`）；缓存份额未同步改（只影响子部门拆分，不影响 `T_v2` 合计） |
| F-02 | 网络溢出 − 表溢出 | VN | 0 | 0 | 0 | 0 | EXACT：网络台账 41,097,220 / 32,073,768 MWh 对表 29,951,239 / 20,927,788；差 11,145,980 MWh = VN pulp_paper 外购生物质向量。受影响的是报告量与由溢出转有用热的负荷（网络正确） |

### 2.1 复现清单（干净副本 `/home/jin/v4fable/`）

| 项 | 命令（在副本根目录） | 结果 |
|---|---|---|
| A2 回退 | `cd a2/scripts_project && python m08b_demand.py && python s3_0_industry.py`，所有被写文件与 `git show d3b9a3bc:<path>` 比 | 56 / 56 文件 SAME（`evidence/a2_compare.txt`） |
| S7 主算 | `python scripts_project/v4_industry.py --checkpoints cp_ras --steps S7 --anchor-mode ras` | 东盟 3,490.338011；11 国全部量 ≤ 5e-10 TWh（`evidence/S7_COMPARE.json`） |
| S7 IId | 同上 `--anchor-mode iid` | 东盟 3,166.521855；同上 |
| out 表 | `python scripts_project/v4_industry.py --anchor-mode ras|iid` | 24 / 24 文件与提交逐字节相同（`evidence/out_compare.txt`） |
| 注册表 | `python scripts_project/d1_registry.py` | `DATA_REGISTRY.csv` 逐字节相同；`D1_EVIDENCE.json` 只差 `generated_utc` |
| 测试 | `pytest tests/research/test_v4_*.py`（副本补齐上游 `scripts/`、`config.default.yaml` 后） | 37 / 37 通过（首轮 35 通过 + 2 失败，失败原因是副本缺上游 `scripts/_helpers` 与 `config.default.yaml`，补齐后通过；`evidence/tests_v4.txt`、`tests_registry_rerun.log`） |
| 开关全关构建 | `python scripts_project/s2_network.py --scenario integrated --output build_off/integrated` | 与 v3.1 包网络逐分量相同（第 2.2 节） |

### 2.2 开关全关的网络级回退（补充）

W08 的 R0 用的是 v3.1 包里的网络（`hpc_package_v3_1`，回执 code_sha `a1ef782b`），没有用 W08 代码重建过开关全关的网络。本审查在副本中用 W08 代码（`v4.enabled: false`，默认配置）构建 2920×3h 一体化网络（1 分 33 秒，峰值 0.81 GB）并与 v3.1 包网络逐分量比较（`scripts/compare_off_build.py` → `evidence/OFF_BUILD_VS_V31.json`）：**10 类组件（Bus 3,115、Load 2,188、Generator 1,946、Link 8,774、Store 649、StorageUnit 134、Line 148、Carrier 150、LineType、TransformerType）的静态表与全部时序逐值相同（rtol 1e-12 / atol 1e-9 MWh）**；meta 只在 `research_config` / `research_config_sha256` / `research_config_subset_sha256`（新增配置键，B12 设计如此）、`research_gas_network.production_caps_table`（F-10 的新键）与 `s2_layers` / `s3_layers` 模块版本戳上不同。即开关全关时 W08 代码在网络层面精确回到 v3.1（VERIFIED）。副本为运行 `build_research_assets.version()` 做了一次本地快照提交（`0de30830`，只进回执元数据，不是项目历史）。

## 3. 建议（按优先级）

1. 审阅端裁定 F-01 的读法并写入决策清单；落选读法登记为敏感性（ID ±36.89 TWh）。
2. F-02：溢出改在守恒层后计算、三处报告量更正、补测试；W08 / I2 报告中"VN 溢出 20.9 TWh"的叙述改为网络值（主算 41.10、IId 32.07）。
3. F-05 的三条测试缺口与 F-06 的注册表修正可与 F-02 同一提交。
4. F-03 / F-04 作为数据版本与对称性说明进入 HPC 计划的口径附录；不阻塞打包。
5. 其余 S4 文档性修正。

## 4. 本审查的证据文件

`evidence/CHAIN_CHECK.json`（数据链手算）、`CONSERVATION_CHECK.json`（守恒、残渣两侧、NEU、交通）、`ANCHOR_PROFILE_CHECK.json`（锚、曲线）、`NET_CHECK_main.json` / `NET_CHECK_iid.json`（网络层）、`S7_COMPARE.json`（A0）、`SENS_PAPER_FUELWOOD.json`（F-01 量化）、`a2_compare.txt`、`out_compare.txt`、`tests_v4.txt`；脚本在 `scripts/`。
