# 765/766：证据支持删除过时引用

**Referential integrity PASS；仅删除 `transf_524_0` 一行。** bus765、其余2520个现有节点和所有其他数据行未改，无新造bus。

上游引入提交 `138ea07b21c55727c937831c396e80286b5ef586` 的 `data/osm-plus-prebuilt/0.1.1/modification_list.txt` 明确在Thailand条目删除766/772。0.1中766为station524的230kV层，只接765→766变压器，没有Line、converter或clean-generator引用；0.1.1及作者paper run树 `5bacad70…` 都仍遗留这条变压器。恢复766会恢复作者明确删除的层级，没有独立证据支持，所以选最小删除遗留引用。

修复前测试记录引用缺失766，失败；修复后9项测试通过。Transformer 651→650，Line3441、Link17、Bus2520、clean Generators1982不变；对全部保留Bus构造的有效端点连通分组前后完全一致。765本来没有有效线路邻接，其孤立状态没有被本轮新增或掩盖；未在此步骤删除其未来应保留的国家能源。

输入 transformer SHA256：

- before `080169b7e0fbc61b44e2b12873e243f9ea8baefeaefbd17d27ef45fe3f5d7428`
- after `b4b319a413dd6ab5327dae00e2602410c9fe1b79d3c8d72091d209b408b74631`

源码与测试先写入，测试失败后才编辑数据。`TOPOLOGY_FIX_PROOF.json` 包含全部前后端点/连通分组，`TOPOLOGY_FIX.diff` 为精确一行删除。修复隔离于 commit `d13d5976da7e8486215efb987718f9b3f9c82215`，未混入需求、碳或配置修改。参考树/原tutorial文件不改。

首次验证器把三条跨国Transformer标签与无效国家混在一起；已纠正为归属复核项，而不是改源数据让测试通过。`transf_407_0`、`transf_443_0`、`transf_501_0` 具有合法但不同的两端country；保留显式复核标记。PASS只覆盖引用/合法元数据，不能据此宣称这些源标签已验证为真实跨境换电设施，也不能直接放进Gate5最终控制集。

原始电力边现在4108条，按现有标签4046 domestic / 62 cross-border / 0 unknown；这是未聚类原始层。尚无实际Research网络，最终控制集仍未就绪。
