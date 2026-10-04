# 工业需求空表反向追踪

**当前全空节点工业需求已定位到 GDP 空间输入及分配链；不是“UNSD 完全没有 ASEAN 工业数据”。本轮仅诊断，没有补数、重新生成模型输入或修改 workflow。**

## 已读取的因果链

```text
全球 GDP 原始 NetCDF（已有、覆盖 ASEAN）
  → load_GDP 复用同名已存在 TIFF（仅非洲范围）
  → ASEAN GADM gdp 全部 0
  → GDP 网格与聚类总量全部 0
  → industrial distribution key: gdp / sum(gdp) = 0/0 → NaN
  → 没有设施分布的工业类别回退到 gdp 权重
  → 每个节点的增长/分配行都含 NaN
  → 与国家工业总量 dot 时传播 NaN，包括 NaN × 0
  → 48×10 节点需求数据单元格全部为空
```

诊断证据：`INDUSTRY_DIAGNOSTIC.json`、`GDP_TIMOR_EVIDENCE.json`；关键 CSV 副本在 `diagnostic_inputs/`。纯映射函数通过 AST 从当前源码提取，只对既有表做缺失值诊断，未运行 Snakemake、网络生成或求解器。

## 从最终表到原始入口

| 环节 | 当前文件 / 函数 | 实读结果 |
|---|---|---|
| 最终工业需求 | demand/industrial_energy_demand_per_node_elec_s_50_{2030,2040,2050}.csv | 每年 480 个单元格全 NaN；含两个最终名为 low-temperature heat 的列 |
| 节点需求计算 | build_industry_demand.py:country_to_nodal；约第 375 行国家循环与 dot | construction 等无设施分布列统一用 GDP；每行都有缺失权重 |
| 分配键 | build_industrial_distribution_key.py:build_nodal_distribution_key | 三年各 48 个 gdp 权重全 NaN；并非所有设施型权重都空 |
| GDP 聚类表 | gdp_layout_elec_s_50_{year}.csv | 48 个 total 都为 0；fraction 的 fillna(0) 掩盖了除零信息，但后续使用 total |
| GDP 网格 | build_population_layouts.py；gdp_layout_{year}.nc | 146×175 共 25,550 个数全部 0 |
| GADM | shapes/gadm_shapes.geojson | 351 个行政区 gdp 全为 0，人口列另有有效值 |
| 实际读取栅格 | data/GDP/GDP_PPP_1990_2015_5arcmin_v2.tif | 289×289，范围约经度 −1.667～22.417、纬度 −2.667～21.417；没有 ASEAN 覆盖，CRS 元数据为空 |
| 已有全球原始源 | 同名 .nc，134,025,184 字节 | 4320×2160，1990–2015，2015 年 ASEAN 包围框存在 89,096 个有限非零单元格；单位 constant 2011 international US dollar |

原始 GDP 是 [Kummu 等数据对应的 Dryad 入口](https://datadryad.org/stash/dataset/doi:10.5061/dryad.dk1j0)，源码引用 DOI 10.1038/sdata.2018.4。本轮未重新下载它，也没有把包围框合计当 ASEAN 国家 GDP——包围框含境外区域。

`build_shapes.py:load_GDP`（约第 810 行）在 TIFF 已存在且 update=false 时直接复用，不比较来源 NC、年份或覆盖范围。`_sum_raster_over_mask` 使用 nodata=0；范围不相交可以产生全零。现有 `update_file=false` 与缓存范围及后续全零结果共同解释了失效链。**尚未找到该局部 TIFF 最初由哪次下载/复制产生的完整日志，因此“来自某个特定教程 ZIP”只是一种可能，不能写成已证实。**

## UNSD 原始数据与筛选

源码入口为 `data/demand/unsd/paths/Energy_Statistics_Database.xlsx` 中的下载路径，现有 `data/demand/unsd/data/` 包含 52 份 `UNdata_Export_20250502_*.txt`。`build_base_industry_totals.py` 拼接导出表，拆 Commodity/Transaction，做 ISO2 转换，过滤基年 2019 与 `data/unsd_transactions.csv` 指定交易，进行燃料分类与吨/GWh/TJ/体积到 TWh 再到 MWh 的转换。

已保存该下载登记工作簿及 `UNSD_REGISTRY_EVIDENCE.json`：75行中52条非空链接，指向 `data.un.org/Handlers/DownloadHandler.ashx` 的 EDATA 导出。`build_base_energy_totals.py` 仅在 update_data=true 时更新；下载异常分支使用固定 Google Drive 存档 `1VUV0X-tTQECi2pHdE5EWXjPI2yeCdk6F`。当前配置 update_data=false，因此使用现有导出，不因链接今天是否有效而自动更新。本轮没有调用会清理旧导出文件的更新分支，也没有据脚本的异常回退设计推断历史下载曾失败。

现有国家工业表中，ASEAN 10 国有 44 个 country-carrier 行、572 个有限数，157 个非零数。10 国工业电力总量均为非零。**这排除了“整个 UNSD 下载失败导致所有国家没有工业需求”作为当前全空表的解释。** 国家表并未缺失成空，空值在下游空间分配中扩散。

Timor-Leste 是独立问题：现有 UNSD 文件包含其 2019 年 **79 条**记录，因而不是国名转换完全失败或该国完全未下载；记录涉及住户、商业公共服务、other、供需和运输等，但本轮未发现匹配所需工业分项的记录。经过当前工业交易筛选后，国家工业表没有 TL。原始相关行已保存为 `diagnostic_inputs/timor_UNSD_2019_rows.csv`，不能把未分类 other 自动转为工业或填成真实零。

## 版本与作者结果的交叉检查

工业代码来自 Earth-Sec 合并链，2024 年已进入 Earth；之后有国家需求处理、2026 年显式 ammonia 与稳健性改动。当前 GDP 缓存复用逻辑在历史中长期存在；没有证据证明本次全空由某个最新工业算法提交单独造成。

两份作者论文网络的工业电力 Load 分别约 721.065 TWh（baseline 2025）、1586.857 TWh（DEC 2050），均非零。它们包含 final_adjustment 的需求重分配，因此只能证明作者最终电力案例不是当前空工业状态，不能反向认证所有原始非电工业需求。

`country_to_nodal` 回退 GDP 使用的是全区域归一化权重，是否保持每国工业总量还需单独核对；`other_industries=false` 分支中的 drop 未赋回也需独立评审。即使换成有覆盖的 GDP 输入，也不能未经守恒检查就宣布 full-SC 工业层有效。本轮未修改这些逻辑。

## 归因与后续最小需求

| 候选解释 | 本轮判定 |
|---|---|
| UNSD 全部下载失败 / 原始文件路径不存在 | 不支持；文件与 10 国非零国家表已存在 |
| GDP 空间缓存不适用 | 已证实范围不匹配；与源码及全零中间量一致 |
| 仅最新工业版本漂移 | 未证实；不能以时间先后替代因果证据 |
| 筛选问题 | TL 工业分项缺口独立存在；不是所有国家全空的主因 |
| 作者未提供任何 ASEAN 工业数据 | 不支持；当前国家表与作者最终工业电力均非零 |

不再要求用户“重新提供全部 ASEAN 工业数据”或“重新下载全球 GDP”。已有原始 GDP 可用于另一个经授权的工程修复与守恒验证任务。真正剩余的是 TL 工业分项/可说明的缺失处理、ASEAN 工业增长率（当前回退 DEFAULT）、设施覆盖与工艺/热值口径确认。这些未经共同确认不能成为正式实验输入。
