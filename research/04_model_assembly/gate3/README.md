# Phase4 Gate3 交付导航

从 PHASE4_GATE3_READINESS.md 阅读范围与系统前提；随后看 TEST_REPORT、START_IDENTITY、RESUME_INVENTORY 与 DRAFT_DIFF_REVIEW。七张 CSV 均可筛选 Evidence/Status。CSV 是审计数据合同，UTF-8 BOM、引号与 CRLF；空 emission factor 表示未明确，不等于零。

PHASE4_CARRIER_REACHABILITY_AUDIT / HIDDEN_CROSSBORDER_PATHS / CO2_POLICY_COMPONENT_MAP 的对象是历史 tutorial reference。ELECTRICITY_LINK_CLASSIFICATION 用 Evidence 列区分历史与 current raw 两个层级，不能混加形成一个网络。

源数据与设计冻结文档在 evidence/，可追踪到 byte SHA；sources manifest 不包含自身。JSON 原记录不被表格清洗覆盖，Infinity/NaN 等原快照缺失/无限标志保持原样。CSV 仅投影字段；不存在未确认数据的 CONFIRMED 升级。

所有静态工具、源代码、测试、审计与运行记录可由 Git 历史复核。交付包只包含 Gate3 新文件/配置和审计证据，不代替整个模型仓库。未求解的 fragment 也不是正式结果。最终提交/远程对齐与包内容 SHA 在包根 CLOSEOUT.json / SHA256SUMS.json。
