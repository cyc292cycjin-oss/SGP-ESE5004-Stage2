# GitHub Actions health

**ACTIONS_HEALTH = PARTIAL。不是只有CodeQL失败，也不是所有Actions失败。** API当前返回共21个可见历史run；10个注册workflow，其中9份仓库YAML、1个Dependabot动态workflow。以下latest按各workflow最近运行，不把SKIPPED/NO_RUN误标PASS。

| Workflow | LatestRun | Commit | Status | FailureStage | RootCauseKnown | ActionRequired |
|---|---|---|---|---|---|---|
| CodeQL | [37048744962](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37048744962) | a3616a68 | FAILURE | SARIF upload | YES：code scanning功能不可用 | 仓库资格/服务边界决定；无YAML根因修复。 |
| Deploy MkDocs site to GitHub Pages | [36313652188](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36313652188) | a3616a68 | FAILURE | Setup Pages | 部分：Pages API拒绝，具体服务配置/资格未单独治理 | 另审Pages是否需要及设置；本轮不公开站点、不启用服务。 |
| Dev Container Build and Push Image | 无可见run | — | NO_RUN | — | NOT_TESTED | 无证据宣称PASS；非本次CodeQL阻断。 |
| Docs CI | 无可见run | — | NO_RUN | — | NOT_TESTED | 路径触发型PR workflow；后续相应变更再验证。 |
| Lint | [36313847449](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36313847449) | 5568912a | SUCCESS | — | N/A | 保留已有成功证据，不重跑。 |
| .github/workflows/main.yml（contributors） | [36817994582](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36817994582) | a3616a68 | SKIPPED | job条件 | YES：schedule只允许上游owner pypsa-meets-earth | 预期跳过，不是失败或YAML不能解析。 |
| Test workflows | [36524269304](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36524269304) | a3616a68 | SUCCESS | — | N/A | 7个job全部success；历史外部下载不稳定另记录。 |
| Update locked envs | [36834440056](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36834440056) | a3616a68 | FAILURE | Generate lockfiles for all platforms | 近因YES：conda-lock找不到et_xmlfile缓存分发；最深原因未证实 | 独立依赖/缓存维护；不因此改科学锁文件或升级环境。 |
| Update reference objectives | 无可见run | — | NO_RUN | — | NOT_TESTED | 不触发；修改参考objective不属于本次基础设施任务。 |
| Dependabot Updates | [37055963303](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37055963303) | a3616a68 | SUCCESS | — | N/A | 更新任务能运行；不自动合并其PR。 |

## CodeQL跨分支历史

| Run / event | Commit / Action | 分析与上传 |
|---|---|---|
| [36313652192](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36313652192)，2026-09-27 push main | a3616a68 / v4.38.0 | SARIF生成成功；上传因code scanning未启用失败。 |
| [36313847572](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/36313847572)，同日Dependabot PR | 5568912a / v4.38.2 | 同一错误；补丁版本升级未消除根因。 |
| [37048744962](https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2/actions/runs/37048744962)，2026-10-02 UTC schedule main | a3616a68 / v4.38.0 | 同一错误，匹配本次通知。 |

当前可见CodeQL历史从此仓库建立时即失败，没有一个更早成功run可用来定位“某科研提交引入回归”。两个main失败是相同SHA；不能把时间上在Phase3之后收到通知解释成Phase3导致。也不能把失败归因于仅fork/Dependabot权限：main schedule实际拥有security-events:write。

## 其他失败的最早可见原因

**Pages：** `Setup Pages`日志首先报“Get Pages site failed…Resource not accessible by integration”，后续deploy跳过。它发生在文档构建后、部署准备时。独立Pages可用性/访问设置问题，本轮未把它归为CodeQL漏洞或Python错误。仅凭此日志不精确断言“已经确认是哪一项Pages套餐/设置”。

**锁文件更新：** 多次找不到`et_xmlfile-2.0.0-pyhd8ed1ab_1`的repodata_record.json后，conda-lock抛`FileNotFoundError: Distribution ... not found in pkgs_dirs`。这是本run可证实近因；不能只凭日志决定更新et_xmlfile、conda-lock或全部环境。本次失败没到create-pull-request，没修改仓库锁文件。

**历史测试：** 2026-09-27 push和Dependabot PR曾在`download_osm_data`失败。Ubuntu日志先有Geofabrik的503（Nigeria/Benin md5下载），后续earth_osm发生NoneType/AssertionError；macOS/Windows也有下载链异常。不是CodeQL失败带来的连锁错误，也不是已证实的科学算法回归。9月29日相同main SHA的定时测试7个job全部成功，包括三种OS的普通环境和pixi组合；这支持外部数据依赖不稳定的判断，但不证明全部外部源永久健康。

原始job、annotations、完整日志与行号摘录均已保存。未重跑make test、未触发任何solver；这里使用的是历史GitHub运行证据，不声称本轮重新验证了科学模型。
