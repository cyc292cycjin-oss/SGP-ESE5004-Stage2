# Shipping compatibility integration

**成功整合；scientific demand 未改变。** Gate1 未整合的原因是换行冲突，不是人审否决。

原始 source lineage：

1. allocation：`512c6cc2e53c579976d269486a7e328a0f372017`
2. target guard：`cf4b0f816086470dce40ec950e20c045044eec0c`
3. validation/byte fidelity：`85a32dc231458fd753445df38d422b78435b8aad`

从 Gate2 起点派生本地 `fix/research-shipping-compat`。兼容实现 commit `ee01f65a78dede9447a950676d16e072e98c8a7a`，通过 ff-only 整合研究分支；不是原 commit 的 cherry-pick。

只替换 `scripts/prepare_sector_network.py::add_shipping` 的功能体并增加 helper import；增加 `_shipping_allocation.py` 和原 17 项 shipping 测试。该源码 diff 为 12 行新增、25 行删除；没有整文件换行重写。函数 AST 与原最终批准版本一致，函数之后全部字节不变，之前仅新增 import。Buildings E1/E2 保留。

CRLF：4043→4030；两侧 lone LF 均为 0。

- 修改前 SHA256 `62d9d453812d9a2c8596d87eeaa6a16631cea4d933d704c62198ac3ea4f48db8`
- 修改后 SHA256 `05a000c45f5b18a3a91ad5c0bf900274ba2bf560d84517545a7975fac8e8155e`

Shipping **17/17 PASS**，Buildings combined strict **1062/1062 PASS**。覆盖 national annual conservation、missing≠zero、非法空间权重报错、无 NaN 静默补零。后续 Gate2 需求实现没有再次修改这些 source 文件。

证据：`SHIPPING_COMPATIBILITY_PROVENANCE.json`、`evidence/SHIPPING_BYTE_PROOF.json`、`shipping_17.json`、`buildings_1062.json`及相应日志。
