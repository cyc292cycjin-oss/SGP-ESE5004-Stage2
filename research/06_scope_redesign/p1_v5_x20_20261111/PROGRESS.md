# X20 进度（v5 输入修订的实施）

指令：`V5_X20_INSTRUCTION.md`，SHA256 `5126e2a7717df42d1e36bf53f602475605fe7514b81915bf185cad16b896cb92`（`sha256sum -c V5_X20_SHA256.txt` → OK）。
会话模型：Opus 5.5（claude-opus-5-5），effort xhigh。用户启动时说明：决策第 240–245 项已勾选，先只做 A 段，完成后停下。

## 开工记录（2026-11-11 21:36 SGT）

- 其他会话：本机另有 2 个 Claude Code CLI 进程（19:58、20:09 启动），均无 bash / wsl / python 子进程，WSL 内无 python / gurobi / snakemake 进程；判定为应用内保留的空闲会话（X03、X10 已完成），不在运行任务。
- 磁盘基线：WSL `df -h /`：1007G 总，249G 已用，708G 可用（26 %）；`du -sh /home/jin` 246G；D 盘 `df -h /mnt/d`：652G 总，445G 已用，207G 可用；交付目录 13,921 B。
- 内存：WSL total 11,483,643,904 B，available 10,618,589,184 B；swap 4 GiB 未用；nproc 16。
- 分支：`asean/v5-x20-20261111` 从 `26c2e47d025fdd4e46cb278718d93aeddabbe984` 新建（远端无同名分支）；worktree `/home/jin/wt_v5_x20`，A 段为稀疏检出（cone，只含 `research/06_scope_redesign/p1_v5_x20_20261111` 与顶层文件），1.7 MB。稀疏检出使共享配置新增 `extensions.worktreeconfig true`（git 为单个 worktree 启用稀疏检出的标准做法，其他 worktree 不受影响）。
- 仓库无启用的 hooks（hooks/ 只有 *.sample）。
- 代码行号读取：`26c2e47d..ac75354c`（W14 worktree `/home/jin/wt_v4_w14` 的 HEAD）33 个改动文件全部在 `research/` 下，代码与 `26c2e47d` 一致，A 段从该 worktree 只读取行号，不写入。

## 进度

| 时间 (SGT) | 段 | 事项 | 状态 |
|---|---|---|---|
| 21:36 | A | SHA256 核对、模型确认、开工检查、建分支与 worktree | 完成 |
| 21:45 | A | 通读 X03 报告（`c6352f89…`）、X10 报告（`d0a8cb01…`）与 BUNKER_CARBON_MEMO（`6789576d…`）；66 个复用输入算 SHA256，GWA 22 个文件按下载日志核对通过 | 完成 |
| 21:50–22:15 | A | 4 个只读子代理分领域定位代码（可再生 / 存量与燃料 / 碳与需求 / 开关与构建），约 40 处关键行号逐行打印核对（`logs/09`）；补充事实：S1 冻结存量边界机组（`logs/10`）、剖面 nc 入 git 与 W14 / D2c 的内存记录（`logs/11`）、PyPSA-Eur 配电网原文 | 完成 |
| 22:20 | A | 撰写 `X20_SPEC.md`（20 项修订 + 框架；待决问题 18 个）与 `DOWNLOAD_CANDIDATES.csv` | 完成 |

## A 段结束记录（2026-11-11 22:22 SGT）

- 磁盘：WSL `df -h /`：1007G 总，249G 已用，708G 可用（与开工时相同，精度为 G）；交付目录 237,000 B；WSL 家目录新增 = 稀疏 worktree 1,678,823 B + `.git/worktrees/wt_v5_x20` 元数据（< 1 MB）。C 盘与 WSL 家目录新增远低于 1 GB。
- 内存：WSL available 10,676,219,904 B。
- 求解器 0 次；不连 HPC；没有下载；没有修改任何代码、输入、配置或注册表。
- 子代理：4 个 Explore 子代理只读（Grep / Glob / Read）。其中一个开工时用 Bash 执行了一次只读 `ls`，已自报，没有写入。
- 偏离：无。读取 `results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json`（只读 JSON，不是网络），没有用内存门槛（门槛针对网络读写）。
- 提交与推送（交付目录副本补记，不在提交内）：`7ac713e532001dfba5250bb854d51561e87898fa`，分支 `asean/v5-x20-20261111`，已推送，`ls-remote` 与 HEAD 一致；`X20_SPEC.md` SHA256 `d5308511c136ce154168291083f74b30b75cdaf76f26cae7a30ae7480cf2d9a3`（D 盘副本与提交版本逐字节相同）。小瑕疵：镜像文件从 `/mnt/d` 复制，提交时的文件模式为 100755，B 段第一个提交顺手改回 100644。未建 PR，台账条目留到 B 段。
- **下一步：A 段完成，请交审阅端审阅。**

## B 段（2026-11-11 23:10 SGT 起）

用户转达：审阅端通过 A 段规格；待决问题答复为决策第 246 项（`X20_SPEC_ADDENDUM_246.md`）；要求开始 B 段。

| 时间 (SGT) | 事项 | 状态 / 恢复点 |
|---|---|---|
| 23:11 | worktree 改为完整检出（720,515,978 B），复制 finance_v5 两个被忽略输入，`results_project/{assembly_v1,s1}` 链接主检出、`v5x20` 链接 D 盘 `builds/`；本步目录 36 个文件模式改回 100644；WSL `df -h /`：250G 已用、707G 可用 | 完成 |
| 23:15 | 写 `X20_SPEC_ADDENDUM_246.md`（Q12 规则在计算前写定）；B 段第 1 个提交 `e4b590f8`（补记 + 文件模式），已推送 | 完成 |
| 23:16 | 用户转达：HK01 清理会话已结束，Q18 的"本机没有其他会话"条件已满足；56 时段求解按"预计峰值 ≤ 可用 − 2 GiB"执行，Gurobi 一次只跑一个 | 记录 |
| 23:18 | v4 基线全量测试第 1 次启动 22 s 即退出（pytest 捕获临时文件在 9p 的 TMPDIR 上无法 truncate；日志改名为 `logs/ut_full_base_failed_tmpdir.txt`）；改为 WSL `/tmp` 作 TMPDIR 与 basetemp（跑完记体积后删除），重跑中 | 进行中 |
| 23:20 | D 盘写 netCDF 测试通过（默认 HDF5 文件锁可用），构建输出可直接写 D 盘 | 完成 |
| 23:22 | Q7 核实：非能源用气在 RAS 锚之外（`m08b_demand.py:7,11,315,453,466`：种子"non-energy use excluded"，"NEU outside the TFEC envelope"）→ ②4 可实施 | 完成 |
| 23:25 | ②2 数据：OSM 预建库国内交流重复组 318 组 / 937 行（MY 292 / 877）；OSM API 4 次请求取 314 个 way 标签，427,221 B，0 缺失，299 个带 cables（`downloads/osm/OSM_API_LOG.tsv`） | 完成 |
| 23:27 | ②1 数据：NGCP TDP 2025–2050 PDF 5,415,314 B，SHA256 `eb39b15e…`（`downloads/ngcp/NGCP_DOWNLOAD_LOG.tsv`）；PDF 第 5 页 MVIP 450 MW；第 35、40、72 页民都洛线路均为规划（2027-09 / 2030-12 / 2033-02）；第 43–44 页双极化"additional 440 MW" | 完成 |
| 23:28 | 两个只读子代理在跑：②6 五台机组坐标（只用网页阅读）、①7 MM 生物质复核 | 完成（见下） |
| 23:25–23:29 | **中断：** 上一次会话退出，WSL 随之停机（`wsl -l -v` Stopped），基线测试与 GWA 试跑都以退出码 4 结束（日志改名 `*_interrupted*`）；23:29 重启 WSL，worktree 干净（HEAD `e4b590f8`），两项任务重跑，两个子代理续跑 | 记录 |
| 23:30 | ①1 数据试跑：`v5_wind_gwa.py` 39 s、峰值 RSS 1.69 GB；有效格点 4,048 个，系数中位数 1.244，截断 1 个；156 个校准风场全部取到 GWA 点位值；容量加权点位系数 / 格点系数：TH 1.432 / 1.265，VN 1.311 / 1.171，PH 1.326 / 1.03 | 完成（试跑在 D 盘 cache，正式运行在 worktree） |
| 23:31 | Q12 观测值：Ember 光伏 CF（同风电校准算法，VN 2020–2022 不进主值）：可用 8 国 ID 0.187、KH 0.191、MM 0.089、MY 0.221、PH 0.135、SG 0.137、TH 0.192、VN 0.201（`cache/q12/`） | 完成 |
| 23:36 | ①7 子代理结论：MM 偏高主要是口径（IRENA 2022 缅甸只含木质残余）；确认 2 处方法错误（E1 棉花三重计数、E2 R-3 组名前缀未剥离，11 国共用），MM 净 −1.42 TWh；3 处疑点写局限。已亲自核对 `d1_biomass.py:79-81,97`。补记 §4.3 写定处理：开关 `biomass_residue_fix`（表级） | 完成 |
| 23:40 | ②2 数据试跑：只有 MY 5 条国内走廊有重复行，4 条通过重建核对（线 90 ×0.320、93 ×0.222、95 ×0.445、96 ×0.387），线 94 核对失败（140 倍）不改；BN / TL / LA / TH / VN 的重复组都在节点内部或不对应国内存量线。**更正规格 §1.9：** `regions_onshore.geojson` 是节点坐标的分国 Voronoi（被 git 忽略），不是作者 busmap，归属改为同国最近节点（同 X10） | 完成 |
| 23:45 | ②6 子代理结论 + 节点计算：只有 Truong Son 二期改节点（LA2 1 → LA2 3，OSM 一期风机群，二期"同一区域"）；Thai Binh（推定厂址区域内各点均为 VN2 6）、Upper Yeywa（坝址仍为 MM2 5）、New Kapar（保留 GEM）节点不变 | 完成 |
| 01:54 | 第 2 次基线测试 2 h 25 min 只到约 40 %（m10p 子进程测试段）。原因 VERIFIED：`PYTHONPYCACHEPREFIX` 指向 D 盘（9p）时每个子进程 `import pypsa, xarray, pandas` 要 22.8 / 26.3 s，不设时 2.2 / 1.7 s（`scripts/31_import_timing.sh`）。停掉该次测试（`scripts/32_stop_base_tests.sh`；EXIT 143，用时 8,875 s，basetemp 385,096,087 B 已删；另清理 1 组孤儿 `gates_v6.py select-profile` 进程组）；日志改名 `logs/ut_full_base_stopped_slow_pycache.txt`。**本地计算预算多耗约 2.5 h（偏离，写入报告）** | 记录 |
| 01:58 | `21_full_tests.sh` 去掉 pycache 前缀（worktree `__pycache__` 被 .gitignore 忽略，结尾记录体积与残留进程），第 3 次基线测试启动，20 s 内约 20 个测试 | 完成 |
| 02:30 | **v4 基线全量测试 VERIFIED**（`logs/ut_full_base.txt`，HEAD `e4b590f8`）：1 failed / 875 passed / 56 skipped / 5 deselected，1,917.75 s（31:57）；失败的仍是 `test_s1_built_networks.py::BuiltNetworks::test_static_validation_passes_on_reload`，与 D2c 记录（875 / 1 / 56）一致。basetemp 511,350,578 B 已删；worktree `__pycache__` 10,870,068 B；无残留进程；git status 干净 | 完成 |
| 02:39 | 框架：`v5_common.py`（开关集、SHA256、meta 记录与核对）；baseline.yaml 第 533 行后插入 `research.demand.v5`（enabled false，列出的值 = v5 主集）；`v4_common`：v5 启用时两个表级键 `v5_neu_gas_growth` / `v5_biomass_residue_fix` 进入 v4 开关集，主集目录 `out_<anchor>_v5`，v5 关闭时 v4 开关集与 26c2e47d 相同；`s2_network` 导出前写 `v5_x20` 记录并核对，`m08a_variants` 核对；F0.3 豁免加 `v5_` 前缀。注册表链重跑（`scripts/36_registry_chain.sh fw`）：2,469 行，只有 `v4_biomass_overflow_cap_share` 的 source_sha256 随 baseline.yaml 变（`8a96fc17…` → `818b0fe4…`）。定向测试 185 passed（`logs/ut_fw2.txt`）。本提交同时删掉 23:15 行末残留的 A 段占位句、补记 §4 入库 | 完成：`409deeb8`，已推送 |
| 02:55 | **②5 寿命边界（决策 244、246 Q2 (b)）**。VERIFIED：原 S4A-2 的"网络已有"身份 = 电力底座 745 个 + S1 地热存活 3 个（186 MW）= 748（`logs/37_fleet_identity_check.log`）；`s4a_2_fleet_data.py` 以电力底座为网络、严格 / 30 a 复现已提交的 9 个文件，逐字节相同（`logs/38_fleet_v5_tables.log`，峰值 RSS 382 MB）。v5 规则（≥ 2050，地热 40 a）：`FLEET_ADDITIONS_2050_V5.csv` 501 行 79,153.1 MW（W14 299 行 73,614.7 MW；新增 202 行 5,538.4 MW = 边界 5,483.4 + 地热 55.0；删除 0）；不随规则变的 5 张表重算后不变。S2 地热按同一规则重判（`s2_layers.geothermal_unit_table`）：20 台 1,123 MW（ID 1,051、PH 72），GEM 路径排除这 20 台。**更正 A 段规格：** S1 边界机组是 **8 台**（SG 2、TH 1、MY 2、ID 2、MM 1），2,503.1 MW 不变，"7 台"是加总笔误。Q2 逐台：7 台 1,833.1 MW 经 GEM 新增进入，TH North Bangkok 1 号 670 MW 不进入（GIPT mothballed），重复 0（`evidence/Q2_BOUNDARY_UNITS.csv`、`Q2_NO_DOUBLE_COUNT.json`）；Srinagarind 同厂同名为常规 360 + 抽蓄 360 两台不同机组，不是重复。定向测试 60 passed / 4 skipped（`logs/ut_i25b.txt`）。未改：`asset_survival.py:23`、`selected_closure.py:119`（Q2 (b)）、`audit_residual_sources.py:24`（只审计）、`s4b_1_fleet_data.py:49`（74 台在建无投运年机组退役年均 ≥ 2051，两种规则结果相同；S4B1 表中地热寿命字段仍为 30，只是元件属性，不进 LP） | 完成：`ddc1c071`，已推送 |
| 03:00 | **②6 近似坐标（决策 244）**。`v5_gem_coord_data.py` 用 `s4a_2_fleet_data.nearest_node` 与电力底座 AC 节点（与新增表同一规则）写 `GEM_COORD_CORRECTIONS_V5.csv`，断言 GEM 节点 = 新增表节点。Truong Son 二期、Upper Yeywa 在 S4B-1 表（在建、无投运年）而不在 S4A 表，节点更正放在两表拼接之后（`s4a_fleet.add_gem_fleet` → `v5_layers.gem_node_override`）。只有 Truong Son 二期 350 MW 改节点 LA2 1 → LA2 3（LA2 3 有陆上风电候选曲线）；New Kapar、Thai Binh ×2、Upper Yeywa 节点不变（`logs/40_gem_coord_table.log`）。定向测试 30 passed / 2 skipped（`logs/ut_i26.txt`） | 完成：`8b57ac4c`，已推送 |
| 03:07 | **①1 第一部分（决策 241、246 Q1 (b)）**。worktree 只读链接 `cutouts`、`results_project/s4a`（主检出）。`v5_wind_gwa.py` 正式输出与试跑逐字节相同（47 s，峰值 RSS 1.69 GB；有效格点 4,048，截断 1）。未改的 `s4b_3_wind_calibration.py` 复现 v4 五个输出文件，逐字节相同；加 `--point-factor` 模式后 v4 模式再复现，仍逐字节相同（`logs/41_…`、`logs/42_…`）。**停止点：** 点位系数模式校准 alpha PH 0.6994、VN 0.7893 < 下限 0.8（规格 §1.1(a)2：v5 越界即中止），alpha 表未写出。诊断（D 盘，临时放宽上下限，不入库；`logs/43_calib_v5_diag.log`、`evidence/ALPHA_DIAG_V4_POINT_CELL.csv`）：Q1 (b) 点位 PH 0.699 / TH 0.908 / VN 0.789 / 其余 0.806；Q1 (a) 格点 0.891 / 1.027 / 0.872 / 0.903；v4 0.910 / 1.294 / 0.995 / 1.046。**待用户决定**；①1 剖面、①2、Q12 中依赖风电剖面的部分暂停，其余各项继续 | 第一部分完成：`d42adc31`，已推送；后续待决 |
| 03:10 | **①3 海上风电东盟溢价（决策 241）**：`v5_layers.apply_offwind_premium`，s2_network 在台风溢价之后调用；主值 0 % 不改网络；W14 网络可扩建海上候选 offwind-ac 209 / -dc 194 / -float 207 个。玩具网络测试 12 passed（`logs/ut_i13.txt`） | 完成：`85d11d2d`，已推送 |
| 03:13 | **①4 光伏（决策 241、Q15 (a)）**：`v5_layers.apply_solar_cap_scale` 在 `s4a_layers.apply_renewable_profiles` 的密度换算之后、等级拆分之前调用；`SOLAR_MY_LANDUSE_VARIANTS_V5.csv`：MY 基数 86,396.03 MW（= W14），油棕 FAOSTAT 2019–2023 均值 51,700.41 km² × 5.1 → 系数 4.0519，开阔森林沿用规格 198 / 86.4 = 2.2917（LC100 121–126 原始面积不扣保护区的交叉核对 2.3957，只记录）。测试 47 passed（`logs/ut_i14.txt`） | 完成：`4ee29768`，已推送 |
| 03:17 | **用户转达决策第 251 项（①1 停止点答复）：** 维持 Q1 (b)；越界检查改为逐国核对有效倍数（格点系数 × α，相对 ERA5），候选格点按潜力加权给 p10 / 中位 / p90，国别中位数在 [0.8, 1.6] 内即继续，任一国越界则停下；报告写明这是看到结果后的规则更正及理由，并列 v4、(a)、(b) 三种口径的有效倍数与候选平均 CF 对照表。规则在计算前写入补记 §5 | 记录 |
| 03:21 | **①5 水电（决策 241、Q14）**：`s4c_layers` 入流分母 = 2025 年已投运容量（`v5_layers.operating_share`），在建机组按同国单位入流另加；乘数开关 1.0 = 目标 ÷ 表中乘数；弃水报表（记账部分 / 真实弃水）进 `s2_solve`（有 v5_x20 记录的网络写 HYDRO_SPILL.json）与独立脚本 `v5_hydro_spill.py`。×1.1 出处：PyPSA-Earth 提交 `273eba53`（2022-06-30）写入默认配置，无理由说明，配置文档写默认 1.0 → C 级，区间 1.0–1.1（`logs/46_…`）。**偏离规格：** D2a 重分类出的常规水电部分没有身份记录，按"已投运"计入分母（D2a 的设计就是让它分享目标电量），没有按规格 §1.5 第 1 条排除。v4 已解网络从 W14 归档提取中（`scripts/45_…`），弃水回归待做。测试 54 passed（`logs/ut_i15.txt`） | 完成：`b994c729`，已推送 |
| 03:25 | ①5 弃水回归 VERIFIED：W14 归档 `results_full_final_20261109T142421Z.tar.gz` 只提取 F1 / F2 2920×3h 已解网络到 D 盘 `cache/v4solved`（383 s，2,621,827,153 B，SHA256 两个都 OK）；`v5_hydro_spill.py`：F1 报告 526.956 / 记账 519.865 / 真实 7.091 TWh，F2 528.900 / 521.510 / 7.390 TWh，存量水库 27.024 / 27.131 TWh，复现 X03（`logs/49_…`，`evidence/HYDRO_SPILL_V4_W14_F{1,2}.json`；峰值 RSS 0.34 GB） | 完成 |
| 03:31 | **①1 第二部分（决策 241、246 Q1 (b)、251）**：点位系数校准写出 `WIND_CALIBRATION_ALPHA_V5.csv`（PH 0.6994、TH 0.9079、VN 0.7893，其余 8 国加权 0.8059，区间 0.699–0.908；α 越界只记录）。有效倍数核对（`v5_wind_effective_multiplier.py`，候选格点 = 作者陆上风电潜力 > 0）：(b) 各国潜力加权中位数 0.831（BN）–1.312（TL），全部在 [0.8, 1.6] 内 → 继续；对照表 v4 / (a) / (b) 写 `evidence/WIND_EFFECTIVE_MULTIPLIER_V4_A_B.csv`。剖面：`s4a_profiles` 新增 `calibrated_gwa_v5`（变体自带 α 表与格点系数），与 `calibrated_modern` 同一次运行；c1 39 s / 1.87 GB，c3 37 s / 1.87 GB；**`calibrated_modern` 复现与已提交文件逐值相同（c1、c3）**。导出 `profiles_calibrated_gwa_v5_c{1,3}_3h.nc`，海上与光伏与 calibrated_modern 逐值相同（断言）；类表、清单、日志都是独立文件（v4 输入一字不动）。`s4a_layers`：v5 且 `gwa_cell_ember` 时用 calibrated_gwa_v5。节点平均陆上 CF：c1 8.72 % → 5.45 %，c3 11.38 % → 6.85 %。测试 49 passed（`logs/ut_i11b.txt`）。未改：`s4i_static_audit.py:388`（读 v4 表的审计，不变） | 完成：`5536c9bd`，已推送 |
| 03:34 | **①2 存量风电最好等级 + Q12 机制（决策 241、246）**：`v5_layers.existing_profile_column`（最好等级 = 节点最高 c{k}，逐级回退；节点平均 = `<node> solar rooftop-2025` 列，即 c1 节点光伏曲线），`s4a_fleet.add_gem_fleet` 在 v5 打开时使用并逐组件记账。W14：存量风电 13 个组件（陆上 11、海上 2），存量光伏 12 个组件全部是 GEM 新增，各节点都有 c2 与屋顶列。Q12 的选择待 v5 预构建网络上按补记 §3 计算。测试 44 passed（`logs/ut_i12.txt`） | 完成：`678c1e25`，已推送 |
| 03:36 | **①6 地热上限（决策 241、Q16）**：`GEOTHERMAL_ID_POTENTIAL_V5.csv`（17,506 = 12,046 + 2,493 + 2,967，文章合计写作 17,501；5,460；23,590）；`v5_layers.geothermal_caps_v5` 在 `apply_candidate_caps` 中按当前网络 ID 存量算上限（上限 + 存量 = 潜力）；PH 重建按 v5 寿命规则：1,827 → 1,755 MW（v4 的 1,827 在电力底座节点上复现；`logs/51_…`）。测试 43 passed（`logs/ut_i16.txt`） | 完成：`66f41aca`，已推送 |
| 03:43 | **①7 生物质 E1 / E2（决策 241、246）**：`d1_biomass.py --v5-residue-fix`（只留籽棉；GROUPS 补三个组名）→ `BIOMASS_POTENTIAL_2050_V5FIX.csv`；`v4_biomass_potential.py --v5-residue-fix` → T06_V5FIX 与 `BIOMASS_CROSSCHECK_IRENA_V5.csv`；v4_common / v4_industry S7 按表级键读 V5FIX。两脚本 v4 模式复现全部已提交输出；**发现：** 片段 `fragments/biomass.*` 记录的 IRENA 文本 SHA256 `eaf81aa2` 是主检出工作区副本，git 中为 `76356c9e`（数据相同，可能是行尾差异，INFERENCE），片段未改，写入局限（`logs/53_…`）。T06：MM 85.63 → 84.21 TWh，ASEAN +11.26 TWh（ID +9.86、TH +1.75、VN +0.78；`logs/52_…`）。测试 66 passed（`logs/ut_i17.txt`） | 完成：`3abd4f3c`，已推送 |
| 03:45 | **②1 菲律宾直流存量（决策 244、Q8）**：`PH_DC_STOCK_V5.csv`（冻结值与电力底座逐条一致，18,193.28 → 1,330 MW）；`v5_layers.apply_ph_dc_stock` 在 TH-MY 存量层之后调用。测试 27 passed（`logs/ut_i21.txt`） | 完成：`2596dc26`，已推送 |
| 03:47 | **②2 OSM 重复交流行（决策 244、Q6 (a)）**：正式表（电力底座为网络，与 W14 线路数值相同）与试跑一致；线 90 / 93 / 95 / 96 修正，线 94 不改（局限）；way 标签表入库 `OSM_WAY_TAGS_V5.csv`；`v5_layers.apply_ac_dedup` 在 PH 直流层之后调用。测试 51 passed（`logs/ut_i22.txt`） | 完成：`f25fa9b5`，已推送 |
| 03:57 | **②4 NEU 天然气按产品（决策 244、246、Q7）+ 表目录 out_ras_v5**：`m08b_demand --neu-gas-rule product`（a = min(NEU₁₉, 合成氨₁₉ × 10.8)，b = 0（甲醇原料气无有出处单耗，局限），残差 × NEU 乘数，再做 F2.4）；USGS 2019 合成氨只有 ID / MY / VN，ID、MY 按气头处理（INFERENCE），VN 不论气头份额 2050 均为 0。表链：v4 主集复现 out_ras 无差异；`out_ras_v5`（两个表级键）生成，各 4–5 s / 0.14 GB（`logs/56_…`）。NEU 天然气 2050：ID 84.37 → 0，MY 181.67 → 183.50 TWh，其余不变（`evidence/NEU_GAS_PRODUCT_RULE_V5.csv`）。`test_v4_d2a_fixes` F-14 辅助函数改读 `biomass_potential_file`。测试通过（`logs/ut_i24*.txt`） | 完成：`923878a5`，已推送（该提交顺带收进了有语法错误的 `v5_gas_cap_data.py`，下一提交修正） |
| 03:58 | **②3 天然气上限（决策 244）**：`GAS_CAP_FRACTIONS_V5.csv`（X10 全精度）；`s3_layers.add_gas_network` 乘国别系数，v4 上限表不改；规则 B 合计 1,594.77 TWh、规则 A 930.79 TWh（与规格一致）；系数 0 走现有"上限 ≤ 0"分支。测试 56 passed（`logs/ut_i23.txt`） | 完成：`c2f860c9`，已推送 |
| 04:02 | **③1 CO₂ 封存（决策 244、Q13）**：`CO2_STORAGE_CASES_V5.csv`（X10 值，合计 200.0 / 377.009 Mt/a）；`co2_storage_caps` 新增 `iea_anchor_200` / `project_ramp_377`（直接取年上限，空单元格报错）；新键 `research.co2.extra_asean_capacity_mt: null`（主值不设上限；数值 / 按国字典 → e_nom_max；0 = 不建储罐与链路）。注册表链重跑：`v4_biomass_overflow_cap_share`（baseline）与 `v4_pks_in_mill_share`（①7 改过的 `v4_biomass_potential.py`）两行 SHA 变。测试 91 passed（`logs/ut_i31.txt`） | 完成：`a1822511`，已推送 |
| 04:04 | **③2 DAC 缩放键（决策 244）**：`cost_scaling.DAC: 1.0`，缩放账本进 v5 meta。**偏离规格：** 两处审计（`s4i_static_audit.py:170`、`s4c_1_cost_audit.py:86`）对任何 carrier 都不读缩放因子，未改，写入局限（X21 用非 1 因子时需同步改）。注册表链重跑。测试 77 passed（`logs/ut_i32.txt`） | 完成：`8fe90d20`，已推送 |
| 04:07 | **③4 配电网与负荷母线（决策 244；Q3 (b)、Q4 (a)、Q5 (a)）**：`v5_layers.apply_distribution_grid_v5` 在 AC 损耗层之后调用（损耗层拒绝已有 reversed 链路与零长度）；同步钩子按 `reversed` 标志自动收集配对（VERIFIED，`s4j_layers.py:166-179`），不需新列表；负荷不缩放；需求账本 bus 列同步；LV 母线缺 location 时补节点名。测试 56 passed（`logs/ut_i34.txt`） | 完成：`26b86a77`，已推送 |
| 04:09–04:21 | **预构建与 Q12**：pre1（v5 主集，D 盘 `builds/pre1`）在专用电厂层停（决策 180：Truong Son 一期 250 MW 经 ②5 新进入，GEM 占位坐标同二期，落在 LA2 1，状态表无此身份）。修正：v5 时状态表缺的身份取其 gem_status（同为 GIPT 2026-09）；②6 扩展第 6 行（一期，同证据）；坐标更正对缺席机组记账跳过。pre2 构建通过（2:17.9，1.07 GB，构建内静态检查通过）。**Q12（规则先定后算）：** E(节点平均) 0.02707 < E(最好等级) 0.03585 → 11 国统一节点平均（主值不变）；对照的 0 级 E 0.01225 更小（PH 权重 6,703 MW，Ember PH CF 0.135），按规则不参与选择，写入报告。测试 87 passed（`logs/ut_pre3.txt`） | 完成：`79152d65`，已推送 |
| 04:24 | **③3 EV 智能充电份额（决策 244、Q5 (a)）**：`ev_smart_share: 1.0`（主值不变）；s < 1 时智能部分按 s 缩放，不可调部分为电网侧负荷（充电桩 bus0，÷ 0.9），需求账本拆行；配电网层同时移动该 carrier。s < 1 未做构建验证（局限）。注册表链重跑。测试 74 passed（`logs/ut_i33.txt`） | 完成：`232d4053`，已推送 |
| 04:31 | **③5 燃料舱碳归属 + ④1 导出元数据（决策 244、Q11）**：`v5_bunker_attribution.py` 在 v4 已解网络上 VERIFIED：F1 合成端碳 130.958 Mt、燃料舱 120.13 Mt（X10：130.96 / 约 117–121），F2 131.17 / 120.34 Mt，未归属 0；只计本国燃料舱时 3.54 Mt（`logs/63_…`，`evidence/BUNKER_CARBON_ATTRIBUTION_V4_W14_F{1,2}.*`）。④1：导出前写 `run_status`（V6_PENDING）与 `build_history`（无读取点的键移入、有读取点的复制，`logs/64_…`），B 组门检结果进 `RUN_STATUS.json`（导出在 B 组之前，不改 B4P 步骤顺序）。测试 38 passed（`logs/ut_i35.txt`） | 完成：`e3ccd2d7`，已推送 |
| 04:36 | **注册表**：`v5_x20_registry.py`（新行 103 条、描述更正 30 条，值不变）；DATA_REGISTRY 2,469 → 2,572 行，校验通过；v5 改变其值的 v4 行保留原值，v5 值另起 `v5_*` 行（偏离规格 1.1 (d)、1.12 的"更正原行"写法，理由：v5 关闭时须等于 26c2e47d 构建）。测试 145 passed（`logs/ut_reg.txt`） | 提交中 |
