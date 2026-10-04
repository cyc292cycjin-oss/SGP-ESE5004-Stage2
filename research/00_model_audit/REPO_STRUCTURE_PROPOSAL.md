# 仓库组织提案（只提案，不迁移母模型）

## 实际位置与历史

| 位置 | 已核实状态 | 本轮处理 |
|---|---|---|
| WSL `/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean` | 正式模型仓库，sgp-stage2-asean，ce327bfa；输入/输出多为ignored | 只读提取；提取前后git status为空 |
| 原项目镜像 `.../.chatgpt-projects/g-p-6ab.../audit_repo` | ce327bfa detached审计副本，origin指向用户GitHub仓库 | 未改源码/默认配置/历史结果 |
| 当前 `C:/Users/20122/Documents/ChatGPT/ASEAN` | 本地Git初始化目录；本轮开始无提交；已有untracked outputs/和work/ | 新审计包在research/00_model_audit，保留已有文件，不以“清理”为由删除或代为提交 |
| `Desktop/Singapore/技术目录` 等 | 用户本地来源材料 | 只读元数据/相关表页；不改名、覆盖或升级数据 |
| 原项目镜像research/00_model_audit | 切换工作目录前的本轮中间产物 | 原地保留；**最终交付以当前Documents/ChatGPT/ASEAN中的版本为准** |

母模型根目录已有Snakefile、scripts、configs、envs、doc/doc-asean、notebooks；项目修复/结果记录放在reproducibility，项目教程override放在configs/tutorials；运行输入位于data/cutouts/resources/networks，结果/logs多未跟踪。现有24项教程归档修改见历史 `REPO_AUDIT.md`，不重写ce327bfa。

## 推荐目标：项目研究层包住冻结的上游工作流

```text
SGP-ESE5004-Stage2-research/       # 项目研究仓库（未来采用）
  upstream.lock.json             # origin、baseline SHA、patched SHA、license
  upstream/pypsa-asean/           # 固定检出/子模块，选择方式后再实施
  research/
    00_model_audit/              # 本轮8项交付及证据/提取方法
    01_data_audit/               # 逐参数确认、转换对账
    02_sector_coupling/          # 部门边界与守恒验收
    03_baseline/                 # 已确认基准的设计/分析入口
    04_country_runs/
    05_interconnection/
    06_distribution/
  data_registry/
    DATA_LEDGER.csv              # 后续唯一确认台账
    sources.lock.json           # 来源版本、哈希、存放位置、许可
    decisions/                  # 人工确认与理由（append-only）
  configs_project/
    base.yaml                   # 只覆盖已确认项，引用冻结上游配置
    scenarios/                  # 有科学含义的命名
    runtime/                    # 资源与求解器工程配置
  scripts_project/
    audit/                      # 只读提取/验证
    prepare/                    # 透明的切片/输入变换
    run/                        # 日后manifest与求解入口
    analysis/                   # 成本/国家/网络指标
  results_project/<run_id>/     # manifest、有效配置、日志、hash、结果引用
  docs/decisions/
  docs/methods/
  docs/reproduction/
```

这是目标布局，**本轮没有创建空实验目录、移动现有母模型、删除历史资产或加入新子模块**。当前审计包暂自包含；将来若移入data_registry，应以一次明确迁移提交改变引用，不长期保留多个可编辑台账。大型输入和结果放独立归档存储，Git保存清单/许可/哈希，不提交环境目录、缓存和不明备份。

两个实现选项：

1. 推荐独立研究仓库+固定上游检出/子模块：研究层独立，母模型修复在模型fork单独提交；upstream.lock绑定未改基线与补丁SHA。优点是界限清晰；需要维护两套版本身份。
2. 保留当前fork根布局，新增research/data_registry/configs_project/scripts_project/results_project/docs：迁移少；仍需禁止研究脚本混入scripts与默认config。作为短期过渡可行。

不建议把现有仓库整个移动到子目录并一次性重写历史。需先选定架构及权限、归档ignored原始数据/结果，再以可回滚提交执行。`reproducibility/line_country_clustering.py`与`scripts/line_country_clustering.py`双份代码有漂移风险，已有验证记录保留；以后建立唯一实现/引用，不在本轮删除。

## 配置与上游改动边界

顺序应为固定default → ASEAN base → 经确认project override → 纯资源runtime override；记录每个关键键的来源层、迁移后的effective config及hash。绝不手工逐实验改上游默认文件。`co2base_value/base_value`说明仅保存命令行文件名还不够。

必须改源码时：独立提交并标记engineering fix / data correction / model change；说明为何不能config实现、影响的输入和物理约束、前后守恒/数值验证、兼容的PyPSA版本。修复不自动等于科学等价；若修正了作者数据，保留“作者原样”与“修正版”的结果身份。

本轮不push、不force-push、不合并、不重构上游。当前用户目录已有untracked内容，不能为满足clean tree而删除；模型工作树干净与整个桌面研究目录干净应分别报告。
