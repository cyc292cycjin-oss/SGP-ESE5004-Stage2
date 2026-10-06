"""Reuse exact frozen-block evidence; no new model, solve, or presolve."""
import json, sys
from pathlib import Path
from fractions import Fraction
import pandas as pd
import pypsa
from fixed_accounts import validate_exported_accounting, validate_fixed_accounts
from gate5_resources import sha
from inventory_audit import FROZEN


def run(root,out,identity_path):
    source=root/'results_project/validation/gate5_20261006_01/research_2050_gate5_24h_validation_input.nc'
    assert sha(source)==FROZEN
    n=pypsa.Network(source);validate_exported_accounting(n)
    ledger={r['FixedAccountID']:r for r in validate_fixed_accounts(n)}
    identity=json.loads(identity_path.read_text())
    prior_path=root/'results_project/validation/gate5_20261006_02/local_diagnosis/LOCAL_FIXED_BLOCK_DIAGNOSIS.json'
    prior=json.loads(prior_path.read_text());assert prior['source_sha256']==FROZEN
    blocks={tuple(b['stores']):b for b in prior['blocks']}
    rows=[];single=[]
    for g in identity['groups']:
        block=blocks[tuple(g['stores'])]
        assert block['group']==g['group'] and block['final_buses']==g['final_buses']
        difference=Fraction(g['exact_annual_difference'])
        if len(g['stores'])==1:single.append(g)
        for s in g['stores']:
            r=ledger[s];link=n.links.loc[r['Meter']]
            rows.append(dict(group=g['group'],store=s,commodity=r['Commodity'],source_account_id=r['SourceAccountID'],
                source_row=r['SourceRow'],load=g['load'],fixed_initial_quantity_mwh=r['QuantityMWh'],
                fixed_quantity_ledger_qualified=True,fixed_destination=True,no_external_alternate_source=True,
                no_alternate_sink=True,no_conversion_substitution=True,
                multiple_stocks_share_demand=len(g['stores'])>1,
                no_decision_relevant_capital_or_variable_cost=True,
                capacity_nominal_variable_retained_in_conditional_proof=bool(link.p_nom_extendable),
                no_storage_arbitrage=True,no_cross_country_path=all(n.buses.at[b,'country']==r['Country'] for b in r['FinalBuses']),
                no_carbon_credit_port=True,policy_disabled=not n.meta['policy_enabled'],
                pending_cost_term=r['PendingFixedCostTerm'],pending_emission_term=r['PendingFixedPhysicalEmissionTerm'],
                stocks_in_block=len(g['stores']),block_variables_before=block['columns'],block_constraints_before=block['rows'],
                block_nnz_before=block['nnz'],block_counts_repeat_per_store=True,
                block_count_source='REUSED_FROZEN_EXACT_LOCAL_DIAGNOSIS_NO_PRESOLVE_RERUN',
                required_minus_initial_exact=g['exact_annual_difference'],
                exact_aggregate_stock_shortfall=difference>0,exact_terminal_stock_remainder_possible=difference<0,
                structural_single_stock_candidate=len(g['stores'])==1,
                executable_projection_candidate=False,projection_implemented=False,
                variables_saved=0,constraints_saved=0,estimated_memory_saved_bytes=0,
                proof_status='CONDITIONAL_SINGLE_STOCK_PROJECTION_DERIVED_NOT_IMPLEMENTED' if len(g['stores'])==1 else 'TEMPORAL_REPORTING_FIBER_NOT_ELIMINATED',
                exclusion='Exact rational prefix inequalities, meter capacity and reporting reconstruction must remain; no deletion by approximate annual identity'))
    out.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(out/'FIXED_BLOCK_PROJECTION_AUDIT.csv',index=False)
    report=dict(ledger_terms=len(rows),blocks=len(identity['groups']),structural_single_stock_candidates=len(single),
        multi_stock_blocks=len(identity['groups'])-len(single),exact_annual_zero_blocks=0,
        single_stock_exact_shortfall_blocks=sum(Fraction(g['exact_annual_difference'])>0 for g in single),
        single_stock_nonnegative_terminal_balance_blocks=sum(Fraction(g['exact_annual_difference'])<0 for g in single),
        executable_projection_candidates=0,implemented_candidates=0,variables_saved=0,constraints_saved=0,
        estimated_memory_saved_bytes=0,potential_single_stock_dynamic_variables=365*3*len(single),
        potential_counts_are_not_implemented_savings=True,
        proof='For one source with unity efficiency and fixed q_t, p_store_t=p_link_t=q_t; e_t=Q-sum_{k<=t}(h_k*q_k). Existential elimination of these dynamic variables is equivalent only if all 0<=e_t<=Q and original link-capacity inequalities on remaining P are retained using exact source constants. Reconstruction is unique for p/e but not P. Cost remains unchanged because removed terms have coefficient zero; the external Q*unknown terms and their identifiers remain. Nonzero terminal residual is preserved, never rounded to zero.',
        negative_cases=['Exact binary64 q/h/Q need not sum to the same annual quantity; positive required-minus-stock proves infeasibility of the nonnegative-stock subsystem.',
            'Negative annual difference leaves a nonzero terminal balance; it is not proof of empty feasibility or an exactly exhausted ledger.',
            'For two unit stocks and two unit demands, releases ((1,0),(0,1)) and ((0,1),(1,0)) are both allowed. Fixing equal-hour splits deletes admissible reporting paths.',
            'Even an independent zero-cost meter has a nominal-capacity feasibility interval. Keep P or provide a set-valued reporting reconstruction; do not report arbitrary P as uniquely determined.'],
        decision='No rational-prefix replacement, solver elimination, temporal split or reporting change implemented. Lifetime optimization does not need projection.',
        evidence=dict(source_sha256=FROZEN,identity_sha256=sha(identity_path),local_block_evidence_sha256=sha(prior_path)),
        solver_runs=0,presolve_calls=0)
    (out/'PROJECTION_SUMMARY.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]))
