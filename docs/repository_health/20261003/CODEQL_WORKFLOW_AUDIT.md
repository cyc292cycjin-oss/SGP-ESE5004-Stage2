# CodeQL workflow audit

固定读取：`a3616a68ee44592af6527ca9024a90f1956646ae:.github/workflows/codeql.yml`。证据副本位于 `evidence/source/.github/workflows/codeql.yml`；所有workflow副本来自Git blob，不编辑原文件。

| 检查项 | 当前配置 / 实际运行 | 审计结论 |
|---|---|---|
| checkout | actions/checkout@v7，实际SHA 3d3c42e5aac5ba805825da76410c181273ba90b1 | 对应官方v7.0.1；本次checkout成功。 |
| init / analyze | github/codeql-action/{init,analyze}@v4.38.0；SHA b96794f015dfd88f77b49b1c93e0fa7110f94c63 | 当前v4系列；不是退役v2或v3误用。 |
| CLI | 附带2.27.0 | feature-flag API不可用后fallback；成功分析。 |
| Language matrix | include: language=python，build-mode=none | 适合解释型Python。 |
| autobuild / manual | 没有autobuild action；manual echo＋exit1占位step仅在manual时执行 | 本次condition=false、skipped；不导致失败。无需编译/安装整个科研环境。 |
| Triggers | main push；目标main的pull_request；每周五18:23 UTC schedule | 实际失败为schedule。没有workflow_dispatch。 |
| Fork/PR | 标准pull_request，未用pull_request_target | fork/Dependabot运行须遵守其令牌限制；这不能解释main schedule的失败。 |
| Permissions | job级security-events:write；actions/contents/packages:read | 实际令牌一致；仓库默认read被job显式权限适当覆盖。 |
| Packages | packages:read配置存在 | 未配置私有query pack；不是本次根因，不需扩大权限。 |
| Runner | 表达式对python解析为ubuntu-latest；本次Ubuntu24.04.5，runner2.337.0 | 初始化与分析成功；Ubuntu26迁移仅未来notice。 |
| Concurrency | 未配置 | 不是2m54s失败原因；可作为后续维护项，不混入此次修复。 |
| Custom config/query packs | 无生效config-file、queries或packs输入；仅注释示例 | 使用默认分析集合。 |
| paths / paths-ignore | CodeQL workflow无路径过滤，无自定义CodeQL过滤 | 不能把其他workflow或gitignore的过滤当成本分析排除。 |
| SARIF | analyze默认上传，category=/language:python | 生成成功、服务器拒绝上传；没有成功结果可核实。 |
| YAML | 9份workflow均以保留on键的BaseLoader解析，并检查jobs映射 | 语法通过不代表所有workflow设置/业务均可用。 |

## 2026版本支持证据

[官方CodeQL v4.38.0 release](https://github.com/github/codeql-action/releases/tag/v4.38.0)对应日志SHA并附带CLI2.27.0；[官方checkout v7.0.1 release](https://github.com/actions/checkout/releases/tag/v7.0.1)对应日志checkout SHA。未因工具旧知识把2026已发布的v7误判为不存在。

[官方版本公告](https://github.blog/changelog/2025-10-28-upcoming-deprecation-of-codeql-action-v3/)说明v4已发布、v3计划2026年12月弃用；本次不是v3。支持的版本不必等于最新补丁。已有v4.38.2的PR仍同样上传失败，不做与根因无关的版本升级。

[固定版本README](https://github.com/github/codeql-action/blob/v4.38.0/README.md)支持解释型语言使用none以及code-scanning写权限要求。本次配置符合这些要求；不安装PyPSA依赖或运行Snakemake来让CodeQL通过。

## Python发现与目录边界

默认分支有78个`.py`路径，完整日志能逐一匹配78条Extracted file记录，没有缺失路径；最终analyzer自身摘要为77/77 Python。二者统计口径不同，保留原数值，不强改为“78/78摘要”。9/9 Actions也有摘要；未观察到阻止本次分析的Python语法错误。

默认分支还有5个`.ipynb`；notebooks/analysis_helper.py在提取日志中，但不能由此声称notebook全部单元已扫描。`.gitattributes`中的linguist-vendored只作该配置的事实记录，不作为CodeQL排除/覆盖证明。

当前main没有跟踪venv、.venv、site-packages、node_modules或__pycache__，没有Phase1–3 research归档树或大型生成结果树；主要大文件是已跟踪的预构建OSM CSV。个人本地审计仓库中确有固定源码快照，但它们未在本次main运行中出现，不能将其归为此次CodeQL失败的原因。

若未来经审阅把研究层托管到GitHub，需明确活动研究脚本与只读历史快照的扫描范围，避免把归档重复扫描当实际工作代码覆盖；本轮不添加paths-ignore，也不删除任何证据。

## 最小改动判定

**WORKFLOW_CHANGE_REQUIRED_FOR_THIS_ROOT_CAUSE = NO。** 正确的下一步是解决或明确接受仓库code-scanning资格/可用性限制。不能以security-events:write再加一次、upload:never、continue-on-error或跳过job来声称CodeQL已修好。

未创建代码修复分支/commit，未push、PR、merge，也没有“修复后重跑PASS”。条件式CODEQL_FIX_REPORT不适用。
