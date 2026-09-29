# 我的 PyPSA-ASEAN 复现记录

## 当前阶段

2026-09-29：已完成教程 2030、2040、2050 年计算，三个年份均报告 optimal。当前是流程验证完成，不是论文结果复现完成。

教程范围：50 个地理节点、2013 年中的 6 天、3 小时时间分辨率。优化成功不代表数据和建模假设已通过科学验收。

## 分工与工作约定

- 研究者本人：在自己的 WSL Ubuntu 中执行模型命令，观察结果，审阅并提交代码，决定实验范围。
- AI 助手：协助读取日志、定位问题、准备修复和运行脚本、执行已说明的检查，并解释依据与限制。
- 本轮教程的计算由研究者本人启动；助手执行的 dry-run 和结果文件检查不属于重新求解实验。
- 后续每次实验先写清目的、输入、改动和验收标准，再运行；完成后保存日志、配置和结果校验值。
- 修改有记录不等于已经提交 Git，提交 Git 不等于已推送 GitHub。

## 主要文件

| 文件 | 用途 |
|---|---|
| RUN_LOG.md | 本轮工作和运行结果摘要 |
| BASE_BRANCH.txt / UPSTREAM_BASE_COMMIT.txt | 原有上游版本记录 |
| LINE_COUNTRY_FIX.md / LINE_DIRECTION_FIX.md | 输电线路国家属性修复说明 |
| SIMPLEX_RETRY.md | 2040 求解失败及算法切换记录 |
| retry_2040_simplex.sh | 2040 单独重试；已完成，不需再次执行 |
| resume_2050_simplex.sh | 2050 续跑；已完成，不需再次执行 |
| check_tutorial_completion.py | 不重算模型的文件与日志检查 |
| tutorial_completion_audit.json | 三个结果的哈希、求解设置和目标值 |
| simplification_audit_20260929.json | 网络简化中的已知数据差异 |
| tutorial_package_versions.json | 当前已安装 Python 包版本清单，不是完整环境锁文件 |

## 自己检查进度

在 Ubuntu 中执行：

```bash
cd ~/research/SGP_ESE5004_Stage2/pypsa-asean
conda activate pypsa-earth
python reproducibility/check_tutorial_completion.py
git status --short --branch
```

检查脚本验证结果文件可读取、目标值有限、日志含 optimal，并记录 SHA256；不检查全部物理约束或论文数值一致性。

## 保存与上传范围

Git 保存代码、配置、运行脚本、说明、轻量审计记录。原始数据、完整日志和 NetCDF 结果目前被 .gitignore 排除，仍需独立备份；上传 GitHub 不会自动备份这些文件。

本轮关键本地目录：

- results/baseline-aims-3H-tutorial/postnetworks/：三年优化结果。
- logs/reproduction/：运行记录，含重试前日志和环境清单。
- data/ports/：本地 WPI 数据与来源记录。

审计 JSON 含目标函数原始值；不要直接将这些值解读为论文年度系统成本。

## 下一阶段

1. 审阅并提交教程期间的代码与记录，保留这个阶段的 Git 提交号。
2. 对齐论文对应的代码、环境、输入数据和配置。当前代码不等于论文版本。
3. 处理或解释网络简化的数据损失：原始母线 765 经变压器映射至不存在的母线 766，关联负荷和 1 MW 光伏丢失。详见审计文件。
4. 先验证正式 2025 年基准情景，再扩展规划年份和情景。

以上步骤尚未完成。不要因为教程 optimal 就开始对外报告论文已复现。
