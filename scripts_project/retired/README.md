# 退役模块（S1-2，2026-10-15）

本目录保存按研究层清单第 9 节（`work/p1_module_spec_20261015/RESEARCH_LAYER_INVENTORY.md`）
判定为 RETIRE、并在 S1 实际移出 `scripts_project/` 的模块。文件内容未改动，仅移动；
Git 历史保留原路径。任何 `import` 这些模块的历史执行脚本（gate5/gate6 运行器）在新口径下
不再是入口，S4（完整求解与 V5 验收）时统一处理。

| 模块 | 原用途 | 新口径下的替代 |
|---|---|---|
| fixed_accounts.py | 807 个固定生物质账户与 1,256 条终端计量 Link 的结构/导出校验与会计报告 | 固定账户不再存在；需求在 S2（R8）接回为内生部门需求；V5 B 组门槛 B11 检查技术/路径完整性 |
| fixed_account_scope.py | 动物粪便等附加固定账户的人工授权范围 | 同上 |
| fixed_inventory_scaling.py | 固定资源库存缩放 | 同上 |
| audit_fixed_price_residual.py | 固定账户价格残差审计 | 同上 |
| diagnose_gate5_fixed_blocks.py | Gate5 固定块诊断 | C08 已证明该块可解耦；块不再存在 |
| verify_local_fixed_diagnosis.py | 固定块本地诊断核对 | 同上 |
| gate6_fixed_term_contract.py | 固定项不变量合同 | 同上 |
| check_research_carriers.py | Phase3 隔离契约（跨境开关必须为 false、情景不得有差异） | `research.cross_border.*` 配置开关 + V5 B5/B12（`scripts_project/v5/v5_gates.py`） |
