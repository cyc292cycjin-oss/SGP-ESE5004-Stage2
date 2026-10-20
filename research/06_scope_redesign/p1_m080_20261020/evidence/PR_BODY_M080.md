## M08-0（第 130 项）：注册表补登与一致性修正（只改注册表）

叠在 #43（S4R）上。只改注册表与 `work/` 下清单 / 方案副本：**未求解、未连云、未调用 Gurobi，未改配置、构建 / 求解脚本、网络与既有结果**；构建读取的注册表数值无一改变（前后逐行对比，`evidence/M080_REGISTRY_DIFF.*`）。

### 结果
- 注册表 1,962 → 2,052 行（新增 90、修改 32、删除 0；SHA256 `46e234d7` → `6950a15d`），按"筛查运行实际使用的值"登记（S4O 云包 365×24h 未求解网络，构建 `126110ff`）。
- 补登：风光（含屋顶光伏）分国候选上限 55 行、土地类别 / 密度 / Copernicus LC100 / GEBCO / EEZ 文件 SHA256、构建实际读取的 calibrated_modern 廓线文件、屋顶光伏方法、Astar 形状来源（GEGIS `Asia.nc`，VERIFIED）、地热新建投资 3,596.6 EUR2020/kW 与 FOM / VOM、决定 72 下 LNG 分国上限（VN 278.67、ID 422.33、KH 14.67、PH 510.00 TWh/a 等）。
- 海上风：筛查网络用 NREL 2020ATB 5.5 MW + 尾流 0.8855（VERIFIED）——注册表正确，S4R 的"NREL 5 MW、无尾流"有误；M08-7 只剩海上面积规则。
- v0.13.2：新建组件全部 v0.15.0；电力底座存量机组的成本与效率仍来自作者 v0.13.2 表（存量固定运维 108.1 亿 EUR/a，存量 CCGT 效率 0.57 对新建 0.60）→ 统一性问题，交 M08。
- 状态 / 等级：natura → REGISTERED；v0.13.2 成本层 → 历史；KH / TL 封存 A → C；另 12 行过时状态改正；DATA_PENDING 51 → 47；未新增状态值。
- S4R 新版本 `REGISTRY_ROWS_PROPOSED_v2.csv`、`USER_DOWNLOAD_LIST_v2.md`；数据清单 v2 与附件 B 精简版（`research/06_scope_redesign/p1_meet_20261020/`）。

### 注册表工具
- `scripts_project/m080_data.py` → `fragments/m080.csv`（新行）+ `fragments/m080_corrections.csv`（整行替换，原片段不动）；`d1_registry.py` 增加修正层。
- `fragments/s4c_0.csv` 原被 `*.csv` 忽略、从未提交，干净检出无法重拼注册表 → 强制入库（重拼与原注册表逐字节一致）。

### 测试
- 27 个读注册表的测试文件（排除唯一的玩具网络求解用例）：91 passed / 24 skipped，与基线相同。工作树缺被忽略的 finance 输入，已复制（不提交）。开始时一次 `tests/research` 全量运行约 25 s 后停止，其中玩具网络 HiGHS 用例很可能已执行（不涉及研究网络、Gurobi、云端）。

### 待审阅确认
屋顶光伏等级 B 是否降 C；KH / TL 分项行沿用国家行区间；`d1_registry.py` 修正层；`s4c_0.csv` 入库。详见 `research/06_scope_redesign/p1_m080_20261020/M080_REPORT.md`。（补充 01：屋顶光伏已改 C；`d1_registry.py` 的改动超出原指令范围，用户 10-20 23:38 认可。）

### 补充 01（第 131 项）
同一边界（只改注册表与 `work/` 下清单，未求解、未连云、未调用 Gurobi）。注册表 2,052 → 2,057 行（`6950a15d` → `6d1b2c34`；新增 5、修改 14，数值无改动；构建读取的数值未变）。
- 屋顶光伏 12 行 B → C（0.5×–1.5×），描述记录与 AEO8 / PDP8 / MyRER 的比值（0.33–2.54，只记录）。
- GEGIS 原始文献核实：Mattsson, Verendel, Hedenus, Reichenberg (2021) *Energy Strategy Reviews* 33, 100606，doi:10.1016/j.esr.2020.100606（作者链 PyPSA-Earth 文档 + Crossref 元数据）；LA / TL 借用曲线登记为 C 级例外。
- 登记 4 个已获取文件（USGS 年鉴 2023 水泥 T22、worldsteel 粗钢 2021–2025、UN WPP 2024 TL 人口、Eurostat HICP），REFERENCE_ONLY，"M08 实施时使用"。
- HICP 核实：technology-data v0.15.0 用欧洲经济区（EEA）年均变化率累乘（1.25733），不是 EU27 指数（1.25624）或欧元区（1.2256）。
- 存量机组成本表版本登记为"统一性问题，M08 处理"；`REGISTRY_ROWS_PROPOSED_v2.csv` 增 `existing_fleet_cost_rule`（v0.15.0 对应投运年份）。
- 清单 v3 与新精简版（旧精简版改名 `_v2`）：主算输入 A 10.85 / B 60.33 / C 28.82 %；表 4 第 17、21–23 行改为"已获取，M08 实施"。报告 `M080_REPORT.md` §10。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
