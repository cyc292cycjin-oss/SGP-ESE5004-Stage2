# S4P 进度文件（第 122 项第 (2) 点：全模型、11 国核查；只读）

- 指令 `S4P_CLAUDE_CODE_INSTRUCTION.md` SHA256 `b94ccb88…38ca0`，与 `S4P_INSTRUCTION_SHA256.txt` 一致（2026-10-20 核对）。
- 分支 `codex/s4p-country-audit-20261020`（自 S4O 头 0b681881），独立工作树 `/home/jin/wt_s4p_20261020`；draft PR 叠在 #40 上（待建）。
- 只读：不求解、不连云、不改模型 / 网络 / 配置 / 结果。分析脚本在 `scripts/`，输出在本目录。

## 子步骤

| 步 | 内容 | 状态 | 提交 | 说明 |
|---|---|---|---|---|
| S4P-0 | 核对 SHA、读背景、开分支与工作树、进度文件 | 完成 | 373e6ef4 | |
| S4P-A | 分国差额通道分解（必做 A） | 完成 | 373e6ef4 | `A_CHANNEL_DECOMPOSITION.md`；明细加总 B6 69.2429 bn，恒等式最大偏差 3e-5 EUR |
| S4P-1…8 | 矩阵八个方面的数据表 | 完成 | 373e6ef4 | `ASPECTS_TABLES.md`（网络提取 `scripts/s4p_net_extract.py` → `evidence/net/`，8 MB，不入库，可重生成） |
| S4P-M | 核查矩阵 13 × 8 | 完成（外部对照 4 / 7 待补） | 本次 | `COUNTRY_AUDIT_MATRIX.csv/.md`；覆盖项 `evidence/EXT_OVERRIDES.json` |
| S4P-E | 外部对照检索（三个子代理） | 政策 / 封存 / 海风 / 生物质 完成；需求 + 钢铁水泥、成本 进行中 | 本次 | `evidence/EXT_TECH_POLICY_BENCHMARKS.md/.json` |
| S4P-B | 跨区域一致性（必做 B） | 完成 | 373e6ef4 | `ASPECTS_TABLES.md` 末节 |
| S4P-C | 按影响量级排序与修正建议（必做 C） | 草稿完成（F1–F13） | 本次 | `PROPOSED_FIXES.md` |
| S4P-R | 报告、证据 JSON、外部来源清单、台账、PR | 完成 | 本次 | 三个子代理全部返回（需求 128 条、政策 80、成本 90；DATA_PENDING 24）；`EXTERNAL_SOURCES.md` 298 条 |
| S4P-S1 | 补充 01（SHA256 f601b5a8…c83a8 核对一致）：货币与价格年份一致性核查并入方面 7；NZE 降为低优先级 | 完成 | 本次 | 报告 §4.7.2 清单（15 项）、F14、用户决定事项第 6–7 项；矩阵方面 7 加货币摘要 |

## 续行点

**S4P 与补充 01 全部完成，停下等待审阅。** 分支 `codex/s4p-country-audit-20261020`，draft PR 叠在 #40（见报告 §11）。所有修正均为 PROPOSED，未实施；任何重跑需另行授权。
