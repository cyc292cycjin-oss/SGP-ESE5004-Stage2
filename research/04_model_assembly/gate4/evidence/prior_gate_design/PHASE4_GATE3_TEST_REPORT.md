# Gate3 测试与证据边界

| Suite | 结果 | 证据 |
|---|---|---|
| 新载体/碳/真实 PyPSA fragment + 未求解 Linopy 系数 | 60/60 PASS | GATE3_TEST_RESULTS.json、gate3_tests.log |
| Buildings strict E1/E2/E4 | 1062/1062 assertions PASS | BUILDINGS_REGRESSION.json |
| Shipping | 17/17 tests PASS | SHIPPING_REGRESSION.json |
| Gate2 demand | 70/70 tests PASS | gate2_regression_70.log |
| Gate1 static | 20/20 tests PASS | gate1_static_regression.log |
| Manifest schema | 7/7 tests PASS | gate1_manifest_regression.log |
| Gate2 数据/脚本字节守卫 | 21/21 PASS | GATE2_HASH_GUARD.json |

Buildings 1062 是逐行 assertions，其他数量是 unittest 方法，不混称独立实验。所有测试为静态/合成 fixture，无求解、无正式需求物化。最终实现 SHA `140294807bffe5cc172d5226ee0af3d4f548d180`。首次59方法通过后，对价格元数据窄修复重跑新增到60的受影响套件与配置门禁；上游及 Gate2 输入未变，旧 suite 结果继续有效。

11 国模板：111 Bus、110 候选组件，全部110候选未接受、无真实 Load；方向图无跨国载体可达路径。可达图包含 PENDING 技术方向，非空图，且变异测试能检出错误跨国端口。它是多输入转换的潜在路径上界，不是可行调度证明。

有效参考证据复用：历史6306条组件审计、280条共享/路径风险记录；其中110 CO2方向路径、110 biomass共资源访问、60 lignite共资源访问。没有篡改历史网络以制造“已修好”的结论。电力记录分开标记 historical tutorial 与 current pinned raw topology；最终 clustered 网络尚无。

PROJ 数据目录提示及旧配置弃用警告仍出现在现有环境日志；本轮所有相关测试完成并通过，未调整环境，也未据此宣称 GIS/完整 workflow 就绪。

## 可复核命令（从模型根目录、既有 pypsa-earth 环境）
```text
python scripts_project/run_gate3_validation.py --output /tmp/gate3-review
python scripts_project/check_research_carriers.py --output /tmp/gate3-review/config.json
python tests/research/test_demand_accounting.py
python tests/research/test_phase4_static.py
python tests/research/test_run_manifest_schema.py
python tests/transport/test_shipping_allocation.py . /tmp/gate3-review/shipping.json
python tests/research/approved_buildings_regressions.py --repo . --fix combined --output /tmp/gate3-review/buildings.json
```

`audit_reference.py --evidence <evidence-dir>` 可从冻结 JSON 重做方向图审计；当前未重跑。`complete_source_audit.py` 还要求原历史 NetCDF/原 pinned raw topology，并先核验 NetCDF SHA。工具副本用于追溯；不是可直接组装 Full-SC 的入口。
