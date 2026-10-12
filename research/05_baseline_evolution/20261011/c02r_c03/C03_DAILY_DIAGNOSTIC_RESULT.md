# C03 365日诊断真实结果

**OPTIMAL_BUT_NOT_ACCEPTED**。2026-10-12在122号机完成唯一一次C02R日LP构建和唯一一次C03优化。Gurobi返回码0、Status=2、SolCount=1；69次Barrier迭代，Runtime **155.370942831秒**。完整原生X/Pi/RC优先落盘后执行日V4，存在物理与KKT超限，不能认定日模型科学PASS，更不能认定2920时段Gate6 PASS。没有重试、调参、修补解或放宽阈值。

## 1. 身份、授权与实际执行链

- Run：`c02r_c03_daily122_20261012T044259Z_25e62c10`；云端`/root/autodl-tmp/SGP/runs/c02r_c03_daily122_20261012T044259Z_25e62c10`。
- 新分支`codex/c02r-c03-daily-diagnostic-20261012`，父提交`291fcd057e14a73eb093a986348846a74f8e40eb`；实际生产代码提交`a3c1f5e97e03b99f4fa5fa885f6fe0747768d7d7`已push，独立[PR #13](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/pull/13)，未合并。
- 合并授权SHA `2dd5b182445ace1928a2358e0b599f656ae34e4c8f42e18e62df0e2da691f5a3`。先核残留进程、旧Run与持久消费标记；新身份只消费一次。真实调用证据为NATIVE_CALL_EXIT、原生日志及原始Status，而非仅凭claim。
- 122实际hostname `autodl-container-21104cb00b-43be1fed`；12核CPU配额、90GiB有效cgroup-v1上限，Python3.11.13、PyPSA0.30.3、Gurobi12.0.3。可信ED25519验证通过；未复用379身份。
- Scheme A固定提交`8883de6fb3e15767c632ac92f535e8a423e90b69`、Manifest `a94f4ce099be43f080378a677cfabb5eb48561f6813bed2dcfb751ed6c2e9720`；C01R协议`661a81e532184003938213a3e81ad35bd4a687108332d14b3582bf7a8eac2856`；V4父SHA `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`。
- 复用已封存未求解日NetCDF `b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2`，不重复聚合、重新派生Q或重建2920模型。旧solver_allowed=false等产物provenance原样保留，新授权另存。

## 2. C02R修复、静态门槛和原生交接

两项限定补丁实际生效：有限约束语义以零容差精确数值比较接受±0；源数据/SHA/序列化位身份仍严格。仅对资产上界、默认值和标签掩码共同证实的Line/Link/Store-ext nominal-upper三个+Inf零行家族放行。非零1ULP、NaN、shape/方向/有限界错误和未知缺行仍拒绝。45项无求解接口及正反例测试通过，不冒充真实科学验收。

实际生成 **2,450,005列、6,042,238行、11,403,496非零元**，36个家族覆盖表中包含3个有直接证据的有效零行家族；807资源方向、196电池容量耦合、402,960 Store动态、15,695 StorageUnit动态、Bus、多端口、KVL及lv_limit已导出回读。两个可选家族缺席的原因分别为冻结external_annual_caps为空、existing-resource groups无candidates。

Scheme A 180账户及四字段同步、其余627不变；385组精确D≤Q′，实际LP源行界检查通过。1,737 Load、460 CF、40入流匹配已接受日值SHA；365个快照的三类权重均24，全年各8760。成本/端口/效率/政策无非白名单变化。此日LP与旧2920 LP**不是数学等价模型**。

CSR→CSC→CSR完整稀疏重排核验保持全部条目、行列界、目标与标签。原CSR Manifest SHA `ae24dd48df12fdb042824d7ec070f9153d8432a82e80d1019a41879a7bfa8e72`；实际原生CSC Manifest SHA `f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70`；日mapping SHA `f5bdb465709c0840ad9c370f121b5f23d31f62310300ad7e47208b0b9d6d746e`。实际全矩阵原生载入及逐值回读 **EXACT_READBACK_PASS**，耗时3.866861秒；同一模型句柄进入唯一optimize，日志fingerprint `0xadbe9ee0`。

WLS在昂贵构建前真实GRBstartenv成功并释放；正式原生worker再次成功。无读取/记录许可秘密。154项非秘密数值参数设置/回读，与首次Gate6回执只有授权TimeLimit差异（43199.999811→3600）。Method2、Crossover0、BarConvTol1e-6、Threads4、Seed123、AggFill0、PreDual0、历史200；NumericFocus0、FeasibilityTol1e-6、DualReductions1等保持协议。SoftMemLimit=65十进制GB，MemLimit=1e100默认。未使用P2或G6-05。

## 3. 原生结果与日V4

原生内部Presolve是这一次optimize的一部分；无单独presolve、IIS、feasRelax或测试优化。真实返回UTC2026-10-12T04:51:51.398510Z。原生ConstrVio=6.891766654e-5、DualVio=0.0254763246、ComplVio=803.471944895；这些是原生模型质量属性，不能直接视为原单位物理误差。

日志还实际报告大目标系数与大边界警告：原生矩阵范围约1e-3—1e3，目标2e-1—8e9，列界6e-1—6e9，RHS3e-6—4e8。这是数值范围证据，不是单独确认根因或更改参数的依据；运行中没有响应警告擅自改参。

| 日V4项目 | 实际结果 |
|---|---|
| 原生OPTIMAL、完整X/Pi/RC | PASS；全部仍标UNQUALIFIED保存 |
| 原单位全矩阵/列界 | **FAIL**：48,298行超限，列界超限0；最大行违约18,298.4059834（最大项为Store库存，MWh） |
| 1,849项工程检查 | 1,470 PASS、379 FAIL；失败含Bus、Store下界及377项资源使用 |
| Bus平衡 | **FAIL**，最大8.320790671 MW |
| Store库存下界 | **FAIL**，最低库存约−18,298.4059834 MWh |
| Store/StorageUnit动态方程 | PASS；最大残差4.09782e-7 / 4.92820e-8 MWh |
| 807资源账户 | **377 FAIL**；年度、终态、库存下界、累计资源上限失败，状态递推各期/前缀/L1本身通过 |
| 385最终义务组 | **111 FAIL**；逐期、总过供和全部交付前缀失败，无总欠供 |
| Stationarity | **FAIL**：4,304列；归一化最大1.869757959e-5，高于1e-6 |
| 对偶符号 | **FAIL**：365项；归一化最大3.802943433e-5 |
| KKT整体 | **FAIL**；互补性最大803.471944895，L1=189,887.484984 EUR |
| 双目标差 | 相对1.968888994e-7低于1e-6；仍披露绝对84,271.2570801 EUR；不能抵消其他KKT/可行性失败 |
| FOM一次计量、双成本核算 | PASS（仅已知成本范围，不表示完整系统经济成本齐全） |
| NetCDF逐值回读及日身份绑定 | PASS；18张动态表；实际解仍不合格 |

资源年度正超用汇总约 **338,137.847468 MWh（0.338138 TWh）**，385组总过供338,137.847467 MWh。二者来自不同核算边界，不相加作为两份损失。最大资源超用资产为`ID:2050:Industry:IndustryFinalEnergy:biomass@ID_Java-Bali1 0 Bagasse fixed resource`：Q=16,183,494.888810169 MWh，释放16,201,793.294793567 MWh，超用18,298.405983398 MWh，V4预算1.619349489 MWh。源级D≤Q′通过不等于候选满足库存非负。

NetCDF回读后全部工程PASS/FAIL及807/385新V4详细回执一致。旧工程浮点汇总有723个派生残差数值略有不同：最大MWh差1.788139343e-7、FOM核算误差变化6.103515625e-5 EUR；未改变任何资格结论。不能把“逐值回读通过”误写成所有重新求和结果逐位相同。前后原始回执均保留。

日V4只适配新维数/标签/时间索引，未改公式、reference或门槛；每个账户仅有一份年度预算，未扣除C01R表示误差、未截断负库存、未修补Bus结果。

## 4. 两套目标与科学解释边界

- 原生ObjVal：428,014,262,628.2498 EUR；独立V3复算：428,014,262,628.28937 EUR，差约0.03957 EUR。
- 原科学已知成本复算：427,765,450,088.104 EUR；微扰贡献248,812,540.18522856 EUR，双账恒等式残差0.0001352131 EUR。
- 日V3 offset独立重算为−12,788,967.997821666 EUR；未硬编码旧offset。科学offset=0。已知固定FOM8,224,491,125.573893 EUR只计量一次。
- `FullSystemCostComplete=false`，NULL资源价格没有被填造；以上是不合格候选的诊断账，**不是获认证的系统最优成本**。V3数值OPTIMAL不证明原未扰动目标严格最优。

已证实：日模型能构建、真实原生精确交接、Barrier能够返回OPTIMAL；本次候选仍不符合冻结日V4。未证明：完整日LP严格可行或不可行、全部失败的唯一根因、2920模型是否能科学通过。与旧Gate6同时改变了Scheme A源版本、时间分辨率和日规模；不能把差异全部归因于聚合，也不能因为377/111计数重现就认定完全相同的成因。本轮到此停止，未展开新的参数研究或运行。

## 5. 固定预算、资源与退出

t0=UTC2026-10-12T04:42:59.952203Z；总截止UTC07:15:29.952203Z（9150秒），阶段持续/累计截止取早，不借用提前结束时间。构建worker356.666秒（create_model部分35.079秒）；原生wall155.372秒；RAW在返回后约0.82秒完成；日V4约97.89秒；worker/guard/supervisor于UTC04:53:31.196165前退出，无遗留PID。云端seal于04:53:39.590061完成，计算至封存639.638秒。

2,463次保护采样：进程树RSS最大4.309307 GiB，cgroup内存峰值6.149261 GiB（内核lifetime high-water，非专属原生精确峰值）；最小余量83.852203 GiB，最小磁盘27.645412 GiB，未触发内存/磁盘/截止/监护异常。原始RESOURCE.jsonl及进程身份回执完整保留。此峰值不能推断2920规模或未来算法内存需求。

实例122保持运行，未关机、释放、扩容或换机；进程结束不意味着停止计费。本次未读取122实际单价，费用NOT_ESTIMATED，不沿用379单价。

## 6. 完整保全与交付

原生X 2,450,005项 / Pi 6,042,238项 / RC 2,450,005项已fsync并SHA保存，资格UNQUALIFIED。

| 原生文件 | SHA256 |
|---|---|
| X.npy | e0c007733546cc6260a11e644493ce64f78af4188c82b0f86fa9f90f655eda2e |
| Pi.npy | 138cbd464a1b2a446758114ae1440cddc08663b2f6d4bb2c05b5c1b3265ae67c |
| RC.npy | 326f198c39cfee22d8b68960a6db19f8eec5a7349fe723c43ff6d053f94ea407 |

云端BACKUP_INDEX：17,417文件、1,946,512,966字节，SHA `eb80de5b50ff64d976d23066c514811fcc4f80f9b768f62ade1b6e1b4282d47d`。完整封存归档314,868,916字节，SHA **`d484db824ce041a81b000484dfe6298d32bfb16145e8dab26db3fd2a6c377019`**；云端路径`/root/autodl-tmp/SGP/incoming/c02r_c03_122_20261012_13a5b85e/c02r_c03_daily122_20261012T044259Z_25e62c10_COMPLETE_EVIDENCE.tar.gz`。源Run与旧所有历史均保留。

云端完整封存及轻量本地证据核验完成，完整本地归档同步为**LOCAL_SYNC_PENDING**。一次SCP下载从UTC04:57:07开始，收尾固定截止UTC05:13:31.196165；截止后下一次5秒身份轮询于UTC05:13:34.509509停止已核身份的本地SCP，检测/停止延迟3.313344秒。固定deadline未修改，没有延长授权或再次下载；计算及科学写入此前已经正常退出。此延迟如实披露，不能写成收尾严格零超时。

本地仅收到239,468,544 / 314,868,916字节，保留为`D:/ResearchWorkspaces/ASEAN/work/c02r_c03_combined_20261012/c02r_c03_daily122_20261012T044259Z_25e62c10_COMPLETE_EVIDENCE.tar.gz.partial`，部分文件SHA `870b25513bf7ae076bf3bdf17d925dea9c273380232a223b639d4acf6b370c1b`。该partial不是完整备份；不能验证完整归档SHA/CRC或逐项本地大文件SHA，`verify_local_backup.py`未执行。

云端X/Pi/RC、矩阵、NetCDF、索引及完整归档均保留；本地轻量41项来源证据及清单已独立SHA/CRC核对。下一次只需单独的**文件传输窗口**：通过用户可信JupyterLab或已固定主机身份的SSH，取上列现成归档，验证大小314,868,916字节及既有SHA，再安全解包并对BACKUP_INDEX逐项核SHA。无需重新打包、构建、验收或优化。具体事实见LOCAL_SYNC_PENDING_FINAL.json及LOCAL_BACKUP_STATUS.json。本轮不自动继续传输。

GitHub及审阅ZIP只含本轮代码、Markdown、轻量JSON、原始Manifest与脱敏日志；大NetCDF/CSC/原始向量不发布。日志公开副本仅删除许可账户横幅，原始日志SHA和私有备份均保留；不含WLS秘密、私钥或令牌。审阅ZIP：`D:/ResearchWorkspaces/ASEAN/outputs/C02R_C03_DAILY_DIAGNOSTIC_REVIEW.zip`，完整Git提交和ZIP大小/SHA/CRC由同轮外置FINAL_DELIVERY_RECEIPT.json记录。

证据入口：[汇总](evidence/DAILY_RESULT_SUMMARY.json)、[真实原生返回](evidence/raw/vectors/RAW_RECEIPT.json)、[日V4](evidence/postprocess/POSTPROCESS_RECEIPT.json)、[KKT](evidence/postprocess/KKT.json)、[工程检查](evidence/postprocess/PHYSICAL_CHECKS.json)、[桥接](evidence/bridge/BRIDGE_RECEIPT.json)、[覆盖](evidence/artifacts/C02_CONSTRAINT_COVERAGE.json)、[原生日志公开副本](evidence/gurobi.redacted.log)、[封存](evidence/CLOUD_SEAL_COMPLETE.json)。`methods/summarize_receipts.py`只核SHA并汇总已有JSON，不重新验收或调用求解器。

**C02R：C02_BUILD_STATIC_ACCEPTED_NO_SOLVE；C03：OPTIMAL_BUT_NOT_ACCEPTED。** 不恢复G6-05，不进入2920 Gate6、Integrated/Disconnected/DEC或下一次优化。等待用户与ChatGPT审阅现有原始证据，再决定下一步。
