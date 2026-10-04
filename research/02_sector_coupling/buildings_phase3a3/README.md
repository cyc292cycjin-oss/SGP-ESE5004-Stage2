# Phase 3A-3 — Buildings + Heat engineering and data recovery

**E1/E2/E4 独立与组合回归通过；DATA ACCEPTED 尚未达到。** 请先阅读[readiness与A–K回答](BUILDINGS_PHASE3A3_READINESS.md)。本目录为研究层，不是上游工作流或正式模型输入。

## 九项交付

1. [BUILDINGS_FIX_E1_REPORT.md](BUILDINGS_FIX_E1_REPORT.md)
2. [BUILDINGS_FIX_E2_REPORT.md](BUILDINGS_FIX_E2_REPORT.md)
3. [BUILDINGS_FIX_E4_REPORT.md](BUILDINGS_FIX_E4_REPORT.md)
4. [BUILDINGS_FIX_TEST_MATRIX.csv](BUILDINGS_FIX_TEST_MATRIX.csv) — 1,062 项逐国/行为检查，含 before/after/expected/误差/状态
5. [ASEAN_BUILDINGS_THERMAL_DATA_SEARCH.md](ASEAN_BUILDINGS_THERMAL_DATA_SEARCH.md)
6. [ASEAN_BUILDINGS_DATA_CANDIDATES.csv](ASEAN_BUILDINGS_DATA_CANDIDATES.csv) — 8 项新候选；6 项原文件缓存、2 项仅恢复元数据
7. [BUILDINGS_DEMAND_ACCOUNTING_AFTER_FIX.md](BUILDINGS_DEMAND_ACCOUNTING_AFTER_FIX.md)
8. [BUILDINGS_DATA_REGISTRY_UPDATED.csv](BUILDINGS_DATA_REGISTRY_UPDATED.csv) — 旧42+新8=50项；UNVERIFIED/PENDING
9. [BUILDINGS_PHASE3A3_READINESS.md](BUILDINGS_PHASE3A3_READINESS.md)

## 可复核性

- [测试汇总](evidence/TEST_SUMMARY.json)、[运行环境/指令](evidence/RUN_RECEIPT.json)、[独立分支](evidence/FIX_COMMITS.json)；每个源码修复与验证提交分离，patches 可逐项审阅。
- `test_buildings_fixes.py --repo <pinned checkout> --fix E1|E2|E4 --output <new JSON>` 是 solver-free 合成验证，需要已有 PyPSA 环境。U 预期失败，对应候选预期通过。不要对完整正式模型调用 optimizer。
- `build_evidence.py` 从已保存结果和来源清单重建 JSON；`export_tables.mjs` 用 Artifact Tool 输出 CSV。不需要重跑测试才能查看交付表。CSV 是机器可读审计表，没有隐藏公式或把缺值变成零。
- `retrieve_sources.py` 只访问枚举 URL，缓存不覆盖；远端版本改变必须另立身份。原文件/hash/许可限制见[data说明](data/README.md)。
- `record_fix_validation.py` 和 `compose_and_validate.py` 是本轮一次性构建记录，已有分支/目录不应重置后重跑；日常验证只用上述指定检查命令。

P=`5bacad702ccfed17ad19ab510fa710651e966f2c`；U/R=`a3616a68ee44592af6527ca9024a90f1956646ae`；T=`ce327bfae2abe5526d4c1976173f0f8d08366ba5`。P、U、R、T 的身份不因候选补丁混同。

交付包是来源/工程审查材料，不是自带全部模型数据与环境的正式复现镜像。首次读取 ZIP/README 不授权执行其构建命令。没有大模型求解、自动合并、数据采用或进入下一部门。

实测测试环境为 Python3.11.13、PyPSA0.30.3、NumPy1.26.4、pandas2.3.1。日志保留既有 PROJ 路径告警；本轮未调用地理变换，不能用这些守恒测试把完整环境 readiness 升级为 PASS。各分支环境标签更正的文档提交也保留在 Git 中。
