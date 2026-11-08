# W14 第 3 节：打包与本机演练

- **标记：** VERIFIED（回执、记录文件）、EXACT、INFERENCE、PROPOSED。逐条记录在 `logs/`（`pkg_*.txt`、`dry_bash*.txt`、`smoke_drill.txt`、`rebuild_and_dry*.txt`），脚本 `hpc_v4/make_hpc_package_v4.sh`、`scripts/w14_pkg.sh`、`scripts/w14_dry.sh`、`scripts/w14_smoke_drill.sh`。
- **演练副本不在 work/ 下、不得上传：** 每次演练都把交付包整个打成 tar、解到 `/home/jin/v4w14/<dry|smoke>_<时间>/pkg`（全新目录，从不复用），先 `sha256sum -c SHA256SUMS` 再做任何事。

（结果见下文各节。）
