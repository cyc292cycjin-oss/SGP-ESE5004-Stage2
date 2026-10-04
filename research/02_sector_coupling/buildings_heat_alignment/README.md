# Phase 3A-2 — Buildings + Heat Baseline Alignment

**Read → trace → validate → report 已完成；DATA ACCEPTED 未达到。** 从[readiness与A–K回答](BUILDINGS_BASELINE_READINESS.md)开始阅读。

## 八项交付

1. [BUILDINGS_HEAT_BASELINE_MAP.md](BUILDINGS_HEAT_BASELINE_MAP.md)
2. [BUILDINGS_DEMAND_ACCOUNTING.csv](BUILDINGS_DEMAND_ACCOUNTING.csv) — 99行、45列；含国家与R/S、fuel A–F、2019和教程2030/40/50；空值不等于0
3. [BUILDINGS_SOURCE_FAMILY_REVIEW.md](BUILDINGS_SOURCE_FAMILY_REVIEW.md)
4. [BUILDINGS_ASEAN_DATA_CANDIDATES.md](BUILDINGS_ASEAN_DATA_CANDIDATES.md)
5. [HEAT_PROFILE_VALIDATION.md](HEAT_PROFILE_VALIDATION.md)
6. [BUILDINGS_ENGINEERING_FIX_PLAN.md](BUILDINGS_ENGINEERING_FIX_PLAN.md)
7. [BUILDINGS_DATA_REGISTRY.csv](BUILDINGS_DATA_REGISTRY.csv) — 42项身份/用途/版本/哈希记录，全部UNVERIFIED/PENDING
8. [BUILDINGS_BASELINE_READINESS.md](BUILDINGS_BASELINE_READINESS.md)

## 数据和代码位置

本目录是研究审计层，不是upstream工作流的`data/`。`data/raw/buildings`保存候选资料及下载manifest；`processed`保存原始行的明确子集和模型转换；`derived`保存CSV生成记录和检查。候选文件从未复制到正式模型输入路径。既有原始数据继续由上轮hash清单引用，不搬动历史资产。

原始大文件PDF/HTML不进Git；Git保留URL/hash/版本/获取脚本，交付ZIP附这些已下载缓存。用户与导师可以用manifest逐一校验。统计数据引用其原机构，完整报告的使用仍按原机构条件。天气/人口本轮只登记来源族，没有假造未冻结研究输入的hash。

`patches/E1,E2,E4.patch`是独立待审工程候选；实际各branch与commit见`evidence/CANDIDATE_COMMITS.json`。没有合并R或push远端。共享审计目录也将提交到项目仓库的独立研究分支；最终交付receipt单独记录，避免文档引用自身commit导致循环。

## 复核方法

- `extract_accounting.py`：用已有PyPSA环境只读原始UNSD、上一轮JSON、T中间结果，生成审计JSON；不运行Snakemake或solver。
- `retrieve_candidates.py`：仅访问枚举URL，已有cache不覆盖；新远端版本须另立记录。`inspect_candidate_pdfs.py`用bundled Python定位关键页、输出render receipt。
- `build_registry.py` + `export_tables.mjs`：核对冻结快照hash，使用Artifact Tool生成两张CSV。CSV为审计呈现，不是模型配置。
- `check_candidate_fixes.py --repo <candidate> --fix E1|E2|E4 --output <audit.json>`：合成守恒测试；`check_residual_account.py`展示尚未修复的E3。
- `build_candidate_patches.py`在独立worktree创建候选，`finalize_candidate_tests.py`整理独立测试路径和本地提交；这是首次构建记录，已有worktree不应reset后重跑。日常验证使用上条检查命令即可。

所有原始输入 `UNVERIFIED`；所有human acceptance `PENDING`。源码核实/哈希通过与科学接受是两件事。没有运行正式实验，没有新增模块，没有自动进入其他部门。
