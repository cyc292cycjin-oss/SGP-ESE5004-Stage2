# W08 进度（V4_W08_INSTRUCTION.md v1，SHA256 17fdf2f1…c077c0 已核对，与 V4_W08_SHA256.txt 一致）

- 分支 `codex/v4-w08-20261106`（起点 `aad8e476` = `codex/v4-i2-20261106` 头，开工时本地与远端一致），worktree `/home/jin/wt_v4_w08`。
- 交付目录 `work/p1_v4_w08_20261106/` = 仓库 `research/06_scope_redesign/p1_v4_w08_20261106/`（zip 不入库）。
- 参照引擎临时目录 `/home/jin/v4w08/ref_main`、`/home/jin/v4w08/ref_iid`（I2 引擎副本，第 1 节）。
- 求解额度：第 5 节 4 次 56 时段求解（v3.1 对照、v4 一体化、v4 不互联、v4 IId 一体化）；已用 0 次。

| 步 | 内容 | 状态 | 提交 |
|---|---|---|---|
| W08-1 | 第 1 节：I2 引擎加第 0 节两处修改，参照值 REFERENCE_V4_MAIN / REFERENCE_V4_IID | 完成：副本复核 0 差（复核组 = I2 S1 / S7，IId 组 S0–S1 = I2）；东盟 S7 主算 3,490.338011、IId 3,166.521855 TWh（`scripts/w08_ref_*.py`、`tables/W08_REF_*.csv`、`evidence/W08_ref.json`） | 见 git log（W08-1） |
| W08-2.1 | 清单第 1 节：SDMX 基年（检查点 S1 在第 3 节后） | 完成：`v4_base_sdmx.py`（I1 Recon / blend / rail_children / d1_rows 原样移入；`reconstruct_base_accounts.py` 不改）；胶囊、v4 种子、掺混备忘与 I2 逐字节相同；G1–G3 通过；`test_v4_base_sdmx.py` 5 项 | 见 git log（W08-2.1） |
| W08-2.2 | 清单第 2 节：分行业缓存 | 完成：`v4_industry_cache.py`（I2 cells / build_cache / residues 原样移入）；输入表 RESIDUE_CLASSES、NATIONAL_BALANCE_BIOMASS_COVERAGE、FUELWOOD_OUTSIDE_BALANCE；缓存三种开关组合与参照逐值相同；`test_v4_industry_cache.py` 4 项（缓存和对 D1 工业行时须加回掺混扣减量，ID 生物质含燃料木材、木炭与生物柴油三项） | 见 git log（W08-2.2） |
| W08-2.3 | 清单第 3 节：锚构造与锚边界（检查点 S1、S2） | 完成：`m08b_demand.py` 选项 `--anchor-mode ras/iid/iib/external`、`--residue-anchor-adj`（各模式都适用）、`--out-dir`；`s3_0_industry.py` 选项 `--only-mode` 等（默认路径不变，A2 逐字节通过）；`v4_industry.py`（I2 引擎移入，`run_case`）；冻结 v3 锚表（与参照 v3 锚逐位相同）；检查点主算 S0/S1/S2、IId S1/S2 与参照差 0；测试 `test_v4_anchor_iid.py` 4 项、`test_v4_a2_fallback.py` 2 项 | 见 git log（W08-2.3） |
| W08-2.4 | 清单第 4 节：(ii) 类（检查点 S3） | 待做 | |
| W08-2.5 | 清单第 5、6 节：自备、燃料木材（检查点 S4） | 待做 | |
| W08-2.7 | 清单第 7 节：子部门（检查点 S5、S6） | 待做 | |
| W08-2.8 | 清单第 8 节：网络层（检查点 S7） | 待做 | |
| W08-2.9 | 清单第 9 节：小时曲线 | 待做 | |
| W08-2.10 | 清单第 10 节：注册表与配置哈希 | 待做 | |
| W08-4 | 56 时段网络重建与静态检查 | 待做 | |
| W08-5 | 4 次 56 时段求解 | 待做 | |
| W08-6 | 报告、证据、审阅包、HPC 草案、推送 | 待做 | |

续做点：见上表第一个"进行中 / 待做"的行。
