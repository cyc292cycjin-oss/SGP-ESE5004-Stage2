# GitHub repository health

**REPOSITORY_HEALTHY = YES（Git版本控制与对象完整性）。** Actions整体为PARTIAL，CodeQL外部服务不可用；二者不能混写成Git仓库损坏。

## 初始身份与远程引用

仓库：https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2 。API显示private、owner.type=User、非fork、未archived/disabled；当前账户对仓库有admin/push权限。本轮只读API，没有利用该权限修改服务或可见性。

| 位置/引用 | 审计前身份 |
|---|---|
| GitHub默认分支main | a3616a68ee44592af6527ca9024a90f1956646ae |
| GitHub sgp-stage2-asean | ce327bfae2abe5526d4c1976173f0f8d08366ba5 |
| GitHub dependabot/github_actions/github-actions-547ce19ed8 | 5568912ad8e838723d2c9c774346f8876418d45a |
| Windows本地交付仓库HEAD | f5853f0c666a48782d202919c9e96a61619b8ca1，codex/remaining-sector-phase3c；没有Git remote |
| WSL research_audit HEAD | d1c2790281b8768228ee369aeb81dd543654af4a，codex/remaining-sector-phase3c；工作树干净 |
| WSL原tutorial对象池HEAD | ce327bfae2abe5526d4c1976173f0f8d08366ba5；用途是no-checkout对象库，不是开发工作树 |

远程当前共3个分支、0个tag。WSL origin指向用户仓库，upstream指向pypsa-meets-earth/pypsa-asean，local-history指向既有教程目录。只执行origin fetch，未拉取更新上游模型、未prune、未改变任何工作树HEAD。初始refs及fetch结果在 `evidence/WSL_GIT_BEFORE.json` 和 `REPOSITORY_GIT_AUDIT.json`；本地交付仓库状态在 `NATIVE_GIT_BEFORE.json`。

## 独立Git检查

| 检查 | 结果 / 范围 |
|---|---|
| origin fetch | PASS；成功获取3个远程分支并核对main SHA；不需要重复clone。 |
| Git对象完整性 | `fsck --full --no-reflogs` exit0；未报missing/corrupt对象。 |
| dangling对象 | 12个dangling commit；不是对象损坏，没有prune/删除。 |
| 对象库统计提示 | count-objects提示1个4KiB非对象garbage路径，位于`.git/worktrees/research_audit/refs`；fsck仍通过。本轮只记录，不自动清理worktree元数据。 |
| 默认分支/引用 | main存在；API、ls-remote和fetch后的origin/main一致。 |
| unresolved merge | research_audit无unmerged index；有效研究工作树均无冲突状态。 |
| 有效工作树 | 12个研究/验证/候选工作树status为空；固定P/U/V/R与候选SHAs保持原值。 |
| no-checkout对象池 | model-source显示445项D；历史prepare_model_layers.py明确使用clone --no-checkout创建。不得把该对象池误作可运行checkout或自动commit这些D；本轮未造成删除。 |
| Submodule | 默认HEAD无160000 gitlink、无需初始化子模块。 |
| Git LFS | 未发现LFS pointer；现有gitattributes未配置LFS；不是缺失LFS对象导致失败。 |
| Workflow YAML | 9份文件全部解析通过，on/jobs有效；不等于9个workflow都PASS。 |

Windows交付仓库原有未跟踪outputs/、work/已保留，本轮只新增本审计目录；不能声称整个本机目录完全无未跟踪文件。科学层已有跟踪文件未改。

## 跟踪文件、大小与ignore

默认main有424个跟踪文件，总blob长度53,364,714 bytes（约50.9MiB；不是克隆下载体积）。GitHub API size为43,383KiB。共享本地对象库pack约43.15MiB、loose约13.41MiB，含历史和本地研究提交，不等于单一main大小。

| 较大跟踪文件 | Bytes | 判断 |
|---|---:|---|
| data/osm-plus-prebuilt/0.1/all_lines_build_network.csv | 14,585,331 | 已有预构建网架输入，不自动删除。 |
| data/osm-plus-prebuilt/0.1.1/all_lines_build_network.csv | 14,547,223 | 同上，版本并存需按provenance保留。 |
| data/osm-prebuilt/0.1/all_lines_build_network.csv | 14,486,768 | 同上。 |
| pixi.lock | 1,280,901 | 依赖锁文件，非虚拟环境。 |
| doc-asean/docs/Images/elec-ASEAN.png | 1,127,987 | 既有文档图。 |
| doc-asean/docs/Images/renewable-pot.png | 1,048,618 | 既有文档图。 |

未发现main跟踪zip/pdf/netcdf文件、venv/.venv/site-packages/node_modules/__pycache__或大型results/research归档树。存在预构建CSV、原始XLSX、notebook和锁文件，均记录清单，不将其自动判为垃圾。没有发现足以解释CodeQL失败的仓库体积/生成文件问题。

`.gitignore`广泛忽略csv/xlsx/nc/zip及data/resources/results等，含特定来源文件例外；ignore不会移除已经跟踪的历史输入。它未明确覆盖所有未来可能的.venv/node_modules位置，但当前没有误提交实例，故不为此次CodeQL添加无关修复。`.gitattributes`为`* text=auto`和notebook linguist-vendored；研究证据逐字节保真应沿既有局部属性规则处理，本轮未修改科学层属性或输入。

## GitHub托管覆盖缺口（与CodeQL根因分开）

远程三分支并未包含当前research_audit、Buildings验证、工业/碳/航运候选或Paper P的HEAD祖先链。本地对象库和交付包仍有这些历史，**不能把“已本地提交/同步WSL”说成“已推送GitHub完整备份”**。

U和教程归档已在远程；其余重要研究引用的远程托管应另作明确清单与授权，不在本次CodeQL工作中夹带push或merge科学分支。该覆盖问题不证明已有科学结果损坏，但影响导师只凭此GitHub仓库复现全部阶段的能力。

证据：`REPOSITORY_GIT_AUDIT.json`逐工作树`remote_branches_containing_head`；远程tags列表为空。检查只涵盖目标仓库公开给当前账户的分支/tag，不对其他备份位置作断言。
