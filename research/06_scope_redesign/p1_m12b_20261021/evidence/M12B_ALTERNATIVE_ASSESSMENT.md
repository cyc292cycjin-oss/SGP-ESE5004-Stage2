# M12b 第 4 节：备选方案"跨境交流线改为可控联络线"评估（只评估，不实施）

等级：代码位置为 VERIFIED（只读检索，关键行号已抽查）；工作量与影响为 INFERENCE / PROPOSED。数据来自 M08b 补充 01 一体化 2920×3h 网络（bca20fc0…，`M12B_CROSS_BORDER_BRANCHES.json`、`M12B_KVL_LOOPS.json`）。

## 4.1 方案内容

把跨境交流线（两端母线属于不同国家的 `Line`）改成不参与 KVL 的可控 `Link`（运输模型，类似 NTC / HVDC：`p_max_pu = s_max_pu`、`p_min_pu = −s_max_pu`，或按现有有损双向拆分），国内交流线保留 KVL。这样 KVL 回路全部落在一国内部；去掉任何一国只删除该国自己的回路，其余国家的回路与 KVL 行不变，物理联盟与矩阵博弈一致，Owen 定理（y′b 在核心内）对去一国联盟重新严格成立。

## 4.2 跨境交流线的数量与容量（VERIFIED）

- 跨境交流线 62 条（全部 `carrier = AC`，线型 Al/St 240/40 4-bundle 380 kV），分布在 12 个国家对；全部可扩建；存量 `s_nom` 合计 2,570 MW；单条扩建上限 20,000 MW（PyPSA-Eur `max_extension`），上限合计 1,242,570 MW。国内交流线 86 条。
- 跨境直流链路 10 条（5 对 × 正反向：ID|MY、ID|SG、MY|PH、MY|SG、MY|TH；存量只有 TH–MY 300 MW × 2 = 600 MW），本来就是可控链路，不参与 KVL。

| 国家对 | 交流线条数 | 存量 MW | 长度合计 km |
|---|---|---|---|
| BN\|MY | 1 | 0 | 63 |
| ID\|MY | 10 | 230 | 4,370 |
| ID\|TL | 1 | 0 | 256 |
| KH\|LA | 2 | 300 | 578 |
| KH\|TH | 4 | 250 | 1,568 |
| KH\|VN | 6 | 200 | 1,871 |
| LA\|MM | 2 | 30 | 709 |
| LA\|TH | 16 | 955 | 6,232 |
| LA\|VN | 9 | 0 | 3,287 |
| MM\|TH | 8 | 0 | 4,696 |
| MY\|SG | 1 | 525 | 240 |
| MY\|TH | 2 | 80 | 549 |
| **合计** | **62** | **2,570** | |

- KVL 回路：全网 71 个（= LP 中 KVL 行 3,976 / 56 时段）；其中纯国内回路 18 个（ID 9、MM 5、KH 3、TH 1），其余 53 个经过跨境线。改为联络线后每时段 KVL 行由 71 降到 18（INFERENCE：图的回路空间维数）。

## 4.3 需要改动的代码位置与工作量

现有代码没有"线改链路"开关（检索 `line_to_link`、`as_link`、`NTC`、`transport model`、`controllable` 均无命中）。

| 位置 | 现在做什么 | 需要的改动 |
|---|---|---|
| `scripts_project/s2_network.py:384–386`（`tag_cross_border` → `apply_cross_border_switches_s2` → `set_transmission_s2`） | 跨境标记、开关、存量下限、存量 FOM 台账 | 新转换函数插在 385 与 386 之间（须在 `pipeline_candidates`（约 328 行）与 `apply_cost_layer_s4c1`（382 行）之后、`apply_max_extension` 与损耗步骤之前）；元数据键与回执 |
| 新函数（如 `s4x_layers.apply_cross_border_links`） | — | 删跨境 Line、加 Link（复制 capital_cost、length、p_nom、p_nom_min、underwater_fraction、border_class、transport_carrier）；先用 `s4k_layers.line_lambda` 算损耗系数；改写内存中的走廊表与 `n.meta["existing_cross_border_fom_ledger"]` 的 `component_type`；约 60–90 行 |
| `s2_network.py:147–172` 静态检查 | 未标记链路报错；走廊集合必须与网络一致 | 新链路须带 `border_class`；走廊表改写后检查自然通过 |
| `s4f_layers.py:63`、`:87`（`apg_plan_groups`、`apply_max_extension`） | 只处理 `carrier == "DC"` 的链路 | 纳入转换后的链路（2 处） |
| `s4j_layers.py:37–41, 108–195`（`LOSS_EFFICIENCY`、`apply_transmission_losses`、`loss_summary`） | 只拆分登记过的载体（DC、管道） | 为转换链路加分支（逐线效率、双向拆分、无压缩）；`research_lossy_bidirectional_sync`（166–179）通用，无需改 |
| `s4k_layers.py:90–158`（AC 损耗代理 `Line-loss_proxy`） | 只作用于 `n.lines` | 自动只剩国内线；**语义差异**：代理为 loss ≥ λ\|s\| 两端各半，链路效率 1 − λ 只在受端扣；`pypsa_tangent` 模式无链路对应 |
| `s4l_layers.py:137–155`（`identical_link_groups`） | 合并相同的零容量可扩建链路 | 排除跨境电力链路，否则候选线被合并后走廊集合检查失败 |
| `s4d_ledger.py:128–130, 178–188`；`m12_allocation.py:211–264`；`m12_rhs_audit.py:198–217` | 存量 FOM 按 `component_type` 取；按长度份额键为 `Line:<名>` | 份额表 `XB_LENGTH_SHARES_S4H2.csv` 只有 62 行 `Line:`，转换后会静默退回 0.5 / 0.5——加 `Line:` 回退或重生成份额表（各 2–3 行） |
| `s4m_cost_breakdown.py:119–126` | 只有 Line-AC 与 Link-DC 分支 | 加 Link-AC 分支（诊断用） |
| `configs/research/baseline.yaml` + 注册表 | — | 新键（如 `research.network.cross_border_ac_mode: kvl \| transport`），注册表行 |
| 通用、无需改 | — | `apply_wacc_mode`（AC 载体的 Link 已按 HVAC 计）、`m08a_layers.apply_remove_countries / apply_stock_mode`、`v5_gates` B5、`gates_v6`、`l23_violation_analysis`、`s4o_c1_precision`、`s3b_scaling` KVL 行归一化 |

工作量（INFERENCE）：生产代码约 120–200 行、8–10 个文件，新测试文件约 100–150 行（两国玩具回路：线变链路、KVL 行中无跨境线、双向拆分与同步钩子、走廊 / FOM 改写、长度份额回退、合并保护、不互联情景不变、配置默认值）；开关默认关闭时现有测试不受影响。

## 4.4 对重建与测试的影响

- 新配置键进入研究配置哈希与 GATES_V6 G2.2 子集哈希（`SUBSET_KEYS` 已含 `network` / `cross_border`）→ 两种情景、两种分辨率共四个网络都要重建（不互联网络物理上不变，但哈希变）；去一国变体、云端包都要重做；冒烟需重跑（另行授权）。
- 若作为主算设定：11 个读取冻结构建的测试（`test_s4e_1`、`test_s4h_1`、`test_s4h_2`、`test_s4g_1`、`test_s4f_1`、`test_s4f_2`、`test_s4k_1`、`test_s4j_2`、`test_s4d_4`、`test_s4c_1`、`test_s1_built_networks`）的期望要随新构建更新；若冒烟网络也按新设定重建，`test_m12_allocation.py` 中依赖 KVL 跨国转移的网络测试断言要改（跨国 KVL 转移归零）。
- M12 的市场形式 − 对偶形式差额中跨国部分（KVL 回路转移）消失，两种形式只差 KKT 残差。

## 4.5 与 PyPSA-Eur 做法的偏离程度

- PyPSA-Eur 对交流跨境线保留 KVL（交流网络是一个整体同步区，线路为被动支路；只有直流线 / 背靠背为 `Link`）。本方案把 62 条跨境交流线（存量 2,570 MW，扩建上限 1.24 TW）改为可控链路，偏离 PyPSA-Eur 的电网物理口径：跨境环流（经第三国的回路潮流）不再表示，跨境容量可被完全利用，倾向于高估互联价值（B6 偏高），且偏差随扩建规模增大。
- 偏离程度：涉及全网 71 个回路中的 53 个（75 %），属结构性偏离，不是参数调整。东盟实际跨境互联多为点对点、规模有限的交流 / 直流联络（APG 项目以双边购电协议运营，接近 NTC 口径），这一点可作为采用运输模型的依据（INFERENCE，未核文献）。
- 折中方案（PROPOSED，未评估）：只把 Owen 检验中违反量超标的国家对改为联络线；或主算保留 KVL，Owen 只在运输模型敏感性下报告。
