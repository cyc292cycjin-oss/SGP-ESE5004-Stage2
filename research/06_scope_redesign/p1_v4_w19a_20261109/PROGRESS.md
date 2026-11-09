# V4 W19a 进度（只读准备：KH 封存上限 / WACC 口径 / 0.25 出处 / 注册表重数）

恢复点按最后一行为准。时间为 SGT（按 `date -u` 校正；会话创建于 2026-11-09 07:18 SGT = 2026-11-08T23:18Z）。

- 07:19 开工核对：`V4_W19A_INSTRUCTION.md` SHA256 = e284f70ddd0d36e9c6cc3aaef45dc076bbfc9d4397abd29a7f21e251b5c5b9a5，与 `V4_W19A_SHA256.txt` 一致。会话模型 claude-opus-5-5、effort xhigh（get_session self）。其他 Claude Code 会话均 isRunning=false；WSL 无 gurobi / s2_solve 进程，Windows 无 gurobi 进程；WSL 可用内存 9 GiB。
- 07:21 分支改名核实：`git ls-remote --heads origin` 中 `refs/heads/codex/` 0 条、`asean/` 74 条；`asean/v4-w14-20261109` 远端 = 本地 = ac75354c。F1 / F2 的 HPC 提交状态本机无法核实（不连 HPC），按用户启动本步视为满足。
- 07:22 新建分支 `asean/v4-w19a-20261109` @ ac75354c，worktree `/home/jin/wt_v4_w19a`；W14 包 COMMIT 26c2e47d 是祖先（其后只有 0bf6a807、ac75354c 两个交付提交）；core.hooksPath 未设。
- 07:23 先读材料已读。包 COMMIT 注册表 SHA256 a9798b0c…（2,469 行），与代码包、W14 worktree 副本相同；基线 aad8e476 注册表 93dbeb43…（= W10 META）。
- 07:25–07:33 第 2.1 节：KH CO₂ 账（D2a 缓存 7508ec72 / 4cc51892；网络与对偶 SHA256 与 export 文件一致）；直接读两张已解网络复算一致（`scripts/w19a_2_verify_nc.py`，20 s，峰值 0.88 GB，读前 MemAvailable 9.8 GiB、无 Gurobi）。发现 KH 注册表行实际有登记区间 1.8–900 Mt/a（与指令"注册表无区间"不同）。
- 07:33–07:38 第 2.2 节：`scripts/w19a_3_kh_bracket.py` → `KH_CO2_ACCOUNT.csv`、`evidence/KH_CAP_BRACKET.json`；`evidence/KH_LINK_LIMITS.json`（KH 封存链路可扩展、p_nom_max = inf、零成本 → 可行解界成立）。
- 07:30–07:40 第 2.3 节文献：ERIA 2024 第 1 章（WebFetch 存入工具缓存，复制到 scratchpad 单独目录后 pypdf 抽字）；CSRC Cycle 5 用本机原文（SHA256 = 注册表）；Mao et al. 2014 只取得摘要（机构库 PDF 抽不出正文；ScienceDirect 403；Scribd 转载副本被拦截，未使用）；OGCI 网站 403。
- 07:40–07:44 第 3 节 WACC：注册表行、D2b E60–E70、S4R 指令 F7、L23 指令（第 111 项）、M10P（第 132 项第 5 条）；IEA 观察站口径重读；M10S1 R10 / R11 参照。
- 07:42–07:47 第 4 节 0.25：`d1_biomass.py:50 / 281 / 311`；IRENA 2022 / 2017 本机原文（SHA256 前缀与代码登记一致）抽字核对；含义与第 224 项第③条一致，未停止。
- 07:47–07:53 第 5 节：`scripts/w19a_4_registry_tiers.py` → `REGISTRY_TIERS.csv`、`evidence/REGISTRY_C462_CLASSES.csv` 等；`scripts/w19a_5_top30.py` → `TOP30_STATUS.csv`（审阅端 05:00 分类在工作区内未找到）。
- 07:53–07:55 第 3 节换算：`scripts/w19a_6_wacc_basis.py` → `evidence/WACC_BASIS.csv/json`（税率 INFERENCE）。
- 07:55–07:59 `REPORT.md`、`DOWNLOAD_CANDIDATES.csv`、`evidence/APPENDIX_LITERATURE.md`、`EVIDENCE.json`（`scripts/w19a_7_evidence.py`）；用户下载目录无新文件。
- 恢复点：同步到仓库目录、泄露扫描、提交 W19a-1、审阅包与清单、提交 W19a-2、推送。
