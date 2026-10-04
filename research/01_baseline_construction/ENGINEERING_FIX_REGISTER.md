# 工程修复评审登记

| ID | Evidence → failure mechanism | 最小动作 | 修改前 / 修改后 | 状态 |
|---|---|---|---|---|
| ENG-IND-01 | 全球GDP NC有ASEAN值，缓存TIFF却为非洲范围；load_GDP直接复用缓存；分配函数未在国家内归一化 | 按源NC哈希/年份/尺寸/CRS验证缓存；从现有NC重建EPSG4326 TIFF；国家/行业内归一化；非法权重拒绝；缺国家总量拒绝隐式0 | 国家守恒/顺序测试失败，NaN/负数/无穷/零权重未拒绝 → 全部通过；真实10国572个已有工业单元格守恒 | 独立提交`a7a8f06b43f0dcce0dbd7005b989d8f73d142b81`；BASE_YEAR_ALLOCATION_PASS；非完整未来工业模型PASS |
| ENG-CO2-01 | 当前co2.budget.co2base_value未被消费，默认base_value=limit使2050读成7.75Mt | 仅把ASEAN键改为base_value，保留1e9与年份系数 | 错轨迹77.5→7.75Mt → 1000→100Mt；旧/新配置、8760/144h缩放测试通过 | 独立提交`753ac81c23f8b9a1ca8ceed531d0630b56f6953d`；CONFIG_EQUIVALENCE_PASS，不代表SC排放范围等价 |
| ENG-GRID-01 | 0.1.1变更清单明确删bus766，仍保留变压器；765负荷及机组在simplify时消失 | 已追到版本和GIS；暂不改端点、不补bus、不删变压器 | 旧教程mean load损失80.84135264MW、generator损失1MW；尚无合法的after网络 | DIAGNOSED / FIX_NOT_APPLIED |
| ENG-CO2-SCOPE | 共享atmosphere store承接电与非电燃烧 | 提出专门power ledger或定制功率排放约束；共享H2/CHP/CC归属先确定 | 微型测试0.4t→加入非电热后0.65t | SCOPE_EXPANSION_VERIFIED；科学归属未决定、未改政策 |

代码补丁和哈希在 [FIX_COMMITS.json](FIX_COMMITS.json) 与patches/。分支源自同一个官方SHA，相互未合并；一项工程修复一个逻辑commit。所有母模型分支仍干净。测试入口位于各fix分支tests/，返回码见 [FIX_BRANCH_TESTS.json](FIX_BRANCH_TESTS.json)。

## 拓扑的新增闭合与剩余问题

[`138ea07b21c55727c937831c396e80286b5ef586`](https://github.com/pypsa-meets-earth/pypsa-asean/commit/138ea07b21c55727c937831c396e80286b5ef586)引入0.1.1；其`modification_list.txt`在Thailand段明确列出删除766和772。0.1原始bus766属于TH、station524、230kV、(99.1181,10.5022)，765是115kV、(99.1171,10.5012)。变压器两端GIS与之相符。**恢复旧端点不是缺坐标问题，而是会撤销上游明确记录的删除决定。** 需要作者说明删除后的替代连接意图或完整可追溯修正网络；有此前提才能决定恢复/重映射。

数据和网络链见 [TOPOLOGY_TRACE.json](TOPOLOGY_TRACE.json)。修复评审门槛：TH与ASEAN逐snapshot负荷守恒、发电容量按carrier守恒、Line/Link/Transformer端点存在性、孤立分量及765对应区域连通性；不能只消除警告。现阶段不声称上述after检查通过。
