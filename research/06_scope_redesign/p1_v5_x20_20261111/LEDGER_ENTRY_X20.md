### V5 X20（师哥 11-11 第 1–16 条的 v5 输入修订实施；决策清单第 240–246、251 项）— 2026-11-12

- **指令：** `work/p1_v5_x20_20261111/V5_X20_INSTRUCTION.md` v1，SHA256 `5126e2a7…cb92`，已核对一致。分支 `asean/v5-x20-20261111`（起点 W14 包 COMMIT `26c2e47d`），worktree `/home/jin/wt_v5_x20`；A 段规格 `X20_SPEC.md`（`7ac713e5`），B 段按决策 246（Q1–Q18）与 251 实施。未合并 main，未 force-push，未跳过 hooks；不连 HPC；下载只有 OSM way 标签（427,221 B）与 NGCP TDP PDF（5,415,314 B）。
- **实施：** 20 项修订全部挂开关（v5 主值 = 新值，回退 = W14 行为），每项一个提交（`ddc1c071` … `b05753a1`）；v5 关闭时 4 张网络与 W14 逐值相同（VERIFIED）。①1 停止点后经决策 251 把越界检查改为有效倍数核对（看到结果后的规则更正，国别中位数 0.831–1.312，在 [0.8, 1.6] 内）。注册表 2,469 → 2,572 行。
- **构建（b05753a1）：** v5 主集 F1 2920×3h `efe4b1b1…`、F2 `4e43568b…`（D 盘 `builds/v5main`）；静态检查（W14 C1–C12、C6b、C6v5，B1、B11–B16）与零松弛门全部通过。
- **输入桥表** `X20_BRIDGE.csv`（284 行，VERIFIED）：MY 交流 −56.6 GW；PH 直流每方向 16,193 → 1,330 MW；气上限 2,149 → 1,595 TWh/a；NEU 气 380 → 298 TWh/a（ID 84 → 0）；存量水电入流 230 → 275 TWh/a，新建水库单位入流 ID 0.49 → 0.71；ID 地热上限 22.4 → 15.4 GW；2050 存量 +6.2 GW；低压负荷 2,350 TWh/a；陆上风电候选 CF ASEAN 5.35 → 3.58 %（TH 14.1 → 7.9 %）。
- **测试：** v5 全量 1 failed / 919 passed / 55 skipped（唯一失败与 v4 基线相同）。
- **56 时段回归（Gurobi 2 次，Q18 门槛通过，SMOKE_TEST_ONLY，不作数量结论）：** F1 optimal 396,174,224,434.25、F2 optimal 410,510,617,063.03 EUR（v4 同截取冒烟 +9.08 % / +9.14 %）；V6 ACCEPTED_LAYER2 ×2；Owen 前提通过（低压母线无未归属右端项），分摊全部为正，受益符号只有 ID（+ → −）、LA（− → +）改变。
- **待审阅端判断：** ①5 的已投运分母使 ID / MY 单位入流折合 CF 0.69 / 0.65 并传给新建候选（L-C10）；①1 候选 CF 为"GWA 毛值 ÷ r"的 0.53–0.74（L-C11）。偏离 10 条、局限 33 条见 `REPORT.md` §8 与 `LIMITATIONS_V5.md`。
- **交付：** `research/06_scope_redesign/p1_v5_x20_20261111/`（`REPORT.md`、`X20_BRIDGE.csv`、`LIMITATIONS_V5.md`、`ONWIND_SANITY_V5.csv`、`SOURCES.csv`、`DOWNLOAD_CANDIDATES.csv`、`EVIDENCE.json`、`PROGRESS.md`、`evidence/`、`scripts/`），镜像 `work/p1_v5_x20_20261111/`；审阅包 `REVIEW_f08b14b0.zip`（`REPORT.md` SHA256 `f08b14b0…`，不含网络文件；包的 SHA256 见 `REVIEW_ZIP_SHA256.txt`）；提交号与推送结果见 `PROGRESS.md` 最后一行。等待审阅端审阅。
