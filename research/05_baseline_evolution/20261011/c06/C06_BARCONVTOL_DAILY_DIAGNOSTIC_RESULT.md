# C06 BarConvTol 日诊断最终交付

**C06_EXECUTION_ACCEPTED_SCIENCE_NOT_ACCEPTED。** C06原生求解完成，日V4未通过；云端已封存，本地完整归档仍为 **LOCAL_SYNC_PENDING**。本轮仅整理已有证据，没有新的优化、模型构建或远端操作。

## 真实运行与对照身份

Run：`c06_barconvtol_daily122_20261012T095705Z_321aa0f1`。生产提交`34a34b69ef752d7809487ca609cd91e12f75bffd`。GRBoptimize返回码0，优化调用1次；Status=2 OPTIMAL、SolCount=1、Barrier143次、Runtime282.17975401878357秒。NATIVE_CALL_EXIT、NATIVE_RETURN、RAW_RECEIPT、原生日志及POSTPROCESS均对应同一run和模型Manifest；未把OPTIMAL作为科学PASS。

| 项目 | C03 | C05 | C06 |
|---|---|---|---|
| SolCount | 1 | 0 | 1 |
| BarIterCount | 69 | 24 | 143 |
| Runtime | 155.37094283103943 | 81.59514498710632 | 282.17975401878357 |
| ConstrVio | 6.891766654441827e-05 | -1.0 | 4.999788120237309e-06 |
| DualVio | 0.02547632459915626 | {'status': 'NOT_AVAILABLE', 'error': 'GRBgetdblattr: native error 10005'} | 9.541758329495052e-07 |
| ComplVio | 803.4719448953265 | {'status': 'NOT_AVAILABLE', 'error': 'GRBgetdblattr: native error 10005'} | 1.0581741502357782 |
| Status | 2 | 12 NUMERIC | 2 |

C03为主对照，C05为Aggregate=0的NUMERIC分支。154项实际数值参数重新逐项比较：C06相对C03仅BarConvTol从1e-6到1e-9；相对C05有Aggregate 0→1和BarConvTol变化。Aggregate=1，Crossover=0，NumericFocus=0，FeasibilityTol/OptimalityTol=1e-6；TimeLimit3600、SoftMemLimit65十进制GB、MemLimit1e100。完整差异表见`C06_C03_C05_PARAMETER_COMPARISON.json`和主比较JSON。

三次同一日数学模型：2,450,005列、6,042,238行、11,403,496非零元。冻结日CSC、边界、D/R、标签、目标、Scheme A、C01R和日V4绑定均复用。模型Manifest SHA `f70b2dc2dfc79e5b7caadc22beb30b82520a91b1aabf3dd720962af120302a70`；日cost SHA `c9a9717c664e2b3d5d4ca9b56848097f5231823465516113a13e00cb8f632d83`；日V4 SHA `8c48d0735e6dcde870fdff589915aba57b55870994e75bc04b76d39e41c38459`，父V4 `955cfe48f0de95d1ce9df531ee7d5b0a3dff47dad9f6b06f70a180745cf0657f`。

C06生产核验17,369项输入SHA，EXACT_READBACK_PASS用时3.736114秒，原生模型句柄在交接与唯一调用中一致；本轮又核对9项核心文件SHA。没有重建、CSR→CSC转换、P2或warm start。最终C06 BACKUP_INDEX文件尚未收到，因此完整封存引用列表的本地独立核验仍待办，不能用这9项检查替代。

## 保护、RAW与完整日V4

生产t0为2026-10-12T09:57:05.802316Z，固定总截止2026-10-12T11:57:05.802316Z；全流程至封存guard退出406.461504秒。监督回执无保护触发、无OOM。进程树RSS采样峰值4.078358GiB；cgroup共享/生命周期峰值6.249012→6.850983GiB；最小余量83.332123GiB，磁盘最小26.656818GiB。RSS并非连续峰值，cgroup峰值并非库独占峰值。末次10:05:32Z观察确认worker/supervisor/guard均退出；本轮未重新连接实例，未操作电源。

RAW先持久化X/Pi/RC，分别2,450,005 / 6,042,238 / 2,450,005个float64，再验收。三个原生SHA及原单位SHA见`evidence/C06_ANALYSIS_PROVENANCE.json`。本地从已接收完整成员恢复原单位向量，独立逆映射所得NPY三个SHA均与云端RAW回执相同；这证明分析使用同一返回点，不是修补解，也不是完整归档传输完成。

| 日V4门槛 | C03 | C06 |
|---|---|---|
| native_optimal | PASS | PASS |
| complete_primal_dual | PASS | PASS |
| full_matrix_and_column_bounds | FAIL | FAIL |
| independent_KKT | FAIL | FAIL |
| physical_dynamics | FAIL | FAIL |
| 807_inventory | FAIL | FAIL |
| 385_obligations | FAIL | PASS |
| FOM_once | PASS | PASS |
| NetCDF_exact_readback | PASS | PASS |
| daily_binding | PASS | PASS |

日模型仍有243条Store库存下界矩阵行、85个资源账户、3336个stationarity列失败。385组义务全部通过；没有将输入表示预算从求解残差扣除。NetCDF逐值回读和FOM一次计量通过，不代替物理/KKT门槛。

原科学已知成本427765321342.063842773 EUR；V3复算428014090855.334899902 EUR；微扰贡献248769513.271067888 EUR；组分复算误差-1.0758638382e-05 EUR。ObjCon=-12788967.997821666 EUR。独立V3复算减原生ObjVal=0.0405883789062 EUR。均为未合格候选的核算值；NULL未填造，FullSystemCostComplete=false，原未扰动目标最优性NOT_PROVEN。

## 封存、传输与明确缺口

云端封存回执：53项新文件、457,423,943字节，BACKUP_INDEX SHA `47114a605d104fdbbfdb03ea5442d8e3fd2e68ad5c5882aeb5475618490e97c9`。归档153,715,959字节，SHA `fcfb61920d094aec9cf84b755a25d5b589097d4842656fbc863b5e901cb56c07`。

原60分钟传输窗已结束，连接错误为`Connection reset`。两段现有接收数据共140,640,256字节，仍缺13,075,703字节。保留全部partial、旧窗口和失败回执；本轮没有重开窗口或续传。完整gzip CRC、全归档SHA和53项BACKUP_INDEX逐文件验证 **尚未完成**。云端原件及消费标记不变。

本地分析目录：`D:\ResearchWorkspaces\ASEAN\work\c06_barconvtol_20261012\analysis_view`；原partial恢复目录：同目录下`recovered_partial_evidence`。云端Run：`/root/autodl-tmp/SGP/runs/c06_barconvtol_daily122_20261012T095705Z_321aa0f1`。完整归档位置及最小补齐方案见`C06_FINAL_BACKUP_STATUS.json`。只有获得新的明确传输授权后才能补齐；无需也不得重新求解。

## 交付与停止

比较结论见`C03_C05_C06_COMPARATIVE_FORENSICS.md`；全部计量见同名前缀JSON。当前仍为C阶段365日日诊断，未进入D阶段2920时段Gate6。G6-05持续PAUSED_BY_USER；不启动下一实验。此次结果分支`codex/c06-barconvtol-daily-20261012`，关联PR #13/#14/#15，实际提交和PR见ZIP的GIT_PUBLICATION。实例最后已知保持运行及计费，本轮不声称进行了新的在线状态核验。
