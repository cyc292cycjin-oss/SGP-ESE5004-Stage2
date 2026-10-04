# 碳约束版本追踪

**论文的 ASEAN 年度绝对排放路径已恢复到作者运行 SHA、旧配置键、消费函数，并由一个脱碳网络的 2050 年上限直接印证。当前配置键疑点属于后来版本迁移问题。** 本轮没有修改任何政策或配置。

## 历史链

| 时间 / 提交 | 变化 | 证据 |
|---|---|---|
| 2025-08-22，`f6236a385c700d4023225b6a2946f0525ad76f68` | Earth 引入多规划年 co2_budget | `history/carbon_introduction.txt`，PR #1553 |
| 2025-10-08，`ea1799365e98916dcd6dcb3bf830835d792ca487` | ASEAN all-sector electricity-only 调整及区域配置 | `history/carbon_keys.txt`；不是 full-SC 论文证据 |
| 2025-12-23，`5bacad702ccfed17ad19ab510fa710651e966f2c` | 两个作者输出记录的运行 SHA | `official/author_run/` 与 `RESULTS_NETWORK_EVIDENCE.json` |
| 2026-01-21，`99159edb7298b847fea517bf05c3f388493501c9` | 论文情景整理发布 | 旧 co2_budget 键仍可见于 `historical/99159edb/` |
| 2026-06-29，`5ea64e917e283064ff91a4cbb8a023305c9f8a71` | Earth 配置重组：co2_budget.co2base_value → co2.budget.base_value | `_helpers.py` 专门迁移旧顶层键；消费函数同步改名 |
| 2026-07-29，`c1d99d0617e027ebe01fa2dd1ce1f7160eaddd6e` | ASEAN 把 budget 嵌入 co2，但保留 co2base_value 子键 | `history/asean_key_change.txt` 可直接见新增混合键 |
| 当前 `ce327bfa…` | 合并配置同时包含 base_value=limit 与 co2base_value=1e9 | 上轮教程网络实读；baseline 预算关闭 |

历史来源：[作者运行代码](https://github.com/pypsa-meets-earth/pypsa-asean/blob/5bacad702ccfed17ad19ab510fa710651e966f2c/scripts/prepare_sector_network.py#L2973)、[Earth 重组提交](https://github.com/pypsa-meets-earth/pypsa-earth/commit/5ea64e917e283064ff91a4cbb8a023305c9f8a71)、[ASEAN 迁移提交](https://github.com/pypsa-meets-earth/pypsa-asean/commit/c1d99d0617e027ebe01fa2dd1ce1f7160eaddd6e)。本地保存了 diff，避免只依赖浮动网页。

## 作者版本的实际函数

`prepare_sector_network.py:add_co2_budget`（作者 SHA 第 2973 行起）读取 `co2_budget['co2base_value']`。数值为 float 时：

```text
annual_emissions = co2_budget.year[investment_year] × co2base_value
Nyears = sum(snapshot_weightings.objective) / 8760
CO2Limit.constant = annual_emissions × Nyears
```

该函数调用 `prepare_network.py:add_co2limit`，添加 `GlobalConstraint`，carrier_attribute 为 `co2_emissions`，sense 为 `<=`；primary_energy 类型也通过非循环碳 Store 记账。已有 CO2Limit 时由 override_co2opt 决定覆盖。三个 decarbonize 主情景把 enable 设为 true，baseline 为 false。

| 年份 | 配置 factor | 基数 1e9 推出的年度上限（Mt） | 本轮证据层级 |
|---|---:|---:|---|
| 2025 | 1.00 | 1000 | 作者源码 + 两个网络配置，未读取该年 DEC 网络约束 |
| 2030 | 0.82 | 820 | 配置/函数静态推导 |
| 2035 | 0.64 | 640 | 配置/函数静态推导 |
| 2040 | 0.46 | 460 | 配置/函数静态推导 |
| 2045 | 0.28 | 280 | 配置/函数静态推导 |
| 2050 | 0.10 | 100 | DEC-AIMS 网络直接保存 CO2Limit=100,000,000，Nyears=1 |

这是一组 **myopic 各期年度绝对上限**，不是排放强度约束，也不是跨 25 年累计可交易预算。论文称 ASEAN 电力部门的 90% 减排路径；不能无说明地扩展成全部门相同预算。

## 当前混合键为何不能直接沿用

新函数读取 `co2.budget.base_value`，默认 `limit` 对应 `co2.limit=7.75e7`。迁移器只查旧顶层 `co2_budget.co2base_value`，不会处理已经部分改名的 `co2.budget.co2base_value`。因此仅把当前 enable 改为 true，静态上可能得到 77.5→7.75 Mt，而不是 1000→100 Mt。此处是源码与配置推导，不是本轮启动 DEC 实验的结果。

该问题已经从“可能是论文采用不同碳政策”缩小为明确的配置/消费函数兼容缺口。修复应另列 engineering fix，保留旧/新等价性证据，本轮未实施。

## full-SC 与 standalone 的待决边界

需要共同决定“保持当前设定”指 baseline 无显式排放上限，还是沿用论文 decarbonized 路径，以及预算覆盖电力还是所有纳入的部门。这是研究边界选择，不是再下载一份数据可以解决的问题。

若保留区域绝对上限并做 11 个独立国家求解，不能每国复制区域上限。可供下一轮选择的实现方式仍是：同口径基年比例分配且国家限额加总闭合；冻结共同同意的区域份额；或在统一模型内断开能源连接但共享区域碳上限（后者不是 11 个完全独立模型）。各自识别的网络协调与碳额度协调收益不同。本轮不选份额、不设计国家政策。

`co2_sequestration_potential` 的封存限制与 CO2Limit 不是同一约束；共享生物质、碳 Store/封存池也可能跨国耦合。它们不能每个 standalone 复制一份区域资源。碳记账/边界确认、配置兼容性修复和未求解的约束检查，均需先于正式实验。
