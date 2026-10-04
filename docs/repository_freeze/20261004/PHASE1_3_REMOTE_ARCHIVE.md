# Phase1–3 remote archive coverage

**PARTIAL：14个指定/发现的模型与修复里程碑均已远程可达；完整Phase1–3报告链仍仅在本地。** 不能据12个ref核验通过就宣称整个研究史已冻结。

## 已保存远程历史

- tutorial：原`sgp-stage2-asean`和新`reference/tutorial-ce327bfa`。
- paper实际运行、后续publication和U：三个reference tags。
- GDP、carbon、E1/E2/E4、combined buildings、shipping候选：7个原有codex分支；combined buildings另有reference tag。
- 工程验证记录与源码：可从上述分支读取；353dec3c及源修复提交在祖先链中，不依赖reflog。

## 真实研究报告链

`codex/github-health-audit` @ 753ff15b45ddb91c406a823f8252fc7b603f29c4位于U之上的15个提交，含Phase2基线附带的早期model/source audit，到Phase3C与health审计的连续研究历史。各中间阶段分支都是该历史中的具名检查点。没有为整齐命名合成merge。

| Family | Repository path | Files at archive HEAD | Latest touching commit | Remote status |
| --- | --- | --- | --- | --- |
| model_audit | research/00_model_audit | 82 | 9424212a21015c02b9c1f87d14d49851b9209bce | LOCAL ONLY — archive HOLD |
| source_provenance | research/00_source_provenance | 127 | 9424212a21015c02b9c1f87d14d49851b9209bce | LOCAL ONLY — archive HOLD |
| phase2_baseline | research/01_baseline_construction | 65 | 9424212a21015c02b9c1f87d14d49851b9209bce | LOCAL ONLY — archive HOLD |
| buildings_3a1 | research/02_sector_coupling/buildings_heat | 389 | ac98b363c20182b6ae9a354cedaef227fcee196a | LOCAL ONLY — archive HOLD |
| buildings_3a2 | research/02_sector_coupling/buildings_heat_alignment | 47 | f921caa2f7e667a111131b2598b8ee431607206a | LOCAL ONLY — archive HOLD |
| buildings_3a3 | research/02_sector_coupling/buildings_phase3a3 | 65 | 32df5c63c87e25f2ddbb2c04019d8be3ede726f9 | LOCAL ONLY — archive HOLD |
| buildings_3a4 | research/02_sector_coupling/buildings_heat/phase3a4 | 61 | b03b2218866f259e1e6223e5a07738e33fe44e4b | LOCAL ONLY — archive HOLD |
| buildings_3a5 | research/02_sector_coupling/buildings_heat/phase3a5 | 79 | 89b5d8c2ae66dd130841f6fec16c7049db8db8b5 | LOCAL ONLY — archive HOLD |
| buildings_3a6 | research/02_sector_coupling/buildings_heat/phase3a6 | 107 | a5d4d9d1fdd5f39fd44f3745e09c3daae7349a45 | LOCAL ONLY — archive HOLD |
| buildings_3a7 | research/02_sector_coupling/buildings_heat/phase3a7 | 23 | ac98b363c20182b6ae9a354cedaef227fcee196a | LOCAL ONLY — archive HOLD |
| transport_3b1 | research/02_sector_coupling/transport/phase3b1 | 139 | ded939485c10fd6a23d13a45e01b03d64f28a972 | LOCAL ONLY — archive HOLD |
| transport_3b2 | research/02_sector_coupling/transport/phase3b2 | 51 | 9ba4794f6d2ba9b5f16d57c9d12725aeb94413c7 | LOCAL ONLY — archive HOLD |
| phase3c | research/02_sector_coupling/phase3c | 40 | d1c2790281b8768228ee369aeb81dd543654af4a | LOCAL ONLY — archive HOLD |
| github_health | docs/repository_health/20261003 | 95 | 753ff15b45ddb91c406a823f8252fc7b603f29c4 | LOCAL ONLY — archive HOLD |
| data_registries | research/01_baseline_construction/data_registry | 4 | 9424212a21015c02b9c1f87d14d49851b9209bce | LOCAL ONLY — archive HOLD |

15族路径均在归档HEAD真实存在。文件清单与最近修改commit来自git ls-tree/log，见ARCHIVE_FAMILIES.json；实际提交链见ARCHIVE_CHAIN.json。目录统计为递归范围，Buildings根目录包含其后续子阶段，registry也属于Phase2，数量不能相加作为唯一文件总数。没有自动把未提交文件加入归档。

## 为什么完整归档仍未推送

SAFETY_REVIEW.md列出的4份原件存在于归档的祖先历史。所有承载这些报告族的后续本地审计分支也继承它们，单独推Phase3C等并不能规避。远程当前没有RESEARCH_ARCHIVE类ref。用户要求有风险文件就停止该ref，因此不删除历史、重写commit或偷偷过滤后推送。

## 重要本地交付包

| Local file | Bytes | SHA256 |
| --- | --- | --- |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\github_repository_codeql_health_audit_20261003.zip | 475511 | e5901fc9cac8a3b725e247f103a998c084a4356272ad0e3e08a9d14e295bef7c |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\model_audit_20260930.zip | 5024585 | f9eed077fa6f344d207a8d34dc013f7601943331d78d0eb12a48b3f6ea736786 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase2_baseline_review_20261001.zip | 7739223 | c560e1dcb6e45380e49ed4c35cc0cd91e5093cdda0be13b593dc866528b77a01 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a1_buildings_heat_audit_20261001.zip | 468528 | c5b62749b87e01dd2c45d59d68d952ee400cbad5047cf38c8597a23ea6090768 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a2_buildings_heat_alignment_20261001.zip | 12098806 | 20b107abdeea2f2c21b266d6643662f87f8273bf460e2905461d973d28f313b9 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a3_buildings_heat_fixes_data_recovery_20261001.zip | 23362583 | 7f638b804787cce017d84d932d050c18608cdeae9d083fc97c9e8bf46ab5dc6a |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a4_buildings_accounting_closure_20261001.zip | 23609125 | 6ec8462b5862d1252cfe2679b3b681c0f09194f8b5be2beb4a610c8a4cc6be33 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a4_buildings_validation.bundle | 77183 | 653e8c19f8e523dd6713c8be64db9b3da7180f563058345024d236ff01d0a77c |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a5_buildings_e3_evidence_closure_20261002.zip | 51083108 | bd5292a19e4e451edae9a0d8b20e48697203ae710fceb3c825c8ecb93c2b4a37 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a6_electricity_boundary_malaysia_e3_20261002.zip | 66282626 | 85f6a344e84c12a5cf11dd3665b1849a86151feb2952908ef086364e00233c21 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3a7_buildings_boundary_closeout_20261002.zip | 66423893 | cd2b782c2947d5eb1048d161f027f069c25cac8b311f4b629c903300c00bbd28 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3b1_transport_boundary_source_audit_20261002.zip | 1147423 | 99a09f471a47f1fbc9323782dd41b2fa783ccf9d34527325414b707f7607e8de |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3b2_transport_minimum_baseline_closeout_20261003.zip | 1227504 | b6f53d2bff7b05f1b131835ecd2ef0c7f56f222270198131b9729d1c182aa636 |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\phase3c_remaining_sector_carrier_freeze_20261003.zip | 1296185 | 1aecc39e691e08ef3ea05c6554b48c8db8695fc4bd1c707c5e8bb8167f72da3c |
| C:\Users\20122\Documents\ChatGPT\ASEAN\outputs\source_provenance_20260930.zip | 2501614 | 14a54ece589f09b9e69ac2b1bc06ba69fbac3a1a5ac785f06675ceaa9c435aa7 |

这些ZIP/bundle属于本地交付封装，未上传Git；不等于包内每份报告都缺Git历史。原始大文件、作者results-asean-paper-v1.zip、网络/天气/环境缓存仍按既有manifest/URL/hash引用，不为了远程完整性上传数据字节。未对整个work/递归爬取或复制。当前包的本地性与报告历史的待备份状态分开报告。
