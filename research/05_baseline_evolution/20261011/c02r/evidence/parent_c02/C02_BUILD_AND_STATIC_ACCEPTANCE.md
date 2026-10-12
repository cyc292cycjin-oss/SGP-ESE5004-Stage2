# C-02受控日网络与LP构建：真实结果

**C02_BLOCKED_WITH_SPECIFIC_EVIDENCE**。本轮已在122号机完成一次日网络组装和一次完整Linopy模型创建，但Store动态行RHS检查拒绝了binary64位差，未完成全矩阵导出、行界回读及日V4正式绑定。没有任何优化、presolve、IIS、feasRelax、Gurobi原生模型或WLS环境启动。不能申请C-03；没有自动重建。

## 1. 冻结身份、实例及唯一执行

- C01R审计基线 `68ebb96b7d48318654e9ca3f2b2780a0133bc889`；Scheme A PR #4固定对象 `8883de6fb3e15767c632ac92f535e8a423e90b69`，没有合并历史PR。
- 协议/规则、Scheme A、V4、原NetCDF和稳定资产成本微扰账的完整SHA见 `C02_INPUT_AND_ENVIRONMENT_MANIFEST.json`、`evidence/deployed_identity/INPUT_MANIFEST.json`。Scheme A从固定Git对象提取，原科学输入和历史Gate6不覆盖。
- 用户最终确认westb:40516；ED25519公钥严格匹配可信指纹后才使用既有身份认证。实际主机 `autodl-container-21104cb00b-43be1fed`；122的实际身份独立记录，没有复制379启动授权。密钥及许可证内容未读取、复制或提交。
- Python3.11.13 / PyPSA0.30.3 / Linopy0.5.5 / NumPy1.26.4 / SciPy1.15.2 / pandas2.3.1 / xarray2025.1.2 / netCDF4 1.7.2 / psutil7.0.0，40项部署SHA通过。未安装或升级环境。
- Run：`c02_daily_build_20261012T025604Z_fcc0f784`。启动 `2026-10-12T02:56:04.048301+00:00`，固定截止 `2026-10-12T03:26:04.048301+00:00`。构建消费标记保留；worker4168、supervisor4167、guard4169均已退出，事后逐PID核实不存在。

## 2. 实际完成与未完成

| 要求 | 真实结果 | 证据/限制 |
|---|---|---|
| 新365日未求解网络 | VERIFIED，已导出并回读 | `NETWORK_READBACK.json`；365×24h，objective/generators/stores各8760h |
| C01R日值 | VERIFIED | 1737 Load、460 CF、40 inflow逐资产日值SHA与已接受账一致；1641平坦、96时变Load，不补差或裁剪 |
| Scheme A | VERIFIED at network/source level | 180项Q按批准hex；627不变；Store两字段、route cap、外置账同步；385/385精确D≤Q′；没有重新积分派生Q |
| 非白名单科学变更 | 网络层未发现 | 静态表与元数据精确对照；只有批准Q、时间维度/聚合及3个来源元数据字段；未删约束或加路径 |
| Linopy +研究hooks | 已创建 | 持久化标签合计 **2,450,005列、6,042,238有效行**；无求解 |
| 完整稀疏矩阵、行界、R及非零元 | **未完成** | 在导出CSR块之前失败，NNZ UNKNOWN；不能把标签数称为完整矩阵回读 |
| 实际Scheme A LP初始/末端/Bus行 | **未完成** | 第一个Store动态RHS检查停止；源/网络通过不等于所有实际LP常数通过 |
| 日科学/V3目标及D | 部分真实数组已落盘 | 新日维度系数和列界写出，未复制旧V3数组；资产微扰取稳定账，无重抽；完整目标/offset回执未落盘 |
| 正式日V4身份 | **未生成** | `DAILY_V4_BINDING_STATUS.json`仅阻断记录，不能用于执行；原V4公式/阈值保持 |
| V4合成测试 | 10项本地无求解通过 | 365日库存、Bus、KKT、自由RC、互补性、维数及未知家族拒绝；不是真实日解验收 |
| 全LP静态验收/物理可行/KKT | 未完成/未执行 | 无X/Pi/RC，不产生虚构PASS；日聚合不是2920模型等价变换 |

本次新NetCDF SHA：`b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2`，21,259,211 bytes。三权重值24及总和8760均在导出后回读。实际Scheme A日组账见 `evidence/original_run/artifacts/SCHEME_A_DAILY_EXACT_GROUPS.json`。

## 3. 停止原因与证据等级

**VERIFIED**：`BUILD_RESULT.json`与worker.log一致，失败在已冻结本轮 `c02_model.py:210`：`bits(rhs, np.r_[-q, np.zeros(364)])`，错误 `ValueError: binary64 differs`。`bits()`用uint64表示比较，负零与正零不同。

**VERIFIED / DERIVATION**：云端真实PyPSA源码 `constraints.py:927` 为 `rhs = -e_init.where(~include_previous_e, 0)`。独立微型数组计算仅执行该RHS表达式，在非循环Store后续时段得到−0.0，而检查器期望+0.0；数值严格相等但位比较失败。这证明新检查器存在会误拒绝合法零的缺陷，不涉及V4阈值或科学容差。

**NOT_PROVEN**：失败进程已释放，没有逐元素RHS转储；不能声称已排除当时RHS的所有其他差异。没有为补证重新创建日模型。完整生产行系数、行界和offset仍未保存；也没有据此次异常判定数学不可行。

证据：`evidence/C02_SIGNED_ZERO_FORENSICS.json`、`evidence/PYPSA_STORE_SOURCE_EVIDENCE.json`、原异常栈及冻结代码SHA。PROJ数据库警告、2163个Link carrier未定义提示和efficiency3静态NaN警告在worker日志原样保留；模型创建继续完成，停止栈不指向这些警告。没有通过import成功宣称地理功能已验证，也未重建环境。

仅提出的后续修复：对**约束语义比较**采用不容忍任何非零误差的精确数值相等，单独记录±0；输入文件和导出回读继续保留逐位/SHA检查，并在停止前保存首个差异资产、行号和hex。**本轮未修改已执行版本，也未重新运行**。一次新完整构建应在用户审阅后另行批准。

## 4. 实际家族及约束覆盖边界

以下从已写出的label数组只读计数；证明家族/行标签实际存在，不代替全部系数、方向和RHS验证。`C02_CONSTRAINT_COVERAGE.json`保留完整记录。807个资源方向块各365行、196项电池容量耦合已实际生成，hooks新增名称集合检查通过。现存FOM只使用冻结常量变量和同一年度系数；没给资本或FOM重复乘24/365。严格offset重新核算代码已执行至返回，但其值未被最终回执持久化，因此最终目标完整性仍PENDING。

| 家族 | 原始块数 | 有效行标签数 |
|---|---:|---:|
| Generator-ext-p_nom-lower | 1 | 838 |
| Generator-ext-p_nom-upper | 1 | 438 |
| Line-ext-s_nom-lower | 1 | 105 |
| Line-ext-s_nom-upper | 1 | 0 |
| Link-ext-p_nom-lower | 1 | 3,263 |
| Link-ext-p_nom-upper | 1 | 0 |
| Store-ext-e_nom-lower | 1 | 297 |
| Store-ext-e_nom-upper | 1 | 0 |
| Generator-fix-p-lower | 1 | 8,030 |
| Generator-fix-p-upper | 1 | 8,030 |
| Generator-ext-p-lower | 1 | 305,870 |
| Generator-ext-p-upper | 1 | 305,870 |
| Line-ext-s-lower | 1 | 38,325 |
| Line-ext-s-upper | 1 | 38,325 |
| Link-fix-p-lower | 1 | 34,675 |
| Link-fix-p-upper | 1 | 34,675 |
| Link-ext-p-lower | 1 | 1,190,995 |
| Link-ext-p-upper | 1 | 1,190,995 |
| Store-fix-e-lower | 1 | 294,555 |
| Store-fix-e-upper | 1 | 294,555 |
| Store-ext-e-lower | 1 | 108,405 |
| Store-ext-e-upper | 1 | 108,405 |
| StorageUnit-fix-p_dispatch-lower | 1 | 15,695 |
| StorageUnit-fix-p_dispatch-upper | 1 | 15,695 |
| StorageUnit-fix-p_store-lower | 1 | 15,695 |
| StorageUnit-fix-p_store-upper | 1 | 15,695 |
| StorageUnit-fix-state_of_charge-lower | 1 | 15,695 |
| StorageUnit-fix-state_of_charge-upper | 1 | 15,695 |
| Bus-nodal_balance | 1 | 1,255,235 |
| Bus-meshed-nodal_balance | 1 | 1,460 |
| Kirchhoff-Voltage-Law | 1 | 11,315 |
| StorageUnit-energy_balance | 1 | 15,695 |
| Store-energy_balance | 1 | 402,960 |
| GlobalConstraint-lv_limit | 1 | 1 |
| ResearchStoreDirection | 807 | 294,555 |
| ResearchBatteryNominal | 196 | 196 |

三个扩建名义容量上界家族零行已核明：105条Line、3263条Link及297个Store均使用实际云端PyPSA schema的+Inf默认名义上界，NetCDF省略这些全默认字段，因此没有有限上界行。见 `evidence/C02_ZERO_ROW_BOUNDARY_CHECK.json`。这只解释三类零行，不是完整逐系数覆盖PASS。

## 5. 资源、时限及进程保全

- 有效CPU配额12核，cpuset0–47/affinity48不是48核额度；cgroup v1内核层级有效限制90GiB。宿主命名空间外祖先不可直接读取，未声称已检查不可见宿主配置。
- 启动磁盘 29.775GiB；本轮最低 29.495GiB。RSS≤75GiB、cgroup余量≥12GiB、盘≥8GiB、独立guard覆盖网络组装和Linopy全过程。
- 120次约0.5秒样本；worker历史最大RSS（最后阶段回执） 2.583GiB；进程树采样峰值 2.508GiB；cgroup记录峰值 2.910GiB。采样峰值不能视作未采样瞬间的精确上界；cgroup峰值是内核累计值。
- 启动至失败 60.236s，至轻量云端封存 61.170s。单独create_model精确耗时未在失败回执持久化，UNKNOWN；不以总耗时替代。
- worker退出1，guard退出0，supervisor无资源/期限停止原因；没有信号升级、OOM或资源保护触发。固定1800秒窗口未延期、未滚动重置，实例未关机或释放。
- 本地已完成20项必要无求解检查（其中10项V4合成）；它们没有发现后续实际RHS的±0问题，不把先前测试通过写成端到端成功。

## 6. 云端/本地保存与完整性

云端Run：`/root/autodl-tmp/SGP/runs/c02_daily_build_20261012T025604Z_fcc0f784`。

- 新NetCDF与原始轻量回执/日志已下载到 `D:/ResearchWorkspaces/ASEAN/work/c02_daily_build_20261012/cloud_evidence/`，逐文件SHA与云端只读索引一致。
- 原始轻量封存ZIP SHA `d691617f619cf3797eb8d1a173c2fe80cafb5fd65dfaeab26c1d0f57baf0256e`，CRC及全部成员SHA通过。
- 部分列数组和标签保留云端，合计 276,976,761 bytes，本地未同步部分明确 **LOCAL_SYNC_PENDING**，不是完整LP备份。精确路径/大小/SHA见 `C02_LOCAL_SYNC_AND_PARTIAL_ARTIFACTS.json`。
- 原自动云端索引曾引用 `ARTIFACT_SHA_INDEX.json`，但失败时未生成；原件保留不改，本轮独立事后SHA索引补充**已有**部分产物身份，不补造不存在的完整矩阵。
- GitHub和审阅ZIP不含NetCDF、标签数组、矩阵、大向量、许可证、私钥或访问凭据；只含报告、轻量证据和代码。不能根据封存ZIP成功声称完整LP已保全。

## 7. 后续门槛与停止

阻断只有一条实际执行链：新RHS检查器失败，使完整CSR/行界/目标offset/DAILY_V4_BINDING未完成。必须先审阅表示检查的最小修复，再决定是否批准一次新的build-only窗口。此处不扩大科学审查或开展求解参数研究。

未来C-03仍须在C-02完整静态通过并单独授权后，完成真实WLS合法环境、Gurobi版本/参数、同一实际日模型的完整原生载入与逐值回读、资源/截止/唯一调用及RAW优先保全核查；本轮这些项目均未启动。2.91GiB构建峰值不能证明Barrier内存够用或收敛。

G6-05继续 **PAUSED_BY_USER**，C-03与全年Gate6未执行/未授权。原冻结LP、Scheme A/V3/V4/P2、旧结果和消费标记保留。完成报告/GitHub/ZIP后停止，等待用户与ChatGPT联合审阅。
