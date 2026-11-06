# 进度（v4 W08 独立审查，Fable 5.1；2026-11-07）

- 00 开工：两份文件 SHA256 核对一致；W08 头 `7aa356e4`（含 `bd890bf9`、`aad8e476`）；新开分支 `codex/v4-fable-w08-20261107`，worktree `/home/jin/wt_v4_fable`。独立性瑕疵：附录在核对 SHA 时被一并打印（已在 FINDINGS_PRE 声明）。
- 01 规格、W07 / W08 指令、I2 报告第 0 节读完；6 个被改脚本 diff、10 个新模块、10 个测试文件通读。
- 02 临时副本 `/home/jin/v4fable/`（repo / a2 / tests_copy）；A2 回退：默认运行写出的 56 个文件全部与 `d3b9a3bc` 逐字节相同。
- 03 S7 主算 / IId 检查点复现 = 参照（≤ 5e-10 TWh）；out_ras / out_iid 24 表重生成逐字节相同。
- 04 数据链手算 21 条（自写 XML 解析器）全部一致；注册表 67 文件行 SHA 一致、重组一致；许可扫描无命中。
- 05 网络层（主算 / IId 2920×3h）：负荷 = 表、气上限 = 表、曲线守恒；发现 VN 溢出报告量 29.95 / 20.93 对网络 41.10 / 32.07（F-02）。
- 06 锚构造、曲线、残渣对称、守恒检查完成；造纸木材字面读法量化（ID +36.89 TWh，F-01）。
- 07 v4 测试 37 项在副本中全部通过（注册表两项补齐上游 `scripts/`、`config.default.yaml` 后通过）。
- 08 FINDINGS_PRE.md 写成；开关全关网络构建（W08 代码，1.5 分钟）与 v3.1 包网络 10 类组件逐值相同（仅 meta 配置快照 / 哈希 / 气网台账新键不同）。
- 09 第 3 节提交 `6abe892f`（FINDINGS_PRE 等 54 个文件），推送到 `origin/codex/v4-fable-w08-20261107`。
- 10 第 4 节：读 W08 REPORT 第 0–6 节、SMOKE56_V4、HPC 草案、附录；只读分解三次冒烟解（目标常数相同、生物质去向、价格恒定、成本台账逐国 / 逐类别差异）；REPORT.md 写成，FINDINGS.csv 加 F-20–F-22。
- 11 第 5 节：EVIDENCE.json、审阅包与清单、最终提交推送（提交号见下一行）。
- 12 最终提交链：第 3 节 6abe892f → 第 4–5 节 93649c3e00cc23e3f1082ec00aeeae65841eaec3 → 清单与本行（见 git log 最新提交）；审阅包 REVIEW_93649c3e.zip（zip 不入库，清单 evidence/REVIEW_ZIP_MANIFEST_93649c3e.txt 入库）。推送到 origin/codex/v4-fable-w08-20261107 后停止，等审阅。
