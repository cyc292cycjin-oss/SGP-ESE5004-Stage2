# M08-0 进度文件（第 130 项：注册表补登与一致性修正；只改注册表，不改模型、不求解）

- 指令 `M080_CLAUDE_CODE_INSTRUCTION.md` SHA256 `7e72998d39f313a0d00699ea36a9c3bf4676e6cee807de4b161ad52f10a5144e`，与 `M080_INSTRUCTION_SHA256.txt` 一致（2026-10-20 核对）。
- 分支 `codex/m08-0-registry-backfill-20261020`，自 S4R 分支头 `cefab870` 开出；独立工作树 `/home/jin/wt_m080_20261020`（主检出在 S4O 分支，未动）。
- 起点注册表 `research_inputs/registry_v5/DATA_REGISTRY.csv` SHA256 `46e234d79ec4fbc824c5c4e416591525bec11b46dbdbceb4d4512f2f31922e50`（与 MEET-D 记录一致）。
- 边界：不求解、不连云、不调用 Gurobi；不改配置、构建 / 求解脚本、网络、既有结果。

## 子步骤

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| M0 | 核对 SHA、开分支 / 工作树、建进度文件 | 完成 | — |
| M1 | 补登缺口（§J 1–5） | 完成 | `4e1de488` |
| M2 | 海上风机型与尾流核实 | 完成 | `995256ff` |
| M3 | 状态与等级修正（§I 3、5、6、7） | 完成 | `880955b8` |
| M4 | 状态值检查与注册表单元测试 | 完成 | `dca14c83`（只改本文件） |
| M5 | S4R 产出 v2（REGISTRY_ROWS_PROPOSED_v2、USER_DOWNLOAD_LIST） | 完成 | `fc964ea2` |
| M6 | 重跑数据清单 v2 与精简版 | 完成 | `c98bf5d9` |
| M7 | 报告、台账、draft PR | 完成 | 见“收尾记录” |

### 补充 01（第 131 项）

- 指令 `M080_SUPPLEMENT_01.md` SHA256 `a505908bf67585947fce5d9e8455455f071c429fa1f53bd9ab4859af86f673b7`，与 `M080_SUPPLEMENT_01_SHA256.txt` 及用户给出的值一致（2026-10-20 核对）。同一分支、同一工作树、同一 PR #44；边界同 M08-0。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| P1 | 屋顶光伏改 C 级（0.5×–1.5×），记录与 AEO8 / PDP8 / MyRER 的比值 | 完成 | `1a139be9` |
| P2 | GEGIS 原始文献核实；LA / TL 借用曲线登记为 C 级例外 | 完成 | `e18b2bc8` |
| P3 | 登记 4 个新下载文件；核实 technology-data 的 HICP 口径 | 完成 | `4e1007bc` |
| P4 | 存量机组成本表版本登记；`REGISTRY_ROWS_PROPOSED_v2.csv` 加一行规则 | 完成 | `1be5ce02` |
| P5 | 清单 v3 与新精简版（旧精简版改名 `_v2`） | 完成 | `8e1a2a29` |
| P6 | 报告“补充 01”一节、台账注明、更新 PR #44 正文 | 完成 | 本次收尾提交（SHA 见 PR #44 最新提交） |

- 补充 01 结果摘要：注册表 2,052 → 2,057 行（`6d1b2c34…0fa4`，提交 `1be5ce02`）；相对 `880955b8` 新增 5、修改 14，数值无改动；测试每步 91 passed / 24 skipped。GEGIS 文献核实一致（Mattsson et al. 2021，doi:10.1016/j.esr.2020.100606）；HICP：technology-data v0.15.0 用 EEA 年变化率累乘 1.25733（非 EU27 / 欧元区）。清单 v3：`DATA_INVENTORY_v3.xlsx`（`6bc7347d…`）、`.md`（`e2aef870…`）；精简版 `DATA_INVENTORY_BRIEF.xlsx`（`ff83b641…`）、`.md`（`d92d5447…`）；旧精简版 `DATA_INVENTORY_BRIEF_v2.*`（`f05113f1…`、`5726550c…`）。一次只读外部查询：Crossref 元数据（DOI 核对）。
- 续行点：补充 01 全部完成；停止，等待审阅。

## M0–M1 记录

- 复现性：现有片段 + 主检出中未入库的 `fragments/s4c_0.csv`（被 `.gitignore` 的 `*.csv` 忽略、从未提交）重拼得到的注册表 SHA256 = `46e234d7…2e50`，逐字节一致；M1 起把 `s4c_0.csv` 强制入库。`D1_EVIDENCE.json` 重生成时 6 个源文件的记录哈希由主检出的 CRLF 版本变为工作树的 LF 版本（内容相同）。
- 工作树另复制（不提交）`research_inputs/finance_v5/{COUNTRY_WACC_PUBLIC_SOURCES,DISCOUNT_RATE_IN_USE}.csv`，供 `test_s4c_0.py` 读取。
- 测试基线（工作树，27 个读注册表的测试文件，排除唯一的玩具网络求解用例 `test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers`）：91 passed / 24 skipped（缺既有构建，按设计跳过）。**另需说明**：开始时曾启动 `tests/research` 全量运行，约 25 s 后停止；按字母顺序 `test_s3b_r4.py`（可能还有 `test_s4c_3.py`）中的玩具网络 HiGHS 求解用例很可能已执行——不涉及研究网络、Gurobi 或云端。
- 提取：`scripts/m080_extract.py`（只读，12 s，峰值内存 0.57 GB）→ `evidence/M080_EXTRACT.json` 与 3 个 CSV。
- 写入方式：`scripts_project/m080_data.py` → `fragments/m080.csv`（新行）+ `fragments/m080_corrections.csv`（对已有行的整行替换）；`d1_registry.py` 只增加片段名与"按 param_id 整行替换"的几行，原片段不动（保留为历史）。
- M1 结果：新增 87 行（VRE 分国上限 55、土地规则 8、数据文件 3、廓线文件 2、屋顶光伏方法 1、Astar 3、地热 3、LNG 12）；LNG `lng_import_cap_*` 11 行只加注释；注册表 2,049 行；测试 91 passed / 24 skipped。

## M2 记录

- VERIFIED：筛查廓线 `profiles_calibrated_modern_c1/c3_3h.nc` 的 `offwind_ac` / `offwind_dc` 与 pypsa_eur 重建逐值相同（与 fork 最大差 0.776）；构建提交 `126110ff` 的 `s4a_profiles.py` 中 pypsa_eur 海上风 = `NREL_ReferenceTurbine_2020ATB_5.5MW`、`correction_factor 0.8855`。注册表（`renewable_profile_variant` 描述、`renewable_correction_factor_offwind_pypsa_eur`）正确；S4R 把"NREL 5 MW、无尾流"写为现状有误，在 M5 的 S4R 副本中改正。
- 新增核实行 `renewable_offwind_profile_check_built`（REFERENCE_ONLY）；注册表 2,050 行；测试 91 passed / 24 skipped。
- 对 M08-7（INFERENCE）：机型与尾流两项已在主算，无需改、无需为机型重建廓线；仍需海上面积重算（60 m、漂浮类、航道排除、DC 密度 3→2 MW/km²），航道栅格已在 raw12，不再是下载阻塞项。

## M3 记录

- 修正 32 行（整行替换，`fragments/m080_corrections.csv`）：natura → REGISTERED（补 Dataverse `wdpa_reclass.tif` V1.3、MD5 与本地一致、CC0）；`cost_layer_A_technology_data_v0_13_2_2050` → REFERENCE_ONLY（历史：已被 v0.15.0 替代）；SMR 代理 2 行注明构建读取且与 v0.15.0 同值；地热既有 6 行（FOM、CO₂ 强度 → REFERENCE_ONLY；VOM / 效率 / 投资 DATA_PENDING → REFERENCE_ONLY；寿命注明）；KH / TL 封存 4 行 A → C（分项行沿用国家合计行的 D1 区间）；`renewable_ship_density_raster` DATA_PENDING → REFERENCE_ONLY；`renewable_profile_variant`、`renewable_resource_classes`（历史：已被 S4B-3 行替代）与 4 个 pypsa_eur / fork 廓线文件行 → REFERENCE_ONLY；LNG 11 行加注（M1）。
- 新增 2 行：`lng_gem_ggit_release_verified`（文件内写明 September 2025 release；S4R 下载为同一文件）、`cost_v0132_usage_built`（v0.13.2 使用情况汇总）。
- 前后对比（`scripts/m080_registry_diff.py`，基准 `cefab870`）：1,962 → 2,052 行；新增 90、修改 32、删除 0；构建读取的数值无变化；状态 DATA_PENDING→REFERENCE_ONLY 4、REFERENCE_ONLY→REGISTERED 1、REGISTERED→REFERENCE_ONLY 9；等级 A→C 4。DATA_PENDING 51 → 47。测试 91 passed / 24 skipped。

## M4 记录

- 状态值的校验链：`scripts_project/d1_common.py` 第 52–53 行 `STATUSES`（固定 7 个值）→ `Registry.add` 遇未知状态报错 → `tests/research/test_d1_registry.py::test_registry_schema_and_tiers` 断言 `set(status) ⊆ STATUSES`。新增"历史 / 已被替代"状态必须改代码，因此不新增；凡属历史的行一律用 REFERENCE_ONLY，描述以"历史：已被 X 替代"开头（M3 已写入 6 行：`cost_layer_A_…`、`geothermal_existing_FOM`、`geothermal_existing_VOM`、`renewable_profile_variant`、`renewable_resource_classes`，以及 4 个廓线文件行注明"对照文件"）。
- 注册表相关单元测试（27 个读注册表的测试文件，排除唯一的玩具求解用例）：91 passed / 24 skipped / 0 failed，与基线一致；24 个跳过均为"既有构建不在工作树"的设计跳过。

## M5 记录

- `scripts/m080_s4r_v2.py`（只读 S4R 原件 `REGISTRY_ROWS_PROPOSED.csv` SHA256 `258b75c3…dfd7c`）→ `REGISTRY_ROWS_PROPOSED_v2.csv`（42 行，SHA256 `6cd041eb…e936`；新增列 `registry_row_exists`、`supersedes`、`m08_write_note`、`v2_change`）：7 行改为 add（`industry_cement_2050_VN`、`renewable_capacity_per_sqkm_solar`、`renewable_landuse_rule_solar`、`lng_terminal_capacity_source`、`lng_terminal_cap_rule`、`biomass_overflow_rule`、`nuclear_cost_rule`）；9 行 modify 的同名行均存在；`lng_terminal_cap_rule` 按列名重新对齐（v1 只有 10 个字段，缺 `source_locator`）；9 行写明被替代的 param_id 并注明"M08 写入时把旧行标为历史"；`renewable_offshore_rule` 描述按第 2 项结论改写（机型 / 尾流已在主算）。`industry_cement_2050_VN` 的旧值 581 Mt 只在 `research_inputs/demand_v5/INDUSTRY_2050_SUMMARY_aeo8_ats_relative.csv`，注册表无同名行，照实保留。
- `USER_DOWNLOAD_LIST_v2.md`：文首修订说明；删去 A1（航运密度已在 raw12，SHA256 一致，改列 §0）；B4 注明本地已有 OGCI PDF 但汇总表为图片、未能复核。原件 SHA256 `6b97f33c…3c2d` 不变。

## M6 记录

- v1 脚本复制为 `work/p1_meet_20261020/scripts/meet_data_inventory_v2.py`（v1 脚本与 v1 输出不动，哈希与 MEET-D 记录一致：xlsx `d0436436…`、md `4199354e…`、stats `5651c74f…`、脚本 `430b5185…`）。v2 改动：读 M08-0 提交 `880955b8` 的注册表（SHA256 `6950a15d…8dd2`）与 `REGISTRY_ROWS_PROPOSED_v2.csv`；分类规则补 M08-0 新行前缀（2,052 行全部归类）；表 1 中已补登 / 已修正项的文字更新（含更正 v1 的“PyPSA-Earth 无屋顶潜力方法”）；§I 改为“不一致项与 M08-0 处理结果”（11 项，含 M08-0 新发现 2 项）；§J 改为补登后的缺口（8 项）；新增 §K v1 → v2 对比；表 1 增加 5 列“附件 B”文字；表 3 / 表 4 中供附件 B 使用的列去掉内部步骤代号（记录位置列不变）。
- 输出：`DATA_INVENTORY_v2.xlsx`（`d197b840…0205`）、`DATA_INVENTORY_v2.md`（`2324192e…10e7`）、`DATA_INVENTORY_BRIEF.xlsx`（`f05113f1…2583`）、`DATA_INVENTORY_BRIEF.md`（`5726550c…8499`）、`evidence/MEET_DATA_STATS_v2.json`（`71452708…f473`）；xlsx 内含时间戳，重跑哈希会变。
- 实算：注册表 2,052 行，A 263 / B 1,301 / C 488；主算输入 1,263 行，A 10.85 % / B 61.28 % / C 27.87 %（v1 1,185 行：11.73 / 59.32 / 28.95 %）；11 国同口径占比不变（核查表 9/19 = 47.4 %；表 1 现行 18/25 = 72.0 %、修正后 17/25 = 68.0 %）。
- 精简版核对（`scripts/m080_brief_trace.py` → `evidence/M080_BRIEF_TRACE.json`）：664 个数据格全部在 v2 详表中原文出现；自动检查无注册表 `param_id`、无 `xxx_*` 前缀。v2 中剩余的“注册表无记录”均为 S4R 拟增行或外部对照来源，照实保留。

## M7 记录

- `M080_REPORT.md`（摘要、补登清单、海上风结论、v0.13.2 使用情况、Astar 结论、待确认与未解决项）；台账 `research/STAGE2_PROJECT_LEDGER.md` 追加 M08-0 条目；PR 正文 `evidence/PR_BODY_M080.md`。

## 收尾记录

- 提交：M1 `4e1de488` → M2 `995256ff` → M3 `880955b8` → M4 `dca14c83` → M5 `fc964ea2` → M6 `c98bf5d9` → M7 `5fb93483` → 本收尾记录提交（SHA 见 PR #44 最新提交）。
- 分支 `codex/m08-0-registry-backfill-20261020` 已推送；draft PR https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/44（base `codex/s4r-unification-plan-20261020`，即叠在 #43 上）；未合并、未 force-push。
- 推送前保密扫描（本分支相对 `cefab870` 的全部新增行）：无主机、端口、密码、密钥或许可证内容。
- 审阅 ZIP：`D:\ResearchWorkspaces\ASEAN\outputs\M080_REVIEW_20261020.zip`（`workspace_tools/New-WorkspaceDelivery.ps1` 打包；包内 `MANIFEST_SHA256_CRC32.csv` 逐成员列出 SHA256 与 CRC32）；ZIP 不入库。
- 工作树 `/home/jin/wt_m080_20261020` 中另有 2 个被忽略、未提交的复制文件（`research_inputs/finance_v5/` 两个 CSV，仅供测试读取）；主检出未改动。

## 续行点

全部完成；停止，等待审阅。
