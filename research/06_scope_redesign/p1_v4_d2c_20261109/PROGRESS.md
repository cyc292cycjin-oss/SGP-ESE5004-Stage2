# D2c 进度（V4_D2C_INSTRUCTION.md v1，SHA256 18f6e4037de2a4ab770c6d27e77e9e36fcb8e93788aaf77cbfc226e642db95b1 已核对，与 V4_D2C_SHA256.txt 一致；开工 2026-11-09 02:10 SGT）

- 执行：Claude Code，模型 Opus 5.5（`claude-opus-5-5`，开工时确认）；指令要求 effort Xhigh，会话的 effort 设定本会话看不到，不能自证（报告中注明）。
- 分支 `codex/v4-d2c-20261109`，起点 `25bd7cf0be0c17caac1fcc272ed2f3c2779312d2` = `codex/v4-d2b-20261108` 头（fetch 核过，本地 = 远端）；`4e90ea4b` 是其祖先，二者之间只改了 `research/06_scope_redesign/p1_v4_d2b_20261108/` 下 2 个文件（PROGRESS.md、evidence/REVIEW_ZIP_MANIFEST_4e90ea4b.txt），交付目录之外 0 个（`/home/jin/v4d2c/s1_verify.log`）。
- worktree `/home/jin/wt_v4_d2c`；临时目录 `/home/jin/v4d2c`；主检出 `results_project/v4d2c/`（构建与冒烟输出，不入库）。
- 交付目录 `work/p1_v4_d2c_20261109/` = 仓库 `research/06_scope_redesign/p1_v4_d2c_20261109/`（zip 不入库）。
- 额度：求解器至多 2 次（第 4 节），已用 0 / 2；本机计算上限 1.5 小时；磁盘新增上限 5 GB。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| D2c-1 | 第 1 节：分支、worktree、祖先核实 | 完成 | （随 D2c-2 提交） |
| D2c-2 | 第 2 节：每株树干干重、`v4_adjusted_t06`、潜力表、S7 检查点、注册表 | 完成：每株树干干重 Chow 0.2740（37.264 / 136）、Henson 0.2834（图 8 多项式 25 年 41.95 t DM/ha ÷ 标准 148 株/ha，Henson 原文 p.8 与附录 1 新读，`evidence/D2C_TRUNK_LITERATURE.json`）、Khalid 0.3020（41.07 / 136）→ 中心 0.2834，区间 0.2740–0.3020（`TRUNK_DRY_MASS.csv`）；系数 0.152322（0.147246–0.162285），T05 0.313480 为高档开关值；`BIOMASS_BASIS_T06.csv` 只有树干行与 T05 不同；T06 潜力文件与 T05 只差 5 个树干行（首次重算时 EFB / 纤维的来源说明误标 T06，已改为沿用 T05 文本后逐字节相同）；树干 72.50 → 35.23 TWh，东盟固体 1,289.32 → 1,252.05 TWh；W08 / T04 / T05 文件逐字节不变；表目录主集 `out_ras` / `out_iid` 只有潜力上限列变化，敏感性目录 `out_ras_74ec30609dc1` → `out_ras_ac0116bd99da`；检查点 main_t06 16 步 / iid_t06 15 步对 T06 参照逐国 0 差，`T_v2` 3,490.338 / 3,166.522 不变，S7 溢出只有 VN 41.10 / 32.07 不变；注册表 2,463 → 2,469（+6），树干 5 行区间改为 T06 低 … T05；v4 测试 99 过 / 1 跳过（含 A2 回退） | D2c-2（本行所在提交） |
| D2c-3 | 第 3 节：重建 56 时段网络与静态检查 | 完成：构建（提交 `8d05c2da`）第一次即成功，一体化 `db33f84e…`、`no_new_xb` `f03aab19…`（1 分 26 秒，1.07 GB）；C8 对 D2b 两网两分辨率只有 5 个树干 Store 的 `e_nom` / `e_initial`，无 UNEXPECTED；元数据差异均为树干池账面、开关 SHA、构建 worktree 路径；C1–C6、C10–C12 通过（C12 LNG 边际成本与 D2b 相同）；零松弛门两网通过（705 / 589 行）；F-05 等网络测试 25 过 | 随 D2c-3/4a 提交 |
| D2c-4 | 第 4 节：报警线登记（求解前提交）与 2 次冒烟 | 完成：登记（`SMOKE56_D2C.md` 第 1 节，只有右端类，报警线 R1 +2,881.00 / R2 +2,996.37 M EUR）后求解 2 / 2 次（18:38–18:56 UTC，间隔 331 s，令牌预检通过，无重试）；两次 optimal、ACCEPTED_LAYER2、C1 a/b/c 接受、失败门 = D2b（并集内）；ΔV +2,892.20 / +3,004.41 M EUR，高于报警线（超出下界 +10.84 / +7.67 M）；D2c 解中树干池仍全部用尽，边际价值只略升；56 时段 B6 12.9536 bn | 登记 `88bbbe57`（D2c-3/4a，求解前）；结果 D2c-4b |
| D2c-5 | 第 5 节：报告、证据、审阅包、推送 | 完成：`REPORT.md`（第 0 节结论 7 条 + 待决 5 条）、`EVIDENCE.json`（24 条）、`LEDGER_ENTRY_DRAFT.md`、`evidence/D2C_TRUNK_DUALS_POST.json`；全量 `tests/research` 875 过 / 1 败（既有 S1 项）/ 56 跳过（31 分 44 秒）；审阅包、泄露扫描与推送见 D2c-5b | D2c-4b/5（本行所在提交）、D2c-5b |

续做点：全部 5 节完成。提交链 `8d05c2da`（D2c-1/2）→ `88bbbe57`（D2c-3/4a，求解前登记）→ `612d8f6b`（D2c-4b/5）→ D2c-5b（审阅包清单 + 本行）；推送 `codex/v4-d2c-20261109` 后停止，没有开 PR，等待审阅。审阅包 `REVIEW_612d8f6b.zip`（对提交 `612d8f6b` 的交付目录 + 代码与数据差异 `25bd7cf0..612d8f6b`；52 个成员（含 MANIFEST.tsv），233,390 字节，SHA256 `0a29431e29b6afb2361fb53a36a47bf1236420f3c23726dcc61d4f5d3872daec`；清单 `evidence/REVIEW_ZIP_MANIFEST_612d8f6b.txt`；zip 不入库）；泄露扫描交付目录 0、zip 0 命中。求解器 2 / 2 次。未做：中心值纳入规则、Henson 独立性、收获上限 0.25 含义、翻种率低档是否进 W19（报告 0.1，交审阅端）。
