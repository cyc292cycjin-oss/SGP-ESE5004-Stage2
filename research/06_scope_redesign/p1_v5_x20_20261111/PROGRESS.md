# X20 进度（v5 输入修订的实施）

指令：`V5_X20_INSTRUCTION.md`，SHA256 `5126e2a7717df42d1e36bf53f602475605fe7514b81915bf185cad16b896cb92`（`sha256sum -c V5_X20_SHA256.txt` → OK）。
会话模型：Opus 5.5（claude-opus-5-5），effort xhigh。用户启动时说明：决策第 240–245 项已勾选，先只做 A 段，完成后停下。

## 开工记录（2026-11-11 21:36 SGT）

- 其他会话：本机另有 2 个 Claude Code CLI 进程（19:58、20:09 启动），均无 bash / wsl / python 子进程，WSL 内无 python / gurobi / snakemake 进程；判定为应用内保留的空闲会话（X03、X10 已完成），不在运行任务。
- 磁盘基线：WSL `df -h /`：1007G 总，249G 已用，708G 可用（26 %）；`du -sh /home/jin` 246G；D 盘 `df -h /mnt/d`：652G 总，445G 已用，207G 可用；交付目录 13,921 B。
- 内存：WSL total 11,483,643,904 B，available 10,618,589,184 B；swap 4 GiB 未用；nproc 16。
- 分支：`asean/v5-x20-20261111` 从 `26c2e47d025fdd4e46cb278718d93aeddabbe984` 新建（远端无同名分支）；worktree `/home/jin/wt_v5_x20`，A 段为稀疏检出（cone，只含 `research/06_scope_redesign/p1_v5_x20_20261111` 与顶层文件），1.7 MB。稀疏检出使共享配置新增 `extensions.worktreeconfig true`（git 为单个 worktree 启用稀疏检出的标准做法，其他 worktree 不受影响）。
- 仓库无启用的 hooks（hooks/ 只有 *.sample）。
- 代码行号读取：`26c2e47d..ac75354c`（W14 worktree `/home/jin/wt_v4_w14` 的 HEAD）33 个改动文件全部在 `research/` 下，代码与 `26c2e47d` 一致，A 段从该 worktree 只读取行号，不写入。

## 进度

| 时间 (SGT) | 段 | 事项 | 状态 |
|---|---|---|---|
| 21:36 | A | SHA256 核对、模型确认、开工检查、建分支与 worktree | 完成 |
| 21:45 | A | 通读 X03 报告（`c6352f89…`）、X10 报告（`d0a8cb01…`）与 BUNKER_CARBON_MEMO（`6789576d…`）；66 个复用输入算 SHA256，GWA 22 个文件按下载日志核对通过 | 完成 |
| 21:50–22:15 | A | 4 个只读子代理分领域定位代码（可再生 / 存量与燃料 / 碳与需求 / 开关与构建），约 40 处关键行号逐行打印核对（`logs/09`）；补充事实：S1 冻结存量边界机组（`logs/10`）、剖面 nc 入 git 与 W14 / D2c 的内存记录（`logs/11`）、PyPSA-Eur 配电网原文 | 完成 |
| 22:20 | A | 撰写 `X20_SPEC.md`（20 项修订 + 框架；待决问题 18 个）与 `DOWNLOAD_CANDIDATES.csv` | 完成 |

## A 段结束记录（2026-11-11 22:22 SGT）

- 磁盘：WSL `df -h /`：1007G 总，249G 已用，708G 可用（与开工时相同，精度为 G）；交付目录 237,000 B；WSL 家目录新增 = 稀疏 worktree 1,678,823 B + `.git/worktrees/wt_v5_x20` 元数据（< 1 MB）。C 盘与 WSL 家目录新增远低于 1 GB。
- 内存：WSL available 10,676,219,904 B。
- 求解器 0 次；不连 HPC；没有下载；没有修改任何代码、输入、配置或注册表。
- 子代理：4 个 Explore 子代理只读（Grep / Glob / Read）。其中一个开工时用 Bash 执行了一次只读 `ls`，已自报，没有写入。
- 偏离：无。读取 `results_project/s1/S1_SELECTED_ASSET_SURVIVAL_2050.json`（只读 JSON，不是网络），没有用内存门槛（门槛针对网络读写）。
- 提交与推送（交付目录副本补记，不在提交内）：`7ac713e532001dfba5250bb854d51561e87898fa`，分支 `asean/v5-x20-20261111`，已推送，`ls-remote` 与 HEAD 一致；`X20_SPEC.md` SHA256 `d5308511c136ce154168291083f74b30b75cdaf76f26cae7a30ae7480cf2d9a3`（D 盘副本与提交版本逐字节相同）。小瑕疵：镜像文件从 `/mnt/d` 复制，提交时的文件模式为 100755，B 段第一个提交顺手改回 100644。未建 PR，台账条目留到 B 段。
- **下一步：A 段完成，请交审阅端审阅。**

## B 段（2026-11-11 23:10 SGT 起）

用户转达：审阅端通过 A 段规格；待决问题答复为决策第 246 项（`X20_SPEC_ADDENDUM_246.md`）；要求开始 B 段。

| 时间 (SGT) | 事项 | 状态 / 恢复点 |
|---|---|---|
| 23:11 | worktree 改为完整检出（720,515,978 B），复制 finance_v5 两个被忽略输入，`results_project/{assembly_v1,s1}` 链接主检出、`v5x20` 链接 D 盘 `builds/`；本步目录 36 个文件模式改回 100644；WSL `df -h /`：250G 已用、707G 可用 | 完成 |
| 23:15 | 写 `X20_SPEC_ADDENDUM_246.md`（Q12 规则在计算前写定）；B 段第 1 个提交：文件模式 + 补记 | 进行中 | B 段需要等审阅通过、用户转达"继续 B 段"后才开始；开始前须答复 `X20_SPEC.md` 第 6 节的待决问题，尤其是 Q2（冻结底座边界机组）、Q18（56 时段求解的内存门槛）、Q3 / Q4（配电网范围与扣损）、Q1（风电回标口径）。
