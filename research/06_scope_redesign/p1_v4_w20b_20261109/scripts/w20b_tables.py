"""V4 W20b section 2 tables (read only, no solver): from CORE_CHECK_V4_56_BUNKER.csv (w20b_compile.py) print the markdown tables of
CORE_CHECK_V4_56_BUNKER.md section 2 and write tables/W20B_DS_DECOMPOSITION.csv.

D_S split (arithmetic on recorded quantities): D_S = x_B(S) - Delta_S = [x_B(S) - P_S] + [P_S - Delta_S], with P_S = bunker payment of S at the
coalition's own nodal prices (solved coalition network, marginal price x load x objective weight). [x_B(S) - P_S] = price-level term (integrated vs
coalition prices on the same bunker loads); [P_S - Delta_S] = intra-coalition rent (marginal valuation above incremental cost; >= 0 by convexity of
the LP value function in the right-hand side, up to solver tolerance). Identity check: x^m(S) - x_B(S) = x_W20(S) = c_W20(S) - margin_W20(S).

    python w20b_tables.py --work <work/p1_v4_w20b_20261109>
"""
import argparse
import csv
from pathlib import Path

B = 1e9


def f(v, d=4, sign=False):
    if v is None or v == "":
        return "—"
    v = float(v)
    return f"{v:+.{d}f}" if sign else f"{v:.{d}f}"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--work", type=Path, required=True); a = ap.parse_args()
    rows = list(csv.DictReader(open(a.work / "CORE_CHECK_V4_56_BUNKER.csv")))
    g = lambda r, k: (float(r[k]) if r.get(k) not in (None, "") else None)
    VZ = {"strict": "严格", "within_tolerance": "容差内", "VIOLATION": "违反"}
    print("TABLE_A")
    print("| # | 运行 | 终止 | 障碍迭代 | 求解 s | 墙钟 s | 峰值 GiB | c^m(S) | x^m(S) | 余量 c − x | 阈值 | 判定 | α 最不利端余量 | 市场形式余量 | 余量 / 受益 | C1 | B1_BUNKERS |")
    print("|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---|---|")
    for k, r in enumerate(rows, 1):
        ratio = g(r, "margin_over_b_i_merged") if r.get("loo_country") else g(r, "margin_over_benefit")
        print(f"| {k} | {r['run']} | {r['termination']} | {r['barrier_iterations']} | {float(r['solve_seconds']):.0f} | {r['wall_seconds']} | {float(r['peak_rss_gib']):.2f} | "
              f"{f(g(r,'c_eur')/B)} | {f(g(r,'x_dual_eur')/B)} | **{f(g(r,'margin_dual_eur')/B, sign=True)}** | {f(g(r,'threshold_eur')/B, 3)} | {VZ[r['verdict']]} | "
              f"{f(g(r,'margin_dual_alpha_worst_eur')/B, sign=True)} | {f(g(r,'margin_market_eur')/B, sign=True)} | {f(ratio*100 if ratio is not None else None, 1, True)}{' %' if ratio is not None else ''} | "
              f"{'a b c' if r['c1_grade'] == 'layer1_plus_nodal_price_settlement' else r['c1_grade']} | {({'True': '通过', 'False': '不通过'}).get(r['gate_b1_bunkers'], '—')} |")
    print("\nTABLE_B")
    print("| 运行 | 成员数 | W20 c(S) | W20 余量 | c^m(S) | Δ_S = c^m − c_W20 | x_B(S) | **D_S = x_B(S) − Δ_S** | 合并余量 | 变化 = −D_S | P_S（联盟自身节点价） | 价格水平项 x_B(S) − P_S | 联盟内租金 P_S − Δ_S | 燃料舱能量 TWh | 均价 一体化 / 联盟 EUR/MWh | 恒等式残差 EUR |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|")
    out = []
    for r in rows:
        if r["run"] == "R0":
            continue
        xB = g(r, "x_bunker_part_eur"); dS = g(r, "bunker_increment_eur"); P = g(r, "bunker_payment_coalition_prices_eur"); DS = g(r, "D_S_eur")
        res = (g(r, "x_dual_eur") - xB) - (g(r, "w20_c_eur") - g(r, "w20_margin_eur"))
        chk = (g(r, "margin_dual_eur") - g(r, "w20_margin_eur")) + DS
        price, rent = xB - P, P - dS
        out.append(dict(run=r["run"], n_members=r["n_members"], w20_c_eur=g(r, "w20_c_eur"), w20_margin_eur=g(r, "w20_margin_eur"), c_m_eur=g(r, "c_eur"),
                        delta_S_eur=dS, x_B_S_eur=xB, D_S_eur=DS, margin_m_eur=g(r, "margin_dual_eur"), change_eur=g(r, "margin_change_vs_w20_eur"),
                        P_S_eur=P, price_level_term_eur=price, rent_term_eur=rent, price_plus_rent_minus_D_S_eur=price + rent - DS,
                        bunker_energy_twh=g(r, "bunker_energy_twh"), avg_price_integrated_eur_per_mwh=g(r, "bunker_avg_price_integrated_eur_per_mwh"),
                        avg_price_coalition_eur_per_mwh=g(r, "bunker_avg_price_coalition_eur_per_mwh"), identity_residual_x_eur=res, identity_residual_margin_eur=chk))
        print(f"| {r['run']} | {r['n_members']} | {f(g(r,'w20_c_eur')/B)} | {f(g(r,'w20_margin_eur')/B, sign=True)} | {f(g(r,'c_eur')/B)} | {f(dS/B)} | {f(xB/B)} | **{f(DS/B, sign=True)}** | "
              f"{f(g(r,'margin_dual_eur')/B, sign=True)} | {f(g(r,'margin_change_vs_w20_eur')/B, sign=True)} | {f(P/B)} | {f(price/B, sign=True)} | {f(rent/B, sign=True)} | "
              f"{f(g(r,'bunker_energy_twh'), 2)} | {f(g(r,'bunker_avg_price_integrated_eur_per_mwh'), 1)} / {f(g(r,'bunker_avg_price_coalition_eur_per_mwh'), 1)} | {res:.2f} |")
    print("\nTABLE_C")
    print("| 去一国 i | x_i^m | c(N) − c^m(N∖i)（i 连同港口燃料舱的边际贡献） | 余量 = x_i^m − 边际贡献 | 与核心余量之差 EUR | b_i^m | 余量 / b_i^m | W20 余量 | D_S |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        if not r.get("loo_country"):
            continue
        print(f"| {r['loo_country']} | {f(g(r,'x_i_merged_eur')/B)} | {f(g(r,'c_N_minus_c_eur')/B)} | **{f(g(r,'margin_marginal_contribution_eur')/B, sign=True)}** | "
              f"{g(r,'margin_marginal_contribution_eur') - g(r,'margin_dual_eur'):.2f} | {f(g(r,'b_i_merged_eur')/B, sign=True)} | {f(g(r,'margin_over_b_i_merged')*100, 1, True)} % | "
              f"{f(g(r,'w20_margin_eur')/B, sign=True)} | {f(g(r,'D_S_eur')/B, sign=True)} |")
    (a.work / "tables").mkdir(exist_ok=True)
    with open(a.work / "tables/W20B_DS_DECOMPOSITION.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]), lineterminator="\n"); w.writeheader()
        for r in out:
            w.writerow({k: (f"{v:.6f}" if isinstance(v, float) else v) for k, v in r.items()})
    print("\nCHECKS max|identity_residual_x| EUR", max(abs(r["identity_residual_x_eur"]) for r in out), "max|identity_residual_margin| EUR",
          max(abs(r["identity_residual_margin_eur"]) for r in out), "min rent bn", min(r["rent_term_eur"] for r in out) / B)


if __name__ == "__main__":
    main()
