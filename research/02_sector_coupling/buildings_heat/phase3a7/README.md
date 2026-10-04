# Phase3A7 交付入口

先读 `BUILDINGS_PHASE3_CLOSEOUT.md`，再读 `RESEARCH_ELECTRICITY_BOUNDARY_FREEZE.md`。本轮4份报告、2张CSV对应用户要求的6项交付。研究电力概念已由人类冻结，数值输入未被接受或替换。

`BUILDINGS_FIRST_FULLSC_BOUNDARY.csv`是11国×R/S的22行表示建议，当前44个space/water用途均embedded；这不表示真实热量为零。`BUILDINGS_MATERIALITY_REGISTER.csv`为15项定性分流，明确哪些共享系统门槛仍待数值组装前完成，哪些细节不再阻断下一部门审计。

CSV为静态审阅表，不是输入文件或可执行config。`build_tables.py`只从既有JSON/报告建立表示建议和来源manifest；`export_tables.mjs`通过artifact-tool生成两表；`validate_delivery.py`核对范围和数据不被悄悄接受。没有新外部下载，没有能量转换计算或实验重跑。

方法：沿用academic-research-suite的证据核查方式与spreadsheets科学数据表规范。四种陈述分别标识：HUMAN_FROZEN_CONCEPT（人类决定）、REUSED_PROJECT_EVIDENCE（已保留证据）、PROPOSED_TRIAGE（本轮定性判断）、FUTURE_GATE（尚未执行的检查）。概念接受不得外溢为数值确认。

`evidence/INPUT_MANIFEST.json`记录所有依赖及用户本轮指令；原件依赖由交付包继承Phase3A6。新审计文件入Git；预览不入Git。交付包包含SHA清单、root/project两份审计提交记录。保持旧阶段结论及原件，不运行旧finalizer。
