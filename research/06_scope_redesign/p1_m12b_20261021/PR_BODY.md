## M12b（第 138、139 项）：上云前的本机检验——电网回路（KVL）是否破坏 Owen 分配的核心性质

叠在 #46（M12）上；含普通 merge M08b 补充 01 头 b018670c（#47）。未连云。

**判定（事先登记的规则）：全部 11 国违反量为 0，都在容差内 → 维持现有建模（跨境线路保留 KVL）。** 第三批照原计划只做 3 次去一国作 365×24h 复核。冒烟口径的数值没有科学含义。

### 内容
- **合并：** 普通 merge b018670c（3cf5a940）。冲突只在台账，双方保留。合并后的配置与模型代码与 ec80668f 相同。
- **第 138 项（1b3a0cf6）：** Owen 对偶形式验收改为 C1 同口径：恒等式 ≤ 0.01 bn，残差影响 ≤ max(1 % 差额, 0.01 bn)。新增 `m12_rhs_audit.py regrade`，补单元测试。重评：S4O-6 不互联 false → true；S4N 试点 true → true；S4M-1 冒烟 false → false。
- **运行（用户 10-21 13:29Z 授权）：** 一体化复用 M08b 补充 01 冒烟；11 个去一国变体（`m08a_variants.py`）在本机串行求解，56×3h、档案 A。10 次 optimal、SG suboptimal（C1 全过）；11 次都是 ACCEPTED_LAYER2。
- **检验：** 11 国 φᵢ（对偶形式）≥ c′(i) = c(N) − c(N − i)，最小余量 BN +0.002 bn；市场形式也全部通过。不可分成本为正（+88.6 bn，11 国部分 +12.6 bn）。穿越国界的回路被拆掉的国家：LA 28、TH 28、VN 14、KH 11、MY 10、ID 9、MM 9；余量与被拆回路数无正相关。
- **备选方案（只评估）：** 62 条跨境交流线改为可控联络线：8–10 个文件、约 120–200 行，四个网络要重建，相对 PyPSA-Eur 属结构性偏离。未实施。
- **测试：** `tests/research` 579 passed、65 skipped、0 failed（排除其他步骤 5 个玩具求解）。

报告：`research/06_scope_redesign/p1_m12b_20261021/M12B_REPORT.md`。完成后停止，等待审阅。

🤖 Generated with [Claude Code](https://claude.com/claude-code)
