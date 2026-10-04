# 论文基准构建状态

**PARTIAL / BLOCKED_INPUT_IDENTITY：能够加载论文源码并展开部分DAG；没有完成最小正式案例的重建或求解。** 不能报告“Paper SHA已跑通”。

| 身份 | 恢复结果 |
|---|---|
| 实际运行SHA | `5bacad702ccfed17ad19ab510fa710651e966f2c`，两份作者NC metadata一致 |
| 最小目标 | baseline-aims-3H，2025，100 clusters，AIMS，lv2.0，myopic首期 |
| 时间 | 2013全年，3h，2920 snapshots；三种权重和均8760h |
| 技术成本 | v0.13.2 + 作者AEO8 append；作者逐文件input hash未给出 |
| 碳 | Baseline无显式CO2Limit；保留DEC对应六年轨迹作为另一组 |
| 作者环境 | PyPSA0.30.3，Gurobi；作者SHA含environment.yaml及linux-64.lock.yaml |
| 本机 | PyPSA0.30.3 / Python3.11 / snakemake7.32.4 / linopy0.5.5；完整pip freeze已保存 |
| 求解器 | gurobipy12.0.3可初始化，但受限license提示存在；大模型资格未验证 |

作者实际配置是 [PAPER_EFFECTIVE_CONFIG.yaml](evidence/PAPER_EFFECTIVE_CONFIG.yaml)，从作者NC metadata恢复，年份字典键恢复为整数，未缩小到教程分辨率。**其中使用`cutout-2013-era5`，不是当前ASEAN配置中的`asean-2013-era5`。** 不能只读论文SHA下config.asean模板就假定它等于作者有效配置。作者metadata的`retrieve_databundle=false`、`build_cutout=false`说明其运行假定已有输入。

## 已执行的构建检查

第一次dry-run缺EEZ/natura；本地已有这两个原始文件，因此仅以只读源链接供第二次dry-run使用并记录hash，未要求用户重新找它们。第二次停在：`cutouts/cutout-2013-era5.nc`、GEBCO2025、Copernicus LC100 2019等原始输入。日志为 [第一次](evidence/PAPER_DRYRUN.log)、[第二次](evidence/PAPER_DRYRUN_WITH_LOCAL_GEODATA.log)，命令、时间、返回码及输入哈希在 [PAPER_PREFLIGHT.json](PAPER_PREFLIGHT.json) 和 [PAPER_PREFLIGHT_FOLLOWUP.json](PAPER_PREFLIGHT_FOLLOWUP.json)。PROJ路径通过显式环境变量修正于第二次预检；不改论文代码。

沿论文bundle配置找到官方亚洲气象包。HTTP Range实测可访问，ZIP为27,611,570,291B，包含`cutout-2013-era5.nc`（27,693,617,591B，目录CRC32=8bc17e50）。文件名与作者metadata匹配。这里只读取目录及元数据；未下载完整NC、未验证其CRC/全文件SHA/时空坐标。目录时间2023-08-09不是发行版本保证。见 [WEATHER_ARCHIVE_DIRECTORY.json](WEATHER_ARCHIVE_DIRECTORY.json)。**因此“公开下载入口”缺口已关闭；“与作者当年输入逐字节同一”仍未关闭。** 用户不必先重新寻找所有源数据。

## 参考输出与差异

作者baseline-AIMS2025 objective=51,958,123,545.77296；objective_constant=8,754,735,116.417757；作者DEC-AIMS2050 objective=94,026,128,588.01077，CO2Limit=100,000,000t。两份作者网络哈希继承A0.5证据，登记为AUTHOR_OUTPUT_NOT_REPRODUCTION。

本轮正式输出、objective差值、constraint residual、solver status均为**N/A（未正式求解）**，绝不用0表示未测量，也未将作者已解网络重优化当成原始数据重建。没有重新运行全部44个网络。

最低下一步：确认官方候选输入家族的使用/与原作者不一致时的标注；取回并检查完整气象及缺失底图；核对author input manifest（若作者无法提供，则只能标“来源可重建参考”，不能声称字节级复现）；确认可用的正式求解器/环境容量后，才能按manifest工具启动该2025单案例。
