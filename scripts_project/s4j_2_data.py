"""S4J-2 data and checks (decision 105 a, S4I U1): transmission losses as PyPSA-Eur v2025.07.0.

  * source checks: the PyPSA-Eur lines (config transmission_efficiency 747-763, solving.options.transmission_losses 1001; prepare_sector_network.py
    lossy_bidirectional_links 5727-5774 and its call 6445-6447) and the PyPSA 0.30.3 implementation (optimize.create_model transmission_losses,
    define_loss_variables, define_loss_constraints, nodal balance -0.5 x loss at each end, post_processing p0 / p1 += loss / 2), asserted line by line.
  * LOSS_LINKS_S4J2.csv: every DC / H2 / gas link of the built network - direction (forward / reversed / one-way), length, efficiency, compression bus
    and efficiency2; LOSS_LINES_S4J2.csv: every AC line - r_pu_eff, s_max_pu, s_nom_max, the two tangent points of the PyPSA approximation and the
    implied loss share of the flow at each tangent point and at one circuit's thermal rating.
  * model-build check (no solve): the first 56 snapshots, create_model(transmission_losses=2) + research hooks as s2_solve.py - counts of loss
    variables, tangent / upper constraints and sync rows; the coefficient ranges of the loss rows.
  * registry fragment s4j_2.

    python scripts_project/s4j_2_data.py --network <S4J-2 integrated build>
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from d1_common import REG_DIR, ROOT, Registry, sha256, write_csv
from s4j_layers import AC_TRANSMISSION_LOSSES, LOSS_EFFICIENCY, REV, SYNC_HOOK

SCRIPT = "scripts_project/s4j_2_data.py"
INSTRUCTION_SHA = "c20957448c69128c05eaf4e271bcca7f98eecc7ccd3121cd37f3581daff3348f"
LOC = "work/p1_step4j_20261018/S4J_CLAUDE_CODE_INSTRUCTION.md"
SRC = ROOT / "research_inputs/registry_v5/sources"
CONF = SRC / "pypsa_eur_v2025.07.0_config.default.yaml"
PSN = SRC / "pypsa_eur_v2025.07.0_prepare_sector_network.py"
OUT = ROOT / "research_inputs/corridors"


def _line(path: Path, no: int, text: str) -> dict:
    got = path.read_text().splitlines()[no - 1]
    if text not in got:
        raise ValueError(f"{path.name} line {no} changed: {got.strip()}")
    return dict(file=path.name, line=no, text=got.strip())


def source_checks() -> dict:
    import pypsa
    P = Path(pypsa.__file__).parent / "optimization"
    out = dict(pypsa_eur=dict(sha256_config=sha256(CONF), sha256_psn=sha256(PSN), lines=[
        _line(CONF, 747, "transmission_efficiency:"), _line(CONF, 749, "- DC"), _line(CONF, 750, "- H2 pipeline"), _line(CONF, 751, "- gas pipeline"),
        _line(CONF, 754, "efficiency_static: 0.98"), _line(CONF, 755, "efficiency_per_1000km: 0.977"), _line(CONF, 757, "efficiency_per_1000km: 1"),
        _line(CONF, 758, "compression_per_1000km: 0.018"), _line(CONF, 760, "efficiency_per_1000km: 1"), _line(CONF, 761, "compression_per_1000km: 0.01"),
        _line(CONF, 763, "efficiency_static: 0.97"), _line(CONF, 1001, "transmission_losses: 2"),
        _line(PSN, 5727, "def lossy_bidirectional_links(n, carrier, efficiencies={}):"), _line(PSN, 5748, 'n.links.loc[carrier_i, "p_min_pu"] = 0'),
        _line(PSN, 5757, 'rev_links["capital_cost"] = 0'), _line(PSN, 5758, 'rev_links["length"] = 0'), _line(PSN, 5760, '.map(lambda x: x + "-reversed")'),
        _line(PSN, 5769, 'n.links.loc[carrier_i, "bus2"] = n.links.loc[carrier_i, "bus0"].map('), _line(PSN, 5773, "-compression_per_1000km * n.links.loc[carrier_i, \"length_original\"] / 1e3"),
        _line(PSN, 6445, 'for k, v in options["transmission_efficiency"].items():'), _line(PSN, 6447, "lossy_bidirectional_links(n, k, v)")]),
        pypsa=dict(version=pypsa.__version__, lines=[
            _line(P / "optimize.py", 207, "transmission_losses: int = 0,"), _line(P / "optimize.py", 260, "define_loss_variables(n, sns, c)"),
            _line(P / "optimize.py", 305, "define_loss_constraints(n, sns, c, transmission_losses)"), _line(P / "optimize.py", 458, "n.lines_t.p0 += losses / 2"),
            _line(P / "optimize.py", 459, "n.lines_t.p1 += losses / 2"), _line(P / "constraints.py", 556, "if transmission_losses:"),
            _line(P / "constraints.py", 559, '["Line", "loss", "bus0", -0.5],'), _line(P / "constraints.py", 560, '["Line", "loss", "bus1", -0.5],'),
            _line(P / "constraints.py", 932, "def define_loss_constraints("), _line(P / "constraints.py", 947, "if not isfinite(s_nom_max).all():"),
            _line(P / "constraints.py", 956, "upper_limit = r_pu_eff * (s_max_pu * s_nom_max) ** 2"), _line(P / "constraints.py", 964, "p_k = k / tangents * s_max_pu * s_nom_max"),
            _line(P / "variables.py", 155, 'n.model.add_variables(0, coords=coords, name=f"{c}-loss", mask=active)')]))
    return out


def link_table(n) -> pd.DataFrame:
    L = n.links[n.links.carrier.isin(list(LOSS_EFFICIENCY))]
    rows = []
    for k, z in L.iterrows():
        par = LOSS_EFFICIENCY[z.carrier]; Lo = float(z.length_original)
        exp = par["efficiency_static"] * par["efficiency_per_1000km"] ** (Lo / 1e3)
        kind = "reversed" if bool(z.reversed) else ("forward" if (k + REV) in n.links.index else "one-way")
        rows.append(dict(link=k, carrier=z.carrier, kind=kind, bus0=z.bus0, bus1=z.bus1, border_class=z.border_class, length_original_km=Lo, length_km=float(z.length),
                         efficiency=float(z.efficiency), efficiency_expected=exp, loss_share=1 - float(z.efficiency), bus2=str(z.get("bus2", "")),
                         # no compression port (DC): bus2 empty, PyPSA keeps the default efficiency2 = 1 (unused) -> reported as 0
                         efficiency2=(float(z.efficiency2) if str(z.get("bus2", "")) else 0.0), efficiency2_expected=-par["compression_per_1000km"] * Lo / 1e3,
                         p_nom=float(z.p_nom), p_nom_max=float(z.p_nom_max), p_nom_extendable=bool(z.p_nom_extendable), capital_cost=float(z.capital_cost), p_min_pu=float(z.p_min_pu)))
    T = pd.DataFrame(rows)
    bad = T[(abs(T.efficiency - T.efficiency_expected) > 1e-12) | (abs(T.efficiency2 - T.efficiency2_expected) > 1e-12) | (T.p_min_pu != 0)
            | ((T.carrier == "DC") & (T.bus2 != "")) | ((T.carrier != "DC") & (T.bus2 == ""))]
    if len(bad):
        raise ValueError(f"loss parameters differ from the rule: {list(bad.link)[:5]}")
    return T


def line_table(n) -> pd.DataFrame:
    n.calculate_dependent_values()
    Ln = n.lines; s_max = n.get_switchable_as_dense("Line", "s_max_pu").max()
    rows = []
    for k, z in Ln.iterrows():
        smax = float(z.s_nom_max if z.s_nom_extendable else z.s_nom); spu = float(s_max[k]); r = float(z.r_pu_eff)
        pts = [i / AC_TRANSMISSION_LOSSES * spu * smax for i in range(1, AC_TRANSMISSION_LOSSES + 1)]
        one_circuit = math.sqrt(3) * float(n.buses.at[z.bus0, "v_nom"]) * float(n.line_types.at[z.type, "i_nom"]) if z.type else float("nan")
        rows.append(dict(line=k, border_class=z.border_class, length_km=float(z.length), num_parallel=float(z.num_parallel), r_ohm=float(z.r), r_pu_eff=r, s_nom=float(z.s_nom),
                         s_nom_max=smax, s_max_pu=spu, candidate=bool(z.s_nom == 0 and z.s_nom_extendable), tangent_point_1_mw=pts[0], tangent_point_2_mw=pts[-1],
                         zero_loss_below_mw=pts[0] / 2, loss_share_at_tangent_1=r * pts[0], loss_share_at_tangent_2=r * pts[-1],
                         one_circuit_rating_mw=one_circuit, exact_loss_share_at_one_circuit_x_s_max_pu=r * spu * one_circuit,
                         exact_loss_share_at_one_circuit_x_s_max_pu_per_100km=(r * spu * one_circuit / float(z.length) * 100) if z.length else float("nan")))
    return pd.DataFrame(rows)


def model_check(network: Path) -> dict:
    import pypsa
    from assembly_components import install_research_constraint_hooks
    t0 = time.time(); n = pypsa.Network(str(network)); n.set_snapshots(n.snapshots[:56])
    n.meta.update(solver_allowed=True, artifact_role="S4J2_MODEL_CHECK_UNSOLVED", s2_solve_label="S4J2_MODEL_CHECK")
    tl = int(n.meta["research_transmission_losses"]["ac_transmission_losses"])
    m = n.optimize.create_model(transmission_losses=tl); install_research_constraint_hooks(n)
    loss = m.variables["Line-loss"]; cons = [k for k in m.constraints if k.startswith("Line-loss")]
    sync = [k for k in m.constraints if k.startswith(SYNC_HOOK)]
    coef = []
    for k in cons:
        c = m.constraints[k]; v = np.asarray(c.coeffs.values).ravel(); v = v[np.isfinite(v) & (v != 0)]
        r = np.asarray(c.rhs.values).ravel(); r = r[np.isfinite(r)]
        coef.append(dict(constraint=k, rows=int(np.asarray(c.labels.values).ravel().__ge__(0).sum()), coeff_abs_min=float(np.abs(v).min()), coeff_abs_max=float(np.abs(v).max()),
                         rhs_abs_max=float(np.abs(r).max()) if r.size else 0.0))
    return dict(network=str(network), snapshots=int(len(n.snapshots)), ac_tangents=tl, loss_variables=int(np.asarray(loss.labels.values).ravel().__ge__(0).sum()),
                loss_constraints=coef, sync_rows=len(sync), lines=int(len(n.lines)), reversed_extendable=int((n.links.reversed.astype(bool) & n.links.p_nom_extendable).sum()),
                num_col=int(m.nvars), num_row=int(m.ncons), seconds=time.time() - t0)


def main():
    import pypsa
    logging.disable(logging.WARNING)
    ap = argparse.ArgumentParser(); ap.add_argument("--network", type=Path, required=True); a = ap.parse_args()
    src = source_checks()
    n = pypsa.Network(str(a.network))
    if n.meta["research_transmission_losses"]["mode"] != "pypsa_eur":
        raise ValueError("--network is not a transmission_losses = pypsa_eur build")
    LT = link_table(n); write_csv(LT.to_dict("records"), OUT / "LOSS_LINKS_S4J2.csv", list(LT.columns))
    AT = line_table(n); write_csv(AT.to_dict("records"), OUT / "LOSS_LINES_S4J2.csv", list(AT.columns))
    mc = model_check(a.network)
    summ = dict(network=str(a.network), sources=src, meta=n.meta["research_transmission_losses"], model_check=mc,
                links={f"{c}|{k}": int(v) for (c, k), v in LT.groupby(["carrier", "kind"]).size().items()}, dc_loss_share=dict(min=float(LT[LT.carrier == "DC"].loss_share.min()), max=float(LT[LT.carrier == "DC"].loss_share.max())),
                compression=LT[LT.carrier != "DC"].groupby("carrier").efficiency2.agg(["min", "max"]).to_dict(orient="index"),
                lines=dict(candidates=int(AT.candidate.sum()), r_pu_eff_min=float(AT.r_pu_eff.min()), r_pu_eff_max=float(AT.r_pu_eff.max()),
                           zero_loss_below_mw_min=float(AT.zero_loss_below_mw.min()), zero_loss_below_mw_max=float(AT.zero_loss_below_mw.max()),
                           loss_share_at_tangent_1=dict(candidates_median=float(AT[AT.candidate].loss_share_at_tangent_1.median()), candidates_max=float(AT[AT.candidate].loss_share_at_tangent_1.max()),
                                                        stock_median=float(AT[~AT.candidate].loss_share_at_tangent_1.median()), stock_max=float(AT[~AT.candidate].loss_share_at_tangent_1.max())),
                           exact_loss_per_100km_at_one_circuit_median=float(AT.exact_loss_share_at_one_circuit_x_s_max_pu_per_100km.median())))
    (OUT / "LOSSES_S4J2.json").write_text(json.dumps(summ, indent=1, default=str))
    reg = Registry(SCRIPT)
    reg.add("s4j2_transmission_losses_switch", "Decision 105 a: research.network.transmission_losses = pypsa_eur (main) | none (S4H state, comparison; default when absent)",
            "pypsa_eur|none", "flag", "B", "S4J instruction S4J-2", LOC, INSTRUCTION_SHA, decision_ref="105", status="REFERENCE_ONLY")
    reg.add("s4j2_ac_transmission_losses", f"Decision 105 a: AC line losses = PyPSA piecewise-linear approximation with {AC_TRANSMISSION_LOSSES} tangents (PyPSA-Eur v2025.07.0 "
            "solving.options.transmission_losses, config line 1001), passed by s2_solve.py to create_model from n.meta['research_transmission_losses']; PyPSA "
            f"{src['pypsa']['version']}: loss variable per line and snapshot, loss >= tangents of r_pu_eff x s^2 at k/N x s_max_pu x s_nom_max, loss <= r_pu_eff x "
            "(s_max_pu x s_nom_max)^2, -0.5 x loss in the nodal balance at each end, p0 / p1 += loss / 2 after the solve; the same function PyPSA-Eur calls",
            float(AC_TRANSMISSION_LOSSES), "tangents", "B", "PyPSA-Eur v2025.07.0 config.default.yaml; PyPSA 0.30.3 optimization/constraints.py, optimize.py",
            "config 1001; constraints.py 556-560, 932-974; optimize.py 207, 260, 305, 455-459", src["pypsa_eur"]["sha256_config"], decision_ref="105", status="REFERENCE_ONLY")
    reg.add("s4j2_link_losses", "Decision 105 a: DC efficiency 0.98 x 0.977^(L/1000); H2 pipeline compression 0.018 and gas pipeline compression 0.01 MWh_el per MWh and "
            "1000 km on the electricity bus of the sending end (efficiency 1); CO2 pipelines lossless; distribution grid 0.97 not used (S4I R10); bidirectional links split "
            "into forward + '-reversed' (capital cost 0, length 0, length_original kept) with equal capacity (hook research_lossy_bidirectional_sync = PyPSA-Eur "
            "Link-bidirectional_sync; solve_network.py not in the repository); one-way links keep their direction", "table", "flag", "B",
            "PyPSA-Eur v2025.07.0 config.default.yaml 747-763; prepare_sector_network.py 5727-5774, 6445-6447", "research_inputs/corridors/LOSS_LINKS_S4J2.csv",
            sha256(OUT / "LOSS_LINKS_S4J2.csv"), decision_ref="105", status="REFERENCE_ONLY")
    reg.add("s4j2_line_loss_approximation", "Decision 105 a, record: the PyPSA loss tangents sit at k/2 x s_max_pu x s_nom_max (s_nom_max = s_nom + 20 GW), so the "
            f"approximated loss is 0 below {summ['lines']['zero_loss_below_mw_min']:.0f}-{summ['lines']['zero_loss_below_mw_max']:.0f} MW of flow and r is not reduced when "
            "a line is extended (fixed num_parallel); for the one-circuit candidates the loss share at the first tangent point is "
            f"{summ['lines']['loss_share_at_tangent_1']['candidates_median']:.2f} (median) - the same behaviour as PyPSA-Eur, whose lines also keep r when extended",
            "table", "flag", "B", "derived (scripts_project/s4j_2_data.py)", "research_inputs/corridors/LOSS_LINES_S4J2.csv", sha256(OUT / "LOSS_LINES_S4J2.csv"),
            decision_ref="105", status="REFERENCE_ONLY")
    reg.write(REG_DIR / "fragments" / "s4j_2.csv")
    print(json.dumps({k: summ[k] for k in ("links", "dc_loss_share", "compression", "lines")}, indent=1, default=str))
    print(json.dumps({k: v for k, v in mc.items() if k != "loss_constraints"}, indent=1)); print(json.dumps(mc["loss_constraints"], indent=1))


if __name__ == "__main__":
    main()
