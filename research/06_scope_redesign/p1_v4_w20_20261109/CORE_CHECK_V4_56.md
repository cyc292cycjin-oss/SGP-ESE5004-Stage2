# v4 W20：核心稳定性的经验检验——次区域集团与去一国（56 时段，本机）（决策清单第 228 项）

## 1. 求解前登记（本节在任何 W20 求解之前提交，求解后不改）

- **授权：** 指令第 0（性质）、4 节——"在 v4 主算 56 时段网络上做至多 17 次求解（第 4 节；用户启动本指令即授权）"。本节登记 17 次，一个联盟一次；不重试、不改参数、不改档案。
- **执行：** 会话模型 `claude-opus-5-5`、effort `xhigh`（开工时用会话元数据确认）。分支 `asean/v4-w20-20261109`（自 W14 头 `ac75354c`；W14 包 `COMMIT` `26c2e47d` 是其祖先，二者之间只改 W14 交付目录，已核对）。

### 1.1 17 个联盟（第 228 项 (a)(b)；顺序 = 求解顺序）

GMS {KH, LA, MM, TH, VN}、LTMS {LA, TH, MY, SG}、BIMP-EAGA {BN, ID, MY, PH} 及三个补集，加 11 个去一国。单国联盟不做。每个联盟的网络由 `scripts_project/v4_coalition.py` 从 W14 包一体化网络（`86f6d6a0…`）构建、按 `--truncate 56` 同一规则截取（规则、测试、构建统计、静态检查见 `COALITION_BUILD.md`；网络 SHA256 见 `tables/W20_XS_PRE.csv` 与 `evidence/STATIC_CHECKS_W20.json`，运行器按登记的 SHA256 核对后才求解）。燃料舱（第 12 个参与者）不属于任何联盟：17 个联盟网络都不含燃料舱负荷与账户。

### 1.2 c(S) 与 x(S)

- **c(S)：** 联盟网络 56 时段求解的目标值（含目标常数项，即 `SOLVE_RECEIPT.json` 的 `objective`；与 12 个参与者份额加总所对的一体化目标值同一口径）。
- **x(S) = Σ_{i∈S} x_i：** x_i 取 v4 主算 56 时段一体化解的 M12 Owen **对偶形式总成本分配**（α 0.5），读自 D2c 冒烟 R1 的 `m12_owen/OWEN.json`（`results_project/v4d2c/smoke56/v4d2c_F1/`，运行网络 `db33f84e…`）。W14 已证明其 56 时段网络与 D2c 冒烟网络逐组件相同（只差元数据中的构建路径），本地演练目标值相对差 0，所以这是 W14 网络的同一解。M12 已写出总成本分配，无需重算。
- **恒等式核对（指令第 3 节，VERIFIED）：** 11 国 + 燃料舱份额之和 363,190,034,301.60 EUR，目标值 363,190,038,821.08 EUR，**差 −4,519.48 EUR，|差| ≤ 0.01 bn：通过**（OWEN 自身的对偶形式验收、残差影响、Owen 前提也都为 True）。x_BUNKER = 85,724,433,731.87 EUR；11 国之和 x(N) = 277,465,600,569.73 EUR。
- **α 区间：** 只有一端在 S 的跨境国家对（`pair_values_eur`，该对行的 y′b 与该对的目标常数）随 α ∈ [0, 1] 变化，x(S) 在 x(S, 0.5) ± 0.5 Σ|v| 之间；S 内部的国家对互相抵消。
- **市场形式（并列报告，第 184 项由师哥判断主次）：** OWEN.json `market_form.allocation_alpha_half_eur` 之和；它不受 Owen 定理保证。
- **D8 加回（并列报告，不作判据）：** 被移除的边界存量设施的 α 0.5 份额 FOM（`COALITION_BUILD.md` 第 2 节）；c(S) + D8 只会使余量更大。

### 1.3 判定（第 139 项，事前登记）

- 违反量 x(S) − c(S) **> max(1 % × c(S), 0.01 bn)** 才算违反；在此之内记为"在容差内成立"；x(S) ≤ c(S) 记为"严格成立"。判据只用对偶形式 α 0.5；α 区间端点、市场形式、D8 加回并列给出。
- **任一违反：停下交审阅端**，不改模型、不改参数、不重试，其余联盟不再求解（运行器在每次求解后按本节规则判定，`scripts/w20_eval.py`）。
- **非 optimal：** 记录终止状态与 Gurobi 状态，不重试，继续下一个；返回了目标值的非 optimal 运行同样按上式判定并标注（若它显示违反，也停下）。**不可行：** 先查结构原因（成员国合计无封存去向、无液体燃料来源等，`STATIC_CHECKS_W20.json` 的 `sinks` 给出各成员国的 CO₂ 去向与液体来源），属结构原因的记为 c(S) 不可达、条件平凡成立，不计为违反。
- **去一国的第 141 项口径：** x_i ≥ c(N) − c(N∖{i})。本步的联盟网络都不含燃料舱，不含燃料舱的全体联盟不在 17 次之内，所以 **c(N) 取 11 国份额之和 x(N) = 目标值 − x_BUNKER = 277.4656 bn**；于是第 141 项余量 x_i − [c(N) − c(N∖{i})] 与核心余量 c(N∖{i}) − x(N∖{i}) 恒等。与第 141 项（v2 56×3h，M12b）对照时须注意：M12b 的 c(N − i) 含燃料舱，口径不同。

### 1.4 登记值

| # | 联盟 | 成员 | 数 | 保留存量跨境（线 / 链路；国家对） | x(S) 对偶形式 α 0.5 | α 区间 | x(S) 市场形式 | 阈值（求解前估计 ≈ 1 % × x(S)） | D8 加回 M |
|---:|---|---|---:|---|---:|---|---:|---:|---:|
| 1 | GMS | KH LA MM TH VN | 5 | 22（13 / 9；KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH） | 106.0048 | [106.0020, 106.0075] | 106.0048 | ≈ 1.060 | 1.166 |
| 2 | LTMS | LA MY SG TH | 4 | 20（11 / 9；LA–TH MY–SG MY–TH） | 89.6164 | [89.5960, 89.6368] | 90.1721 | ≈ 0.896 | 1.518 |
| 3 | BIMP | BN ID MY PH | 4 | 1（1 / 0；ID–MY） | 159.2403 | [159.2349, 159.2457] | 159.2403 | ≈ 1.592 | 1.633 |
| 4 | nonGMS | BN ID MY PH SG TL | 6 | 4（2 / 2；ID–MY ID–SG MY–SG） | 171.4608 | [171.4581, 171.4636] | 171.4608 | ≈ 1.715 | 1.166 |
| 5 | nonLTMS | BN ID KH MM PH TL VN | 7 | 1（1 / 0；KH–VN） | 187.8492 | [187.8288, 187.8696] | 187.2935 | ≈ 1.878 | 1.518 |
| 6 | nonBIMP | KH LA MM SG TH TL VN | 7 | 22（13 / 9；KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH） | 118.2253 | [118.2199, 118.2307] | 118.2253 | ≈ 1.182 | 1.633 |
| 7 | minusBN | ID KH LA MM MY PH SG TH TL VN | 10 | 31（16 / 15；ID–MY ID–SG KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH MY–SG MY–TH） | 276.8471 | [276.8471, 276.8471] | 276.8472 | ≈ 2.768 | 0.000 |
| 8 | minusID | BN KH LA MM MY PH SG TH TL VN | 10 | 28（15 / 13；KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH MY–SG MY–TH） | 171.7468 | [171.7451, 171.7485] | 171.7565 | ≈ 1.717 | 0.342 |
| 9 | minusKH | BN ID LA MM MY PH SG TH TL VN | 10 | 28（13 / 15；ID–MY ID–SG LA–MM LA–TH LA–VN MM–TH MY–SG MY–TH） | 273.4940 | [273.4899, 273.4981] | 273.8160 | ≈ 2.735 | 0.823 |
| 10 | minusLA | BN ID KH MM MY PH SG TH TL VN | 10 | 14（5 / 9；ID–MY ID–SG KH–TH KH–VN MM–TH MY–SG MY–TH） | 277.1178 | [277.1147, 277.1210] | 277.1378 | ≈ 2.771 | 9.955 |
| 11 | minusMM | BN ID KH LA MY PH SG TH TL VN | 10 | 27（15 / 12；ID–MY ID–SG KH–LA KH–TH KH–VN LA–TH LA–VN MY–SG MY–TH） | 274.9999 | [274.9849, 275.0148] | 274.9286 | ≈ 2.750 | 0.039 |
| 12 | minusMY | BN ID KH LA MM PH SG TH TL VN | 10 | 24（13 / 11；ID–SG KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH） | 240.6990 | [240.6919, 240.7061] | 240.6893 | ≈ 2.407 | 1.974 |
| 13 | minusPH | BN ID KH LA MM MY SG TH TL VN | 10 | 31（16 / 15；ID–MY ID–SG KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH MY–SG MY–TH） | 261.3292 | [261.3292, 261.3292] | 261.3292 | ≈ 2.613 | 0.000 |
| 14 | minusSG | BN ID KH LA MM MY PH TH TL VN | 10 | 28（15 / 13；ID–MY KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH MY–TH） | 265.6031 | [265.6005, 265.6058] | 265.6031 | ≈ 2.656 | 0.466 |
| 15 | minusTH | BN ID KH LA MM MY PH SG TL VN | 10 | 8（5 / 3；ID–MY ID–SG KH–LA KH–VN LA–MM LA–VN MY–SG） | 236.8261 | [236.8061, 236.8461] | 236.2601 | ≈ 2.368 | 10.601 |
| 16 | minusTL | BN ID KH LA MM MY PH SG TH VN | 10 | 31（16 / 15；ID–MY ID–SG KH–LA KH–TH KH–VN LA–MM LA–TH LA–VN MM–TH MY–SG MY–TH） | 277.1076 | [277.1076, 277.1076] | 277.1076 | ≈ 2.771 | 0.000 |
| 17 | minusVN | BN ID KH LA MM MY PH SG TH TL | 10 | 29（15 / 14；ID–MY ID–SG KH–LA KH–TH LA–MM LA–TH MM–TH MY–SG MY–TH） | 218.8854 | [218.8841, 218.8868] | 219.1807 | ≈ 2.189 | 0.663 |

| 去一国 | x_i 对偶形式 | x_i 市场形式 | c(N) := x(N) |
|---|---:|---:|---:|
| BN | 0.6185 | 0.6185 | 277.4656 |
| ID | 105.7188 | 105.7091 | 277.4656 |
| KH | 3.9716 | 3.6496 | 277.4656 |
| LA | 0.3478 | 0.3278 | 277.4656 |
| MM | 2.4657 | 2.5370 | 277.4656 |
| MY | 36.7666 | 36.7763 | 277.4656 |
| PH | 16.1364 | 16.1364 | 277.4656 |
| SG | 11.8625 | 11.8625 | 277.4656 |
| TH | 40.6395 | 41.2055 | 277.4656 |
| TL | 0.3580 | 0.3580 | 277.4656 |
| VN | 58.5802 | 58.2849 | 277.4656 |

表中阈值一列只是求解前的量级（真正的阈值按求解后的 c(S) 计算）。去一国的 α 区间对去 BN、PH、TL 为单点（BN–MY、MY–PH、ID–TL 的国家对值为 0）。

### 1.5 预期

- **审阅端（第 228 项）：** 17 个条件全部在阈值内成立；余量最大的应是去 ID 与三个补集，最小的可能是去 BN、去 TL 或 LTMS。
- **执行方（INFERENCE，不作判据）：** 17 个全部严格成立（余量 ≥ 0）。去一国中 BN、TL、PH、SG 的余量最小（与 M12b 的 BN +0.002、TL +0.021 bn 同量级）：BN、PH、SG、TL 去掉后不拆任何穿越国界的 KVL 回路，物理博弈与矩阵博弈相同，定理直接保证；余量最大的是去 ID（ID 的 x_i 105.7 bn 中含大量为他国承担的 CO₂ 封存与燃料供应价值）与去 MY、去 VN、去 TH。集团中 LTMS 与 GMS 的余量小于其补集（SG 无本国封存、LA 为内陆国），BIMP 有 ID、MY 的封存，余量居中。不可行的可能性低：17 个网络的每个成员国都至少有一条 CO₂ 去向（本国封存、区外封存或联盟内他国封存，`sinks`，VERIFIED）；LTMS 与去 VN 中老挝没有来自其他成员的液体燃料链路（只能由本国节点生产合成燃料），c(S) 中老挝的液体燃料成本因此较高——这是定义的一部分，不是错误。
- **求解量级（INFERENCE）：** 去一国网络为全网的 55–95 %，每次 2–7 分钟、峰值 3–7 GiB；集团网络更小。17 次求解加间隔约 3 小时墙钟，求解本身约 1.2–1.6 小时。

### 1.6 运行设置（`scripts/w20_solve.sh`）

档案 `formal_barrier_1e6_t16`（Threads 16），`--scaling on`，`--truncate 56`（网络已按同一规则截取，LP 与冒烟路径逐字节相同，`logs/lpcheck.txt`），Gurobi TimeLimit 3,000 s，墙钟 3,600 s（进程组终止），标签 `SMOKE_TEST_ONLY`；每次求解前令牌服务器 TCP 预检，串行，间隔 ≥ 330 s，同一时刻至多 1 个 Gurobi 进程，有 pytest 或其他求解 / 构建进程时不启动；许可只经 `GRB_LICENSE_FILE` 传给求解进程。每次求解后：违例分析与 C1 精度（`l23_violation_analysis.py`、`s4o_c1_precision.py run`，只作质量证据），再按 1.3 判定。成本表取 W14 构建的 `costs_active_research.csv`（只用于导出，不进入 LP）。
