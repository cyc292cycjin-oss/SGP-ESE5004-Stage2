# E4 — Services electricity carrier identity

## Material Passport

- Origin Skill: academic-research-suite / experiment-agent
- Mode: validate; Version: Phase3A3-1; Date: 2026-10-01 Asia/Shanghai
- Verification Status: VERIFIED for carrier/Buildings regressions; full-system electricity accounting PENDING

## 定位与最小修复

**修复前失败 → 修复后通过。** `final_asean_adjustment.py` 的 `carrier_to_keep` 把 `"service electricity"` 改为实际使用的 `"services electricity"`，仅一行替换。

| 入口 | 冻结 U 中的含义 |
|---|---|
| `build_base_energy_totals.py:75,177` | 年度列 `services electricity` |
| `prepare_sector_network.py:3060,3066,3068` | `add_services` 读取同名列，并建立同名 suffix/carrier |
| `prepare_sector_network.py:3468` 附近 | 配电层将含 electricity 的载荷接入 low-voltage；与复数命名一致 |
| `final_asean_adjustment.py:44` | singular allowlist 不匹配，power filter 删除 Services electricity |
| `final_asean_adjustment.py:83,199,244` | `elec_carrier` 供最终电量调整使用，仍缺 Services；属于未实施 E3 |
| `final_asean_adjustment.py:419` | `only_elec_network` 决定是否运行过滤器 |

定位记录：[CODE_SCOPE_TRACE](evidence/CODE_SCOPE_TRACE.json)。相关源码、数据列与最终调整分别检查，没有把修复筛选拼写等同于修复电量校准。Residential 在这里仍为原 AC Load，未强行改名或改变需求值。

## 独立提交与验证

源码提交 `5d761eceeeb0d0519208d760224a41ff50ec1e30`，测试提交 `78b23e7804ca05f2fd1f5ee5ec90f3fa6f8bbf7c`，分支 `codex/buildings-e4`。本轮沿用已有独立源码修复，新增严格逐国回归，未合并 R。

11 国、22 节点，用真实 `add_services` 生成 Services electricity，然后分别测试 `only_elec_network=True` 过滤路径与 False 跳过路径。核对各国 AC/Services Load 身份和加权年度电量。88 条断言，U 失败 22 条，E4 全部通过；最大修复后年度误差 **0 MWh**。

Full-SC 的不筛选路径原本就不执行这个拼写分支，所以 E4 在该路径是精确无改变量；E1 的 Buildings 构网链另验证 R/S direct electricity。**这些检查不覆盖未修复 E3 之后的全系统电量目标，也不证明完整 Full-SC 年度账户闭合。**

证据：[前](evidence/E4_before.json)、[后](evidence/E4_after.json)、[矩阵](BUILDINGS_FIX_TEST_MATRIX.csv)、[源码](patches/E4.patch)、[测试](patches/E4_validation.patch)。建议独立人工合并，但必须保留 E3 门槛。不能通过把 Services 加进校准名单来暗中实施本轮禁止的 E3。
