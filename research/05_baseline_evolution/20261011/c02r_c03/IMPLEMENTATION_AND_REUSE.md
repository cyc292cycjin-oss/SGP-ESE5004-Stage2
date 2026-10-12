# C02R→C03实现与复用边界

此目录属于新合并授权，不覆盖历史C02/C02R/Gate6。父提交291fcd057e14a73eb093a986348846a74f8e40eb。运行开始后的生产Release禁止修改。

- 两类检查器补丁只作用于约束语义及三类已核+Inf零行。有限非零值、方向、输入及序列化SHA保持严格核验。
- 复用已封存365日NetCDF，源SHA b2df7dc771d4759668988f7a0abd7ccfafacd976dff644f7acafd20aee50b9f2；不再次聚合Load/Q。
- daily_bridge按原CSR块顺序建立全局行序，稀疏CSR→CSC→CSR逆置验证全部条目；D/R和实际标签独立保存，V3_scaled和重新生成offset送入原生模型。科学成本向量另存。
- 原生载入/逐值回读直接复用已核adapter.CBackend/load_candidate/exact_readback。原参数回执冻结；环境参数只记录非秘密数值，许可仅安全路径绑定。唯一optimize调用位于新c03_native.py。
- daily_acceptance复用既有V4代数、固定账户和物理方程；实际LABELS决定日向量回映射，不使用旧2920标签重建。原始向量先持久保存，物理/KKT和NetCDF检查后置。
- supervisor/guard复用已核production_control，资源读取替换为122已验证cgroup-v1/祖先限制实现；阶段持续和累积绝对截止共同生效。构建worker保留no-solve防护，原生worker独立进程。
- 构建1800、桥接900、原生3600、退出120+30、RAW300、V4 1200、封存同步1200秒，总9150；不滚动延长。启动磁盘20GiB、输出储备10GiB、磁盘底线8GiB、RSS75GiB、cgroup余量12GiB。
- 45项局部合成/格式测试PASS，不等于真实日LP、科学可行性或最优性通过。早期实际GRBstartenv成功，已释放；不创建测试模型、不测试optimize。

REUSE_PROVENANCE.json列出逐源SHA；C03_RELEASE_MANIFEST.json枚举实际66项部署成员。部署包复用此前C02中已核Scheme A/C01R/微扰台账等，Git本目录不重复收入大型源证据。来源在父c02/code及c01r、scheme A固定提交中可追溯。
最终运行结论以C03_DAILY_DIAGNOSTIC_RESULT.md及真实回执为准；旧G6-05继续PAUSED_BY_USER。
