# Avion限定历史OCGT寿命决定

本轮直接用户决定`GATE4-20261006-LIMITED-OCGT-SOURCE-UNCERTAINTY#A`，方法`ASSEMBLY_V1_AVION_OCGT_25Y_LIFETIME_PROXY`，仅用于`GPD:WRI1029960`的2016年Avion批次。未追溯性改写旧批准。

来源冻结表技术寿命25年（DEA52OCGT，原候选证据`evidence/source_scope/OCGT_SOURCE_CANDIDATE.json`）本轮被选作这一个历史批次的代理。按commissioning<=2050<retirement，2016+25=2041，因此`NOT_ACTIVE_2050`、RetainedCapacity2050=0。该0来自明确模型边界，不是缺失变零，也不代表现实电厂一定在2041退休。

原100MW installed保持，97MW dependable独立记录。技术为OCGT，原DOE资料证据等级仍是官方缓存提取，原PDF未取得；没有伪造单机组拆分。真实相容退役记录优先，新增身份/年份/容量或改造冲突触发拒绝；未将旧重复身份待核记录删除。其不进入本版2050继承后，原DOE PDF升级仅是档案补强需求，不继续以此阻断数值寿命决定。

`asset_lifetime_overrides.json`按AssetID限制并固定源hash，未将OCGT加入全局历史寿命表。CCGT40年规则、2050新建OCGT候选、0.405/0.41效率、FOM/VOM与投资值均未被本次接受或改写。

生产库存中的这1条记录由UNRESOLVED_RETIREMENT_OR_LIFETIME变为NOT_ACTIVE_2050；未决源记录404→403。原745条实际接入源记录、187400.4MW完全保持，新增/移除实际接入容量均0MW。5组684MW水电和其他GPD/GEM库存问题不变。

测试对象已修正：未批准寿命的拒绝行为绑定冻结`avion_unapproved_lifetime.json`夹具，不再要求生产配置永远待决。实际执行12项来源范围回归和17项新增寿命/区间/元数据检查，共29项通过。包含25年筛选、不得继承CCGT40、未知寿命非零、实际退役优先、其他OCGT/新建候选不受影响、源冲突拒绝、缺热值/版本冲突、按母线名对齐及NetCDF变量保留。

本轮没有重建物理网络。只修改库存合同和电力基础网/诊断网的资格meta，所有静态组件、时变属性、时权按名称对齐精确比较；153组数组及registry/manifest字节保持。资产manifest保留原物理构建代码SHA，原输入hash另存于qualification_refresh.original_build_inputs，当前inputs更新为有效资格/输入hash，不假称由本轮重建。

初次刷新因旧manifest中的Infinity上限序列化失败，已保留失败日志，仅恢复该次已知生成写入后修复兼容保存。旧无穷上限、未知null均保持其原含义；成功回读与保留性核验见`evidence/uncertainty/QUALIFICATION_REFRESH_RECEIPT.json`及`ACTUAL_PRESERVATION.json`。源环境已有PROJ路径诊断仍见日志，本轮未执行坐标重投影，测试实际完成。
