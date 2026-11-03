# 证据目录索引（V3 独立审查，第 183 项）

探针脚本在 scripts/，输入网络为 INPUT_NETWORKS_SHA256.txt 所列文件（副本在 /home/jin/v3rev/，不进仓库）；运行方式 PYTHONHASHSEED=0 python -I scripts/probeN.py（路径为本机绝对路径，复现时改为自己的副本位置）。

| 文件 | 内容 | SHA256 |
|---|---|---|
| probe1.json | 五个网络的权重、钩子、存量钉值、EV 边界、两情景逐组件含时序差异 | 8363633d4a24ffc916cc74e69c61d02a3a48a58282b4149d5f927a59629ebc2c |
| probe2.json | 需求按国家×部门、注册表参数、成本表年化复算、燃料价、船运链路、封存与净零元数据 | 2b44ffe99cba3347b501890739b7b7982b0323e9b4062912fb74bf4da5ec3608 |
| probe3a.json | 第一批筛查轻包摘要：回执、C1、闸门、Owen 对偶形式、受益、账本、分析文件 | 9c63820ff83275302c8b2d1a2418ff7b2907efd615f0b276c9fcb2793c864f0c |
| probe3b.json | 第一批 V1/V2 解后网络：装机、发电、弃电、LA 交换、EV 储能行为、液体贸易、目标函数分解 | dbba4d072e5b72a2b24f61b28b42069efd0ceba5fa304b4cc74f70b414fd10d7 |
| probe4.json | 需求对表（国家×载体）、EV 下限时区落位、EV 峰值当地时、拆分组件守恒 | b7c48753b173da9cfac6724f81b71f7b4fbc7fd91de83292d513e899c3aa2825 |
| probe5.json | EV 周型按当地星期、储能与可调机组容量、电力平衡 | 39598e17ec3562dcbd256b1a22b58759e4e0fe4a36c1e90781f9e9d2a8f9d2ee |
| INPUT_NETWORKS_SHA256.txt | 审查所用网络副本的 SHA256 | fc6dde4efce6b31a512fa17b602b22bea7a6c8f3fb70c5024b790d0109986b80 |
| scripts/probe1.py | 探针脚本 | 964ec70e0a1c2a68b43db54c0d2582d4c347292e741f1f330cb6fb33a6853908 |
| scripts/probe2.py | 探针脚本 | 0a2fb893b65d47057ce1f58bf6d00159410c8fd06c86f1b15b1c977e732ff5ba |
| scripts/probe3a.py | 探针脚本 | 5ac8cf6ccebe46e8b920775e5ab19598bef6e35c878b0f6837b7f1e098805016 |
| scripts/probe3b.py | 探针脚本 | 76efacbe06d16f35de877b1668c1d47c8d5cf7805c3bf5e73d9338ec65ea9f6f |
| scripts/probe4.py | 探针脚本 | 14f2940abf512c47bde0d12761adb1698bb5eea56a3123e22d0819015411e23e |
| scripts/probe5.py | 探针脚本 | 3f95e85d9664471bca7a448a14b224cc1eae7de106f8765f2771926d0bc65416 |
