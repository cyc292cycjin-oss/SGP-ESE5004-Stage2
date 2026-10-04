# A0.5 — Source Provenance Recovery 交付状态

2026-09-30。研究主题：ASEAN renewable energy transition under sector coupling。本轮完成 source/history/package tracing → report；未修数据、未改配置/政策、未启动正式 integrated/standalone 求解。作者结果读取不计独立复现。

## 主要结论

1. **论文运行版本已恢复到输出证据。** 两个作者网络记录同一 SHA `5bacad702ccfed17ad19ab510fa710651e966f2c`；官方源码和有效配置均已保存。论文整理发布节点 `99159edb…` 与运行节点要区分。
2. **作者包可访问。** 完整目录44份网络；抽查2份，保存 SHA256、内嵌配置、组件与约束。没有宣称读完其余42份或计算整包hash。
3. **工业空表已定位。** 原始UNSD国家表有10国非零工业量；当前GDP TIFF不覆盖ASEAN，导致GDP全零、分配权重NaN并污染节点工业需求。已有全球GDP原始NC可用，未重新生成输入。
4. **论文碳路径有代码与输出双重证据。** 旧 co2_budget.co2base_value=1e9、年度 factors 1→0.1；2050 DEC 网络保存100Mt上限。2026年迁移遗留的混合键与论文运行实现不同。
5. **DEA旧来源已恢复。** v0.13.2→`ec22a184…`，sheet86工作簿与原始单元格可查；三份当前pre_costs与官方输出字节一致。电解投资来自manual override，不能统称DEA数据。

## 八项交付

- [PAPER_CODE_PROVENANCE.md](PAPER_CODE_PROVENANCE.md)
- [SECTOR_COUPLING_PROVENANCE.md](SECTOR_COUPLING_PROVENANCE.md)
- [INDUSTRIAL_DEMAND_TRACE.md](INDUSTRIAL_DEMAND_TRACE.md)
- [CARBON_VERSION_TRACE.md](CARBON_VERSION_TRACE.md)
- [DEA_COST_SOURCE_TRACE.md](DEA_COST_SOURCE_TRACE.md)
- [RESULTS_PACKAGE_AUDIT.md](RESULTS_PACKAGE_AUDIT.md)
- [USER_INPUT_NEEDED_V2.md](USER_INPUT_NEEDED_V2.md)
- 本文件 SOURCE_PROVENANCE_STATUS.md

## 状态分层

| 项目 | 来源恢复状态 | 数据/实验接受状态 |
|---|---|---|
| 作者SHA、两个样本有效配置 | RECOVERED：直接输出读取 + 官方源码 | 不是 clean-worktree / 全量复现认证 |
| 完整 ZIP 目录 | RECOVERED | 两成员内容已审计，其余内容未审计 |
| SC继承关系 | RECOVERED：Earth-Sec→Earth→ASEAN | ASEAN full-SC 需求与边界尚未验证 |
| 工业空表主故障链 | LOCALIZED：输入范围与中间量直接读取，NaN传播推导 | 未修复；国家总量/分配仍需验收 |
| 论文碳路径 / 迁移疑点 | RECOVERED / LOCALIZED | 不替用户选择baseline或DEC、full-SC覆盖范围 |
| DEA86 / v0.13.2 | RECOVERED，主要转换已追踪 | 人工确认仍PENDING；私有来源及部分量纲未闭合 |
| 正式 integrated/standalone | NOT RUN | NOT READY TO EXECUTE |

RECOVERED/LOCALIZED 是来源审计标签，不是旧数据台账中的 CONFIRMED。本轮没有更改 `../00_model_audit/DATA_LEDGER.csv` 的确认状态。

## 证据、推导与未证实事项

**直接读取：** 官方 API/固定SHA源文件；Git日志与diff；作者ZIP目录、两个NetCDF metadata和静态/时变Load；当前国家工业表、GDP原始NC/缓存TIFF/中间量；冻结DEA单元格；成本CSV字节比较。

**分析推导：** 零GDP归一化和NaN矩阵乘积解释全空工业需求；新旧碳键错配会改变有效基数；full-SC互联会经转换/储能改变最优配置。只有前两者有当前具体输入支撑，最后一项是待实验检验的结构推论。

**尚未证实：** 当前非洲GDP TIFF最初来自哪次下载/复制；作者完整输入逐字节身份和工作区无未提交差异；其余42份网络是否全部使用同一SHA；每项完整非电需求的ASEAN适用性；私有电解投资依据。报告未用猜测填补这些空白。

## 对六个最终问题的回答

**1. GitHub源码/历史关闭了哪些缺口？** 关闭基本论文代码版本与配置未知、作者输出不可定位、SC来源不清、碳旧实现未知、DEA86无法找到与成本覆盖顺序不清；把工业“缺全部数据”缩小为明确GDP缓存故障链和TL等独立缺项。

**2. 哪些仍可能需要用户补原始资料？** TL工业分项；已有的ASEAN工业增长情景原表；若可取得的电解投资私有通信说明。严格论文复现时才进一步索取作者全输入/环境/dirty档案。不是要求用户重新寻找已恢复的旧DEA/论文代码/结果包。

**3. 哪些属于边界决定？** full-SC部门与工程版本；baseline或DEC及碳覆盖部门；standalone关闭的跨境载能；外部商品供给；区域资源/预算分解。它们不会由下载更多数据自动决定。

**4. 能否冻结 full-SC model boundary？** **不能正式冻结。** 框架血缘清楚，但需求有效性、版本选择及部门/资源/碳边界未共同确认。

**5. 能否进入 integrated vs standalone 实验设计？** **可以进入带待决项的概念与可比性设计讨论；还不能冻结可执行方案，更不能正式求解。** 这不是以等待为由停止源码工作：本轮可恢复证据已主动取得。

**6. 最少缺哪几组关键证据？**

1. 明确版本SHA和full-SC部门/技术/服务需求边界的共同决定记录。
2. 有效工业及其他非电需求、TL/DEFAULT处理、国家—节点守恒与GDP正确派生的验证记录。
3. 选定baseline/DEC后，旧新碳配置等价性及full-SC排放统计范围的验证记录。
4. integrated/standalone共享资源、外部商品、跨境载能与国内网络保持可比的边界表和约束检查。
5. 所选关键技术成本/燃料参数的来源与单位验收，包括private communications和储氢MW/MWh问题；其余仍保持PENDING。

## 复核与保留痕迹

`RECOVERY_SUMMARY.json` 是简明机器可读索引；`RESULTS_NETWORK_EVIDENCE.json`、`INDUSTRY_DIAGNOSTIC.json`、`GDP_TIMOR_EVIDENCE.json`、`DEA_WORKBOOK_EVIDENCE.json` 保存细节。`official/` 为读取的公开原件，`historical/` 和 `current_source/` 为源码快照，`history/` 为Git输出，`effective_config/` 为作者网络内嵌配置。均不是模型运行目录。

提取脚本有固定输入路径/名单，不调用优化器。外部来源首先锁定SHA或下载身份，HTTP失败也记录在fetch日志；两个错误AEO8候选文件名的404已在验证正确文件名后解决，不据此声称作者缺表。哈希和文档校验见 `VALIDATION.json`、`FILE_HASHES.json`。

原模型与上一轮A1–A4文件保持原样；新增审计单独提交。大网络缓存留在本地并忽略Git，以公开成员路径与hash重取；没有force-push或删除历史资产。原工作区既有 `outputs/`、`work/` 不代为清理。正式实验前仍须完成数据共同确认；本轮不会在未确认数据上启动正式实验。
