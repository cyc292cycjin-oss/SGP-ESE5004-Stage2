# M08B 进度（随进度更新）

- 指令：`M08B_CLAUDE_CODE_INSTRUCTION.md` v1，SHA256 `dde52c9284eb1fa9767a6f059d425bd6658e926891de3ce189e0905e6b7059b2`（与 `M08B_INSTRUCTION_SHA256.txt` 一致，2026-10-21 核对）。
- 边界：不连云；本机 56×3h 冒烟（Gurobi）须在第 4 节另行取得用户授权；单元测试中的 scipy / HiGHS 玩具 LP 允许。
- 工作树：`/home/jin/wt_m08b_20261021`，分支 `codex/m08b-demand-20261021`（自 M08a 头 `820c2cae`，PR #45）。M12 会话可能并行，各用独立 worktree。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| 1 | 开分支 / worktree；M11 台账草稿并入总台账（用户选择：标"无项号"、按时间插在 M08a 前） | 完成 | 见 git log |
| B1/B2 数据 | `m08b_demand.py`（锚表、ats_anchor 需求表、产量表）、`m08b_heat_bands.py`（JRC OIS 温度分布）、`s3_0_industry.py`（aeo8_ats_anchor 模式 + useful_heat_bands 变体）、`s2b_feedstock.py`、`s2_0_process_emissions.py`（33 行 ats_anchor）；旧模式表逐字节不变 | 完成 | 9ca5d341 |
| B1/B2 构建 + B3 | `s2_layers`（demand_anchor_settings / physical_output_settings / biomass_overflow、HEAT_BAND_TECH 三档、热档负荷、溢出转有用热、锚值逐国核对 1e-9）、`s2_network`、载体登记、`v5_gates` B11 / B12、`baseline.yaml`；`m08b_data.py`（新增 30、修正 23；拟增 16 行全部落实）；注册表 2,121 → 2,184 行（97b27c87…）；测试 `tests/research` 550 passed / 64 skipped / 0 failed（5 个玩具求解排除） | 完成 | ef01ceac（已推送 origin） |
| 3 | 在 ef01ceac（dirty 0）上重建：integrated 2920×3h cf189f39…（60.5 MiB）/ 365×24h d9fab9aa…（29.4 MiB）；disconnected af9f1881…（59.9 MiB）/ 7234216e…（28.8 MiB）；各 70 s、0.78 GB。变体 6 个 × 2 遍网络逐字节相同（回执只差 output.path）。静态：B5、B8、B11 路线、B13、B16、G2.1、G2.2、日均网络与全部 M08b 检查通过；B11 完整性（S1 旧检查）失败，S4M-3 旧网络同样失败（287 项相同）。对比表 `BUILD_INPUT_CHANGES_M08B.*` | 完成 | 见 git log |
| 4 | 本机冒烟（用户 10-21 授权；云端无运行经用户确认）：两情景 optimal（357 / 320 s，4.5 / 4.1 GiB），GATES_V6 ACCEPTED_LAYER2 ×2，C1 (a)(b)(c) 全过，B6 = +10.05 bn，账本恒等、无甲烷溢出、LNG 不受上限、导出完整 → 通过（`evidence/M08B_SMOKE_RESULT.json`、`evidence/smoke/`） | 完成 | 冒烟在 7381e91d 上运行 |
| 5 | 交付：`M08B_REPORT.md`、台账 M08b 条目、draft PR、审阅 ZIP | 完成 | 见 git log / PR |

## 设计决定（代码探查后，2026-10-21；写入报告，交审阅）

**构建入口：** 实际构建器是 `scripts_project/s2_network.py`（`build_scenario_s2`；一次构建同时写 2920×3h 与 365×24h（日均））；`build_research_network.py` 只剩 S1 静态校验函数。"四个网络" = integrated / disconnected 两次构建 × 两种分辨率。以往一次构建约 1 min、峰值 0.74 GB。worktree 无 `results_project`，构建时用 `--electric-base/--allocation/--survival` 指向主检出。

**B1 需求锚定（新需求表键 `aeo8_ats_anchor`）：**
- 新数据脚本 `scripts_project/m08b_demand.py`：读 `registry_v5/sources/AEO8_2050_BY_COUNTRY.csv`（C.8 人均 TFEC / 人均电力 ATS 2050、D.1 人口）、`AEO8_2050_ASEAN_TOTALS.csv`（C.3 ATS 面板 2022 / 2050；工业 2022 按 ATS 面板 186，S4R 用 BAS 面板 185.6）、居民电力 29.0 → 33.2 Mtoe（§3.1.3 p.61，常数 + 出处）；TL = mean(KH, LA, MM) 人均 × UN WPP 2024 中位 2050 = 1,889,249.5 人（源文件）。
- 权重 = 各国 2019 部门量（D1 表 base_2019）× ATS 区域部门增长代理，归一化（电力：居民用 §3.1.3，其余用 C.3；TFEC：C.3；非能源并入工业）。
- 基础负荷 = ATS 国家电力 × (居民 + 商业 + 农业及其他 + 交通 2019 电力) 份额（与 S4R 966 TWh 同口径，交通份额 = 2019 铁路等既有电力；EV 另算）。实现：新表中这四个部门的电力行 = 锚值（部门内按 2019 账户比例），`table_sectors` 模式自然得到锚值。
- 交通 = ATS TFEC × 交通权重；新表交通非电力行 × m = (交通锚 − 交通电力锚) / Σ 2019 交通非电力，使交通部门合计 = 锚、且与基础负荷不重复。EV / FCEV / ICE 份额与效率沿用现行 PyPSA-Eur 2050（注册表 share_*）。
- 工业（含非能源用途）乘数 = 工业锚 / 2019 工业（含 NEU）= ATS 工业能耗缩放；用于氨、甲醇、HVC、其余能耗回退子部门、NEU 行与 2.B/2.D、非水泥过程排放。钢、水泥用物理产量规则（下）。
- 居民 / 商业 / 农业的非电力燃料行：不锚定，沿用比率表（BAS 增长）——列为未决项。
- 物理产量：2050 = min(基年 × G^((2050−基年)/28 × 0.5), 人均饱和 × 2050 人口, 规划上限)；G = AEO8 总 GDP 增长 2022–2050（D.6 × D.1；TL = KH/LA/MM 均值）；水泥基年 USGS MYB 2023 T22（SG、TL 为 0），粗钢 worldsteel 2024（BN、KH、LA、TL 为 0）；规划上限只有 VN（钢 70、水泥 150）。过程排放 2.A.1 × (水泥 2050 / 水泥 2019)，其余 × 工业乘数。
- 配置：`research.demand.growth_method: ats_anchor`（新值；ratio / level 保留）、`research.demand.base_load_anchor: ats_buildings_agri`、`research.demand.transport_anchor: ats_service`、`research.s2.industry.physical_output_rule: sqrt_gdp_capped`（`industry_multiplier` = 旧规则，仅与 ratio / level 合用）及其参数。

**B2 有用热三档（other_bucket 新值 `useful_heat_bands`）：**
- 范围：`OTHER_BUCKET` = UNSD other / construction / mining（对应 JRC "Other industrial sectors"）；其余能耗回退子部门与物理产量部门保留 PyPSA-Eur 2050 路线。
- 拆分：其他桶燃料（煤、油、气、生物质）按 JRC-IDEES-2021 EU27 OIS 2019 各载体的过程分布：热用途 → 有用热 × 0.90 进三档（低焓热 / 干燥 / 热驱动冷却 → <150；蒸汽工艺 → 150–400；过程加热（热）→ >400）；柴油机（机械）→ 保留油终端需求；电力 → 全部保留为非热工业用电。C 级。
- 母线：`{node} industry heat`（低温，原母线）+ `{node} industry heat medium` + `{node} industry heat high`。
- 映射（technology-data v0.15.0 行；温度依据 DEA 工业过程热目录 2026 版文本）：低温 = electric boiler steam、industrial heat pump high temperature（≤150 °C）、gas boiler steam、solid biomass boiler steam(+CC)（原样）；中温 = electric boiler steam（DEA 1–16 bar，典型 175 °C）、gas boiler steam、solid biomass boiler steam(+CC)（DEA 蒸汽 125–300 °C）；高温 = direct firing gas、direct firing solid fuels（生物质）(+CC)（DEA 400–1,600 °C）。v0.15.0 无电直燃行 → 高温无电加热；**v0.15.0 无任何氢锅炉 / 氢直燃行 → 三档都不建氢供热（与指令"高温只允许氢、甲烷、生物质"的张力，报告开头标出）**。
- 生物质溢出（`biomass_overflow_mode: useful_heat`）：cap = 潜力（删 0.98）；工业溢出 × 0.90 → 中 / 高温（按工业固定生物质的来源温度档比例），农业溢出 × 0.90 → 低温；旧"溢出转甲烷"保留为 `methane` 模式（历史）。

## 接续点

- 当前（2026-10-21 20:00）：第 1–5 节全部完成，按指令停止，等待审阅。冒烟脚本 `/home/jin/m08b_smoke.sh`（结果在主检出 `results_project/m08b/smoke/`），判定 `scripts_project/m08b_smoke_eval.py`，证据收集 `/home/jin/m08b_smoke_collect.sh`，审阅 ZIP `/home/jin/m08b_zip.py`。
- 报告草稿素材：`evidence/M08B_TEMPERATURE_BAND_MAP.md`（映射表）、`evidence/BUILD_INPUT_CHANGES_M08B.csv`（对比）、`evidence/M08B_NETWORK_FILES.csv`、`evidence/M08B_STATIC_CHECKS.json`；与 S4R 偏差：基础负荷 966.9 vs 965.9（+0.11 %）、交通 1,700.4 vs 1,698.4（+0.12 %），原因 C.3 工业 2022 取 ATS 面板 186。
- 工具脚本（WSL）：`/home/jin/m08b_data.sh`（数据链 + 既有文件逐字节核对）、`/home/jin/m08b_registry.sh`、`/home/jin/m08b_tests.sh`（`FULL=1` 全量；5 个玩具求解用例始终排除）、`/home/jin/m08b_build.sh`（`OUTDIR`、`TAGS`）、`/home/jin/m08b_commit.sh`（镜像 + 提交，消息 `/home/jin/m08b_msg.txt`，强制加入 `/home/jin/m08b_force.txt`）。
- 已知坑：`wsl bash -lc "..."` 中 `$VAR` 为空，变量一律放脚本文件；`set -e` 下 `[ ] && cmd` 末尾失败会退出脚本。
