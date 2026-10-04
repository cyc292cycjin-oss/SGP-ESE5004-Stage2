# 复现与交接规则（机制设计；尚未实施正式运行器）

本轮只读审计不是正式实验。教程结果保持2030/2040/2050既有身份；不得重命名为paper reproduction。未来研究运行必须同时绑定模型、研究层、配置、数据和环境，不能仅记录一个Git SHA。

## 输入确认与停止条件

执行链固定为 Source → Raw value → Unit/year/currency → Model transformation → PyPSA current value → Final candidate → Human confirmation。台账Status=UNVERIFIED/PENDING不自动升级；需用户与ChatGPT确认记录，关联Parameter_ID、确认值、原始文件哈希、确切sheet/cell/table/page、转换版本和理由。

原始来源缺失、多版本未选择、币种/价格年/HHV-LHV/容量口径/年化不明、模型与公开源不一致、论文版本不明时停止相关数据采用和正式运行，继续不依赖该选择的只读审计。不得借默认值、0、插值或最新文件绕过。范围外/未激活数据应标适用范围，不能因台账含未使用技术而无限延长审计。

## Git规范

1. 正式运行从已提交且已记录的干净代码检出开始。检查tracked修改和untracked文件；ignored输入/结果另以清单检查，`git status`干净不证明数据完整。
2. 提交前缀使用audit/data/fix/config/experiment/analysis/docs；说明Why、改了什么、科学影响、验证。工程、数据修正、模型变更分开提交。禁止force-push、重写教程归档、笼统“update files”。
3. 已确认无效代码在专门清理提交删除并保留历史；用途不明文件、输入、运行日志不得删。本轮没有清理用户已有outputs/work。
4. 研究层与模型层分别记录SHA；若存在补丁则记录基线SHA、补丁列表、最终SHA。不要把结果归档提交冒充实际执行时SHA：旧教程运行meta记录e6dbfafe，随后ce327bfa归档，旧审计已记录运行时差异。
5. 不提交下载缓存、环境目录、访问令牌或原始许可禁止再分发的数据。数据归档可独立存放，但清单和恢复路径必须可访问。

## 配置规范

记录顺序列表：上游default、ASEAN base、project override、runtime override以及命令行参数。每份原文hash、解析/迁移函数版本、effective_config和hash都保存。禁止通过反复手改母配置启动实验。为碳预算、sector裁剪、国家、时间/空间、需求和技术开关输出关键键来源。

override不得只比较YAML文本：旧键迁移、字典深合并/列表替换、默认值可能改变实际结果。保存最终网络meta与有效配置对账；保留warnings，特别是未知键、空需求、默认数据回填与未声明输入。

## 正式run manifest设计

`run_manifest.template.json`是**未执行模板**，null表示待采集，不是0/成功。未来每run独立目录且run_id唯一，示例命名规则`YYYYMMDDThhmmssZ_<scope>_<scenario>_<short_sha>`，不得覆盖既有run。起始记录先写PLANNED，启动前补齐门槛；运行中RUNNING，结束SUCCEEDED/FAILED/ABORTED，同时保留失败重试父ID。

| 必需字段 | 精确定义 |
|---|---|
| run_id | 唯一执行身份；重试使用新ID，parent_run_id指向旧记录 |
| git_commit | 实际模型执行SHA；另有research_git_commit、upstream_baseline、patches、dirty状态 |
| config_files | 按优先级的路径/SHA256数组；另存effective_config及hash |
| input_data_hash | 输入清单hash；清单逐项记录角色、相对路径、字节数、SHA256、来源版本、台账/确认ID |
| environment | OS/WSL、CPU/RAM、Python、Conda explicit/pip清单或锁、原生依赖/PROJ/GDAL/Java及环境文件hash |
| solver | 名称/版本/算法、线程、种子、容差、许可信息仅保留必要非敏感部分 |
| start_time/end_time | ISO8601带时区，建议UTC；本地展示Asia/Shanghai；未启动为null |
| objective | 原始优化目标、单位、objective_constant、成本口径说明；不直接命名welfare或年度成本 |
| solver_status | 原始status/termination/exit code，保留日志；不存在objective也可记录失败 |
| output_hash | 结果路径/字节数/SHA256数组，附日志和配置hash；原子完成标志 |

扩展：run_kind（tutorial/audit/production）、countries、sector_boundary、planning_horizon/foresight、snapshot范围与三种权重、cluster/busmap hash、carbon_boundary与预算、commodity_boundary、data_confirmation IDs、命令argv/工作目录、workflow/资源版本、父期网络hash、成本统计方法版本、验证状态。

清单hash建议采用确定序列：每个输入字节哈希SHA256；相对路径POSIX化并排序，序列化UTF-8、固定键序/分隔/换行，再对清单文件计算SHA256。不得以mtime或文件名代替内容哈希。大文件hash可流式计算，复用已验证且内容未改的归档；本轮未哈希的文件必须明确null及原因，不能假装全量完成。

## 环境与旧产物归档

复用已跑通环境，不自动升级。先前记录Python3.11.13、PyPSA0.30.3、Snakemake7.32.4、HiGHS1.11.0、Linopy0.5.5等，只是已有环境证据，不等于所有依赖或全年规模已验收。本轮只读导入出现PROJ路径警告，应在正式地理处理前核定环境激活/资源路径，不为消警告安装最新版。

保存既有教程NetCDF、求解日志、初次失败/恢复收据、完整环境explicit文件及hash，分清执行时commit与归档commit。原运行器使用mtime恢复的例外只能用于旧重试，不继承为研究正式规则。

## 实验验收分层

- 工程：命令退出、solver状态、文件可读、manifest与日志绑定，失败不伪装成功。
- 物理/数据：逐国逐部门Load守恒、原始空值、装机与容量映射、所有多端Link端点、能量平衡/储能动态、可扩张上下界、跨国连接清单、碳/有限资源预算。
- 科学可比性：相同服务需求、国家内网络/聚类、外部商品规则、规划路径、成本/排放口径；比较双方使用同一输入确认版本。
- 论文复现（独立目标）：确切论文版本+作者代码/数据+指标算法+参考输出；教程PASS不覆盖这一层。

本轮交付验证仅检查证据提取、CSV完整性、状态/空确认值、已复制文件hash和报告一致性，不重新求解或执行修复脚本。
