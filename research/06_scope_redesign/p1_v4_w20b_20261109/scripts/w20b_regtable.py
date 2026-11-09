"""V4 W20b: markdown rows of the registration tables (CORE_CHECK_V4_56_BUNKER.md section 1) from evidence/W20B_XS_PRE.json and
evidence/STATIC_CHECKS_W20B.json (generated, not typed). No solver.

    python w20b_regtable.py --xs <W20B_XS_PRE.json> --static <STATIC_CHECKS_W20B.json>
"""
import argparse
import json
from pathlib import Path


def bn(v):
    return f"{v / 1e9:.4f}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--xs", type=Path, required=True); ap.add_argument("--static", type=Path, required=True)
    a = ap.parse_args()
    X = json.loads(a.xs.read_text()); S = json.loads(a.static.read_text())
    print("| # | 运行 | 网络 | 燃料舱 | 成员 | 数 | x(S) 对偶 α 0.5 | 其中燃料舱 Σx_{B,i} | α 区间 | x(S) 市场 | 阈值估计 ≈ 1 % × x | D8 加回 M | 合并 Owen 受益 B^m(S) | W20 余量（同国家、无燃料舱） |")
    print("|---:|---|---|---|---|---:|---:|---:|---|---:|---:|---:|---:|---:|")
    for k, (name, r) in enumerate(X["runs"].items(), 1):
        w = f"{float(r['w20_margin_eur']) / 1e9:+.4f}" if r.get("w20_margin_eur") is not None else "—"
        print(f"| {k} | {name} | `{r['network']}` | {'按港口' if r['include_bunker'] == 'ports' else '不含'} | {r['members']} | {r['n_members']} | {bn(r['x_dual_eur'])} | "
              f"{bn(r['x_bunker_part_eur'])} | [{bn(r['x_dual_alpha_min_eur'])}, {bn(r['x_dual_alpha_max_eur'])}] | {bn(r['x_market_eur'])} | "
              f"{max(0.01 * r['x_dual_eur'], 1e7) / 1e9:.3f} | {r['d8_addback_eur'] / 1e6:.3f} | {bn(r['owen_benefit_merged_eur'])} | {w} |")
    print()
    print("| 运行 | 母线 | 线路 | 链路 | 发电机 | Store | 负荷 | 燃料舱负荷 | 计量链路（账户端口） | 燃料舱能量 TWh | 保留存量跨境 | 经非成员过境保留 | 零松弛门 | 燃料舱检查 | 网络 SHA256（前 16 位） |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
    for name, r in X["runs"].items():
        s = S["networks"][name]; c = s["components"]; bk = s["bunker"]
        print(f"| {name} | {c['Bus']} | {c['Line']} | {c['Link']} | {c['Generator']} | {c['Store']} | {c['Load']} | {r['bunker_loads_kept']} | "
              f"{r['bunker_metering_links_kept']} | {r['bunker_energy_twh']:.2f} | {r['retained_stock']} | {r['transit_via_non_member']} | "
              f"{'通过' if s['zero_slack']['passed'] else '不通过'} | {'通过' if bk['passed'] else '不通过'} | `{r['network_sha256'][:16]}` |")
    print()
    print("| 去一国 i | x_i 对偶 | x_{B,i} 对偶 | x_i^m = x_i + x_{B,i} | b_i^m（合并受益，严格口径） |")
    print("|---|---:|---:|---:|---:|")
    for name, r in X["runs"].items():
        if r.get("loo_country"):
            print(f"| {r['loo_country']} | {bn(r['x_i_eur'])} | {bn(r['x_B_i_eur'])} | {bn(r['x_i_merged_eur'])} | {float(r['b_i_merged_eur']) / 1e9:+.4f} |")


if __name__ == "__main__":
    main()
