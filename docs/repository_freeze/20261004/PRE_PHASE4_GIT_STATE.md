# Pre-Phase4 Git state

实际GitHub项目：https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2（private，default branch=main，账户push权限已读确认）。状态记录时间：2026-10-04T10:35:52.912000+00:00。证据：WSL_BEFORE.json、REFS_BEFORE.json、INTEGRITY.json、REPOSITORY.json。Windows交付仓库与WSL模型仓库是两个Git历史，不能把Windows HEAD当成模型SHA。

## 远程、对象完整性与工作树

远程main在操作前/后均为 **a3616a68ee44592af6527ca9024a90f1956646ae**。原远程3个分支、0个tag；本地有26分支、12个上游版本tag。没有推送那些无关版本tag。

```text
local-history	/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean (fetch)
local-history	/home/jin/research/SGP_ESE5004_Stage2/pypsa-asean (push)
origin	https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2.git (fetch)
origin	https://github.com/cyc292cycjin-oss/SGP-ESE5004-Stage2.git (push)
upstream	https://github.com/pypsa-meets-earth/pypsa-asean.git (fetch)
upstream	https://github.com/pypsa-meets-earth/pypsa-asean.git (push)
```

`git fsck --full`退出0，无missing/corrupt对象；4个dangling commit是已有贡献者README/锁环境机器人历史，详见DANGLING_REVIEW.json，无一是本轮14个关键里程碑。它们没有删除，也没有为其制造研究归档ref。此前`--no-reflogs`的12个dangling与本轮4个并不矛盾：可达性根集合不同。

count-objects仍提示worktrees/research_audit/refs下4KiB garbage（准确路径见INTEGRITY.json）。它不等于丢失对象，本轮不清理共享对象库。

| Worktree | Branch | HEAD | Status |
| --- | --- | --- | --- |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/model-source | sgp-stage2-asean | ce327bfae2abe5526d4c1976173f0f8d08366ba5 | 445 D：既有--no-checkout对象池 |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/fix_carbon_config | codex/fix-carbon-config | 753ac81c23f8b9a1ca8ceed531d0630b56f6953d | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/fix_industrial_gdp | codex/fix-industrial-gdp | a7a8f06b43f0dcce0dbd7005b989d8f73d142b81 | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/fix_topology | codex/fix-topology-765-766 | a3616a68ee44592af6527ca9024a90f1956646ae | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/paper_reference | codex/paper-reference-5bacad70 | 5bacad702ccfed17ad19ab510fa710651e966f2c | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/research_audit | codex/github-health-audit | 753ff15b45ddb91c406a823f8252fc7b603f29c4 | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/research_model | codex/research-sc-main | a3616a68ee44592af6527ca9024a90f1956646ae | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase2/upstream_sc_baseline | codex/upstream-sc-baseline-a3616a68ee44 | a3616a68ee44592af6527ca9024a90f1956646ae | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase3a2/fix_e1 | codex/buildings-e1 | 30bafa420e5cd639e696cbdd56de0e7df36c0e47 | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase3a2/fix_e2 | codex/buildings-e2 | 070db2918186829908a02a0b72a7b4426711c653 | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase3a2/fix_e4 | codex/buildings-e4 | 9342893fcf467eadbbc410f59c3dbe817d123aa9 | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase3a4/buildings_accounting_validation | codex/buildings-accounting-validation | 50a73d8f531132c5459174a55cac412d5f684462 | CLEAN |
| /home/jin/research/SGP_ESE5004_Stage2/phase3b2/shipping_allocation_validation | codex/transport-shipping-reviewable-patch | 85a32dc231458fd753445df38d422b78435b8aad | CLEAN |

model-source由既有prepare_model_layers.py以clone --no-checkout创建，445个D为该特殊未检出状态；未恢复/提交它们。其他12个工作树原先清洁。Windows初始分支codex/github-health-audit、HEAD600b9bdcf52cbd8a887df5d81706a8c7f3909edb；原有outputs/和work/未跟踪内容保留。新报告在独立infra提交中保存。

## 全部本地分支与操作前未推送数量

数量是相对origin已有分支全部历史的差集，不是仅与origin/main比较；不同分支的数量可能重叠，不能相加作为唯一提交数。

| Local branch | SHA | Unpushed commits |
| --- | --- | --- |
| codex/buildings-accounting-validation | 50a73d8f531132c5459174a55cac412d5f684462 | 10 |
| codex/buildings-e1 | 30bafa420e5cd639e696cbdd56de0e7df36c0e47 | 3 |
| codex/buildings-e2 | 070db2918186829908a02a0b72a7b4426711c653 | 3 |
| codex/buildings-e4 | 9342893fcf467eadbbc410f59c3dbe817d123aa9 | 3 |
| codex/buildings-heat-alignment | f921caa2f7e667a111131b2598b8ee431607206a | 4 |
| codex/buildings-heat-audit | a4ac700d65578cdb3d52ca716e13e9b3b6f662de | 3 |
| codex/buildings-phase3a3 | 32df5c63c87e25f2ddbb2c04019d8be3ede726f9 | 5 |
| codex/buildings-phase3a4 | b03b2218866f259e1e6223e5a07738e33fe44e4b | 7 |
| codex/buildings-phase3a5 | 89b5d8c2ae66dd130841f6fec16c7049db8db8b5 | 9 |
| codex/buildings-phase3a6 | a5d4d9d1fdd5f39fd44f3745e09c3daae7349a45 | 10 |
| codex/buildings-phase3a7 | ac98b363c20182b6ae9a354cedaef227fcee196a | 11 |
| codex/fix-carbon-config | 753ac81c23f8b9a1ca8ceed531d0630b56f6953d | 1 |
| codex/fix-industrial-gdp | a7a8f06b43f0dcce0dbd7005b989d8f73d142b81 | 1 |
| codex/fix-topology-765-766 | a3616a68ee44592af6527ca9024a90f1956646ae | 0 |
| codex/github-health-audit | 753ff15b45ddb91c406a823f8252fc7b603f29c4 | 15 |
| codex/paper-reference-5bacad70 | 5bacad702ccfed17ad19ab510fa710651e966f2c | 2 |
| codex/phase2-baseline-review | 9424212a21015c02b9c1f87d14d49851b9209bce | 2 |
| codex/remaining-sector-phase3c | d1c2790281b8768228ee369aeb81dd543654af4a | 14 |
| codex/research-sc-main | a3616a68ee44592af6527ca9024a90f1956646ae | 0 |
| codex/transport-phase3b1 | ded939485c10fd6a23d13a45e01b03d64f28a972 | 12 |
| codex/transport-phase3b2 | 9ba4794f6d2ba9b5f16d57c9d12725aeb94413c7 | 13 |
| codex/transport-shipping-allocation | 512c6cc2e53c579976d269486a7e328a0f372017 | 1 |
| codex/transport-shipping-reviewable-patch | 85a32dc231458fd753445df38d422b78435b8aad | 3 |
| codex/transport-shipping-target-guard | cf4b0f816086470dce40ec950e20c045044eec0c | 2 |
| codex/upstream-sc-baseline-a3616a68ee44 | a3616a68ee44592af6527ca9024a90f1956646ae | 0 |
| sgp-stage2-asean | ce327bfae2abe5526d4c1976173f0f8d08366ba5 | 0 |

## 操作前远程分支与本地tags

| Remote-tracking ref | SHA |
| --- | --- |
| refs/remotes/origin/HEAD | a3616a68ee44592af6527ca9024a90f1956646ae |
| refs/remotes/origin/dependabot/github_actions/github-actions-547ce19ed8 | 5568912ad8e838723d2c9c774346f8876418d45a |
| refs/remotes/origin/main | a3616a68ee44592af6527ca9024a90f1956646ae |
| refs/remotes/origin/sgp-stage2-asean | ce327bfae2abe5526d4c1976173f0f8d08366ba5 |

| Existing local tag | Object SHA |
| --- | --- |
| refs/tags/v0.0.1 | f63fdeca6552a20b4e26a02d3f9290ad98389239 |
| refs/tags/v0.0.2 | 6fb23e98290c576877fdbdf87f9f994c6871273e |
| refs/tags/v0.1.0 | 84cb49c58259878063cb1589622c3b46e8b1bff2 |
| refs/tags/v0.2.0 | dbc555564315943e35636216a36a4770ec987417 |
| refs/tags/v0.2.1 | 084e7aa8a14f9e80a0b085baa74502bc8ef54d67 |
| refs/tags/v0.2.2 | de7a72fede254f75da430a03104b3bde107e3080 |
| refs/tags/v0.2.3 | 2482704c0c413a625107f4c68c41e4f9481e0b08 |
| refs/tags/v0.3.0 | 6f8aa806e306f6e987095df14cde7ea6f6873d00 |
| refs/tags/v0.4.0 | 62691b6171dc6cc9ca5cefa9d52079c046c3b1a9 |
| refs/tags/v0.4.1 | 32c050eeec6cb557b9a23aebca0e2a0be5d8bf3e |
| refs/tags/v0.5.0 | a7fcdb38cd047501732333ff9efa795725aba3e5 |
| refs/tags/v0.6.0 | e3fc578d44d4d2f40b462a10ca96b4f19d2a5296 |

对象type、parents、contains与14个里程碑的前后状态均保存于MILESTONES.json/MILESTONES_AFTER.json。没有改模型文件、研究输入、科学结果、main或旧分支的tip。
