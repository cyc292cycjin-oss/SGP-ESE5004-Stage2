# 干跑第一版（部署包 `be1ce466`）的发现：分国 WACC 变体的 SHA256 随目录变化

- **现象（VERIFIED，`BUILD_ONLY_STATUS.txt`）：** `run_batch3.sh BUILD_ONLY=1` 第 0 阶段在解包目录 `/home/jin/m10p_dry/pkg` 中第三遍生成变体：R5–R9 的 SHA256 与 `EXPECTED_VARIANTS.json`（打包时两遍生成）相同；R10 生成 `f2772bff…`，期望 `3ac0493c…` → `STOP_SAFE:VARIANT_SHA256_R10`，未启动任何构建或求解（按事先登记的安全停止规则）。
- **原因（VERIFIED，`scripts/m10p_diag4.py`）：** 两个 R10 变体网络的全部组件数据相同；元数据只有一处不同——`research_variant.ledgers.finance.costs_table.path`：
  - 打包时：`/mnt/d/ResearchWorkspaces/ASEAN/work/p1_m10p_20261022/cloud_package_dist/networks/integrated_costs_active_research.csv`
  - 干跑时：`/home/jin/m10p_dry/pkg/networks/integrated_costs_active_research.csv`
  
  `scripts_project/m08a_variants.py` 把 `--costs` 成本表的绝对路径写入网络元数据；只有分国 WACC 变体（R10、R11）使用 `--costs`，其余 5 个变体不受影响。云端目录必然不同，不修正则 R10 在云端第 0 阶段即安全停止。
- **修正（提交见进度文件）：** 元数据只记录成本表文件名与 SHA256（`dict(file=..., sha256=...)`）；新增测试 `test_m08a_a7.py::test_wacc_variant_bytes_independent_of_the_folder`（同一 WACC 变体在两个不同目录生成，字节相同；修正前失败、修正后通过）。只改元数据的记录方式，不涉及模型数据。
- **处理：** 第一版部署包改名保留为 `cloud_package_dist_v1_be1ce466/`（作废，不上传），第一版干跑目录改名为 `/home/jin/m10p_dry_v1_be1ce466/`；在修正后的提交上重建部署包并重跑干跑。
