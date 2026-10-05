# 2026-10-06新决定与工程修复

DecisionReference=GATE4-20261006-FIXED-ACCOUNTS-EUR2020。

A：六类已验证固定账采用ASSEMBLY_V1_EXTERNAL_PENDING_FIXED_ACCOUNTS，来源为本轮用户执行指令；仅解除固定未知价格/物理因子对物理构网的阻断。未知数值没有HUMAN_ACCEPTED状态。

B：ASSEMBLY_V1_COMMON_PRICE_YEAR_EUR2020，采用用户指定Eurostat来源EA20年度GDP平减指数。已为EUR2020的值保持。不得二次调整、不改技术学习、无新地区系数。

工程修复：FT已有VOM接入；幂等标准化精确保留原处理值；资格按物理、覆盖、价格、成本报告、排放报告、政策分开；水电计数由表生成70/58/12。不是新增科学假设。

前轮价格年总体判断更正已写入MODEL_FACING_COST_YEAR_CHECK.md，旧结论仍可在Git历史追溯。
