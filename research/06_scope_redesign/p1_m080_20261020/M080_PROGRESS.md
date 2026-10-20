# M08-0 进度文件（第 130 项：注册表补登与一致性修正；只改注册表，不改模型、不求解）

- 指令 `M080_CLAUDE_CODE_INSTRUCTION.md` SHA256 `7e72998d39f313a0d00699ea36a9c3bf4676e6cee807de4b161ad52f10a5144e`，与 `M080_INSTRUCTION_SHA256.txt` 一致（2026-10-20 核对）。
- 分支 `codex/m08-0-registry-backfill-20261020`，自 S4R 分支头 `cefab870` 开出；独立工作树 `/home/jin/wt_m080_20261020`（主检出在 S4O 分支，未动）。
- 起点注册表 `research_inputs/registry_v5/DATA_REGISTRY.csv` SHA256 `46e234d79ec4fbc824c5c4e416591525bec11b46dbdbceb4d4512f2f31922e50`（与 MEET-D 记录一致）。
- 边界：不求解、不连云、不调用 Gurobi；不改配置、构建 / 求解脚本、网络、既有结果。

## 子步骤

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| M0 | 核对 SHA、开分支 / 工作树、建进度文件 | 完成 | — |
| M1 | 补登缺口（§J 1–5） | 完成 | 见 M2 行（本行 SHA 记于下一次提交） |
| M2 | 海上风机型与尾流核实 | 未开始 | |
| M3 | 状态与等级修正（§I 3、5、6、7） | 未开始 | |
| M4 | 状态值检查与注册表单元测试 | 未开始 | |
| M5 | S4R 产出 v2（REGISTRY_ROWS_PROPOSED_v2、USER_DOWNLOAD_LIST） | 未开始 | |
| M6 | 重跑数据清单 v2 与精简版 | 未开始 | |
| M7 | 报告、台账、draft PR | 未开始 | |

## M0–M1 记录

- 复现性：现有片段 + 主检出中未入库的 `fragments/s4c_0.csv`（被 `.gitignore` 的 `*.csv` 忽略、从未提交）重拼得到的注册表 SHA256 = `46e234d7…2e50`，逐字节一致；M1 起把 `s4c_0.csv` 强制入库。`D1_EVIDENCE.json` 重生成时 6 个源文件的记录哈希由主检出的 CRLF 版本变为工作树的 LF 版本（内容相同）。
- 工作树另复制（不提交）`research_inputs/finance_v5/{COUNTRY_WACC_PUBLIC_SOURCES,DISCOUNT_RATE_IN_USE}.csv`，供 `test_s4c_0.py` 读取。
- 测试基线（工作树，27 个读注册表的测试文件，排除唯一的玩具网络求解用例 `test_s4c_3.py::test_net_zero_hook_forces_non_fossil_bunkers`）：91 passed / 24 skipped（缺既有构建，按设计跳过）。**另需说明**：开始时曾启动 `tests/research` 全量运行，约 25 s 后停止；按字母顺序 `test_s3b_r4.py`（可能还有 `test_s4c_3.py`）中的玩具网络 HiGHS 求解用例很可能已执行——不涉及研究网络、Gurobi 或云端。
- 提取：`scripts/m080_extract.py`（只读，12 s，峰值内存 0.57 GB）→ `evidence/M080_EXTRACT.json` 与 3 个 CSV。
- 写入方式：`scripts_project/m080_data.py` → `fragments/m080.csv`（新行）+ `fragments/m080_corrections.csv`（对已有行的整行替换）；`d1_registry.py` 只增加片段名与"按 param_id 整行替换"的几行，原片段不动（保留为历史）。
- M1 结果：新增 87 行（VRE 分国上限 55、土地规则 8、数据文件 3、廓线文件 2、屋顶光伏方法 1、Astar 3、地热 3、LNG 12）；LNG `lng_import_cap_*` 11 行只加注释；注册表 2,049 行；测试 91 passed / 24 skipped。

## 续行点

M2：海上风核实行（证据已在 `M080_EXTRACT.json`）；之后 M3 状态 / 等级修正（`m080_data.py --steps M1 M2 M3`）。
