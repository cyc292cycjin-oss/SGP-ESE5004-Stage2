# A0.5 论文—源码—配置—结果来源链

审计日期：2026-09-30。研究层独立保存；当前项目模型为 `ce327bfae2abe5526d4c1976173f0f8d08366ba5`。本文件的“已恢复”表示来源证据已找到，不表示输入已由人确认，也不表示独立复现完成。

## 结论

**已从两份作者结果的内嵌 metadata 找到运行 SHA `5bacad702ccfed17ad19ab510fa710651e966f2c`，并成功取得该 SHA 的官方源码。** 这比依据发布日期选择 main/tag 更直接。两份样本分别是 baseline-aims-3H 的 2025 年和 decarbonize-aims-3H 的 2050 年；不能把样本结论自动推广为另外 42 份网络的逐文件认证。

证据链为：

```text
Andreyana et al. (2026), DOI 10.1088/1755-1315/1654/1/012020
  → 官方仓库 PR #25 的论文情景/文档与作者结果下载链接
  → results-asean-paper-v1.zip 的两个 NetCDF 样本
  → meta.git_commit = 5bacad702ccfed17ad19ab510fa710651e966f2c
  → 该 SHA 的配置、碳函数、最终 ASEAN 调整、AEO8 表与工作流
  → 内嵌有效配置 / v0.13.2 / PyPSA 0.30.3 / 保存的网络约束与输出 SHA256
```

论文文本见上一轮 `../00_model_audit/PAPER_EVIDENCE.json`。论文案例明确以电力系统为研究对象，完整部门耦合属于后续能力；作者仓库/文档名称中的 sector-coupled 不能改变论文的实际范围。

## 关键历史身份

| 身份 | SHA / 时间 | 证据及限制 |
|---|---|---|
| 作者结果内嵌运行版本 | `5bacad702ccfed17ad19ab510fa710651e966f2c`，2025-12-23 | 两个网络的 metadata 一致；官方 commit API 可访问。不是用户教程 SHA |
| 论文情景最终发布 | `99159edb7298b847fea517bf05c3f388493501c9`，2026-01-21 | PR #25，标题为 Finalized Scenarios from Conference Paper；属于发布/整理节点，晚于样本运行 |
| PR #25 中间版本 | `3f4dbe6c…` → `5bacad70…` → `8bb2d20e…` → `89b264cf…` | API 返回四个提交；解释为何运行 SHA 不在本地 main 的可达提交中，却仍可从 GitHub 精确读取 |
| 当前官方 main | `a3616a68ee44592af6527ca9024a90f1956646ae` | 2026-09-30 官方 branches API 与本地历史一致 |
| 用户教程归档 | `ce327bfae2abe5526d4c1976173f0f8d08366ba5` | 教程与工程修复归档，不能代替作者运行版本 |

官方 tags API 返回 v0.0.1–v0.6.0 共 12 项，releases API 返回空列表。本次检索没有找到明确绑定这篇论文的专用 release/tag/Zenodo 代码存档；这不是“所有可能存档均不存在”的证明。现在已有更强的运行 metadata SHA，因此不再要求用户先寻找某个猜测的论文 tag。

官方入口：[PR #25](https://github.com/pypsa-meets-earth/pypsa-asean/pull/25)、[运行 commit](https://github.com/pypsa-meets-earth/pypsa-asean/commit/5bacad702ccfed17ad19ab510fa710651e966f2c)、[论文整理 commit](https://github.com/pypsa-meets-earth/pypsa-asean/commit/99159edb7298b847fea517bf05c3f388493501c9)。原始 API 响应保存在 `official/`，读取与哈希记录见 `FETCH_LOG.json`、`HISTORY_FETCH_LOG.json`。

## 两个样本中实际保存的配置

| 项目 | 读取结果 |
|---|---|
| 模型与时间 | myopic；2025–2050，每五年；2013 全年，3h；2920 snapshots，三种权重均为 8760 |
| 空间 | 11 国；wildcard clusters=100；不能据此假定每类 Bus 恰好 100 个 |
| 模型范围 | sector enable 多项 true，但 `final_adjustment.only_elec_network=true` |
| 互联 | baseline/decarbonize 的 AIMS 情景；ll=v2.0，非逐线简单乘二 |
| 需求 | demand=DEC、base_year=2019；final_adjustment 有 AEO8 总电量和国家工业份额 |
| 成本 | technology_data_version=v0.13.2，append_cost_data=true，regional_factor=false |
| 碳 | baseline enable=false；decarbonize enable=true，旧键 co2_budget.co2base_value=1e9 |
| 软件/求解器线索 | 网络写出版本 PyPSA 0.30.3；配置写 Gurobi，包含选项和随机种子。不是完整环境锁或 solver 运行日志 |

完整配置分别保存在 `effective_config/baseline-aims-3H_2025.json` 和 `effective_config/decarbonize-aims-3H_2050.json`。它们是作者结果中的配置证据，不是本项目的新实验配置。源码副本在 `official/author_run/`。

## 输入版本闭合程度

- 技术成本 v0.13.2 已进一步绑定到 `ec22a1843632fd28ecb9a139ee5156faf23324a3`；当前教程 pre_costs 的 2030/2040/2050 三份 CSV 与该版本官方输出逐字节一致。
- 作者运行 SHA 下的 AEO8 D15/D17/D18 表已取回，与当前实际输入副本的比较见 `RECOVERY_SUMMARY.json`。Git 工作区换行可能改变文件哈希，因此比较对象使用上一轮从 WSL 复制的原始字节，而非 Windows checkout。
- metadata 指向 OSM+prebuilt 0.1.1、UNSD 2019 基年、ERA5/2013 等。但结果包没有输入文件或全量 input hash manifest；不能据“版本标签相同”认定所有外部输入逐字节相同。
- 内嵌 `git_commit` 没有同时附带 dirty 状态、未提交差异和每条 rule 的源码哈希。它确定了作者记录的运行版本，尚不能证明运行时工作区完全等于 clean SHA。

**已关闭：论文运行版本完全未知、作者有效配置完全未知、作者结果无法定位。仍未关闭：全量原始输入冻结及运行环境/工作区完整认证。** 后者是严格 paper reproduction 的残余要求；它不应被误写为“当前还需要用户替我们重新寻找论文源码”。

本轮只读取作者输出，没有复算 objective、运行优化器或核验论文全部表格。详细输出覆盖范围见 [RESULTS_PACKAGE_AUDIT.md](RESULTS_PACKAGE_AUDIT.md)。
