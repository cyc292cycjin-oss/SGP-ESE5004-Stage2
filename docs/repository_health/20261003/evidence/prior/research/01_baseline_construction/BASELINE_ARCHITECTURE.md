# 三层基准架构 — 2026-10-01

**版本身份已冻结；Full-SC 科学边界尚未冻结。** 来源为官方 Git、作者网络内嵌配置及现有本地输入，非对数据的人工验收。

| 层/分支 | 完整 SHA | 当前状态 |
|---|---|---|
| Paper Reference / `codex/paper-reference-5bacad70` | `5bacad702ccfed17ad19ab510fa710651e966f2c` | 源码清洁；DAG预检到缺输入；未正式重建/求解 |
| Upstream SC / `codex/upstream-sc-baseline-a3616a68ee44` | `a3616a68ee44592af6527ca9024a90f1956646ae` | 官方main固定源码；默认仍裁剪到电力案例，不能直接称已验证full-SC |
| Research / `codex/research-sc-main` | `a3616a68ee44592af6527ca9024a90f1956646ae` | 从Layer 1分出；零研究修改、零研究求解 |
| 工业修复 / `codex/fix-industrial-gdp` | `a7a8f06b43f0dcce0dbd7005b989d8f73d142b81` | 独立工程提交及回归测试通过；未合入Layer 1/2 |
| 碳键修复 / `codex/fix-carbon-config` | `753ac81c23f8b9a1ca8ceed531d0630b56f6953d` | 独立配置修复及回归测试通过；未合入Layer 1/2 |
| 拓扑诊断 / `codex/fix-topology-765-766` | `a3616a68ee44592af6527ca9024a90f1956646ae` | 只读诊断；无修复提交 |

官方入口：[https://github.com/pypsa-meets-earth/pypsa-asean.git](https://github.com/pypsa-meets-earth/pypsa-asean.git)，branch=`main`，抓取时刻 `2026-09-30T17:25:48.957281+00:00`。远端可能继续变化，本报告始终引用完整SHA。

隔离目录：`/home/jin/research/SGP_ESE5004_Stage2/phase2/`；每层都是独立工作目录，共享新建model-source对象库；原教程目录及commit `ce327bfae2abe5526d4c1976173f0f8d08366ba5` 未改。详细路径在 [LAYER_IDENTITIES.json](LAYER_IDENTITIES.json)。本轮没有force-push，没有覆盖旧结果。

研究代码/证据在 `research/01_baseline_construction/`；小型登记在其 `data_registry/`；大文件在既有cache或隔离工作区，仅提交身份/脚本。建议未来项目根层data/raw、processed、derived采用同一来源ID索引，当前未移动历史资产。所有修复先review再合入具名validation分支，未经检验不把修复后的网络冒充Paper Reference。

未来比较对象已由用户给定：同一个区域Full-SC模型，仅关闭跨境AC/DC电力连接；Baseline与DEC均保留，DEC仍为区域共享的电力口径预算；不拆国家碳配额。研究方向已确定，但可执行配置尚不具备冻结条件。
