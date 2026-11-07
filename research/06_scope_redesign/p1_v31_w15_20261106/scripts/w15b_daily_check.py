"""V31 W15 stage B, section 8.2 support: quantities behind the daily-resolution conclusions, side by side for the v3.1 2920x3h runs and the
supplement 07 (s07) / first screening 365-daily-slice runs, from exported files only (read only; no solver).

  python -I w15b_daily_check.py --final <unpacked/export> --s07 <s07 export> --screen <screening export> --out <work/p1_v31_w15_20261106>

Writes evidence/DAILY_CHECK_VALUES.json.
"""
import argparse, csv, json
from pathlib import Path

PLAYERS = ("BN", "ID", "KH", "LA", "MM", "MY", "PH", "SG", "TH", "TL", "VN", "BUNKER")


def rows(p: Path):
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def la_vn_and_la_export(d: Path) -> dict:
    cap, exp_la = 0.0, 0.0
    for r in rows(d / "cross_border_flows.csv"):
        c0, c1 = r["country0"], r["country1"]
        if {c0, c1} == {"LA", "VN"} and r["transport_carrier"] == "electricity":
            cap += float(r["capacity_opt_mw"] or 0)
        if r["transport_carrier"] == "electricity" and "LA" in (c0, c1) and c0 != c1:
            e01, e10 = float(r["energy_0_to_1_mwh"] or 0), float(r["energy_1_to_0_mwh"] or 0)
            exp_la += (e01 - e10) if c0 == "LA" else (e10 - e01)
    return dict(la_vn_electricity_capacity_gw=cap / 1e3, la_net_electricity_export_twh=exp_la / 1e6)


def ledger_row(d: Path, ent: str) -> dict:
    for r in rows(d / "COUNTRY_COST_LEDGER.csv"):
        if r["entity"] == ent:
            return {k: float(v) / 1e9 for k, v in r.items() if k != "entity" and v not in ("", None)}
    return {}


def methanol_prices(d: Path) -> dict:
    out = {}
    for r in rows(d / "NODAL_PRICES.csv"):
        if r["carrier"] == "methanol" and r["bus"].endswith(" methanol") and len(r["bus"].split()) == 2:
            out[r["bus"].split()[0]] = float(r["mean"]) if r["mean"] not in ("", "nan") else None
    return out


def vn_biomass(d: Path) -> dict:
    G = json.loads((d / "V5_GATES.json").read_text(encoding="utf-8"))
    vn = [r for r in G["B3"]["rows"] if r["country"] == "VN"]
    pot = sum(r["potential_mwh"] for r in vn); used = sum(r["used_mwh"] for r in vn)
    return dict(vn_pools=len(vn), vn_potential_twh=pot / 1e6, vn_used_twh=used / 1e6, vn_share=used / pot if pot else None,
                vn_pools_fully_used=sum(1 for r in vn if r["share_used"] >= 0.999999))


def owen(d: Path) -> dict:
    return {r["player"]: float(r["owen_dual_alpha_0.5_eur"]) / 1e9 for r in rows(d / "m12_owen" / "OWEN.csv")}


def main():
    ap = argparse.ArgumentParser()
    for k in ("final", "s07", "screen", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    F, S, SC, OUT = map(Path, (a.final, a.s07, a.screen, a.out))
    sets = {"F1": F / "F1", "F2": F / "F2", "F3": F / "F3", "F4": F / "F4", "s07_V1": S / "V1", "s07_V2": S / "V2", "screen_V1": SC / "V1", "screen_V2": SC / "V2"}
    res = {}
    for k, d in sets.items():
        if not d.exists():
            continue
        r = dict(la_vn_and_la_export(d), methanol_price_mean=methanol_prices(d), owen_alloc_bn=owen(d))
        led = ledger_row(d, "ID")
        r["ID_ledger_bn"] = {s: led.get(s) for s in ("network_trade_AC", "network_trade_DC", "network_trade_gas pipeline", "network_trade_H2 pipeline", "total")}
        try:
            r.update(vn_biomass(d))
        except Exception as e:   # older exports
            r["vn_biomass_error"] = str(e)[:100]
        res[k] = r
    ben = {}
    for p, (i, dd) in {"F": ("F1", "F2"), "FB": ("F3", "F4"), "s07": ("s07_V1", "s07_V2"), "screen": ("screen_V1", "screen_V2")}.items():
        if i in res and dd in res:
            ben[p] = {pl: res[dd]["owen_alloc_bn"].get(pl, 0.0) - res[i]["owen_alloc_bn"].get(pl, 0.0) for pl in PLAYERS}
    res["owen_benefit_bn"] = ben
    (OUT / "evidence").mkdir(exist_ok=True)
    (OUT / "evidence" / "DAILY_CHECK_VALUES.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
    for k, v in res.items():
        if k == "owen_benefit_bn":
            for p, b in v.items():
                print("benefit", p, {pl: round(x, 3) for pl, x in b.items()})
        else:
            print(k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if kk not in ("owen_alloc_bn", "methanol_price_mean")},
                  "TL alloc", round(v["owen_alloc_bn"].get("TL", 0), 4), "MeOH", {c: round(x, 2) for c, x in v["methanol_price_mean"].items() if x is not None})


if __name__ == "__main__":
    main()
