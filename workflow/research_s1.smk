# S1 (2026-10-15) scenario DAG. Builds integrated and disconnected unsolved networks from the
# frozen source-qualified electric base. No solver target; solving is authorised separately.
S1 = "results_project/s1"
S1_SCENARIOS = ["integrated", "disconnected"]

rule research_s1_all:
    input:
        expand(S1 + "/{scenario}/{scenario}_BUILD_RECEIPT.json", scenario=S1_SCENARIOS),
        S1 + "/S1_STOCK_REVIEW.json",

rule research_s1_stock_review:
    input:
        frozen="results_project/assembly_v1/final_assets/SELECTED_ASSET_SURVIVAL_2050.json",
        contract="results_project/assembly_v1/final_assets/SELECTED_INTEGRATION_CONTRACT.json",
        electric="results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc",
        decisions="research_inputs/asset_survival/lifetime_decisions_s1.json",
        script="scripts_project/s1_inputs_review.py",
    params:
        cache=lambda w: config["source_plant_cache"],
    output:
        S1 + "/S1_STOCK_REVIEW.json",
        S1 + "/S1_SELECTED_ASSET_SURVIVAL_2050.json",
    shell:
        "python scripts_project/s1_inputs_review.py stock --repo . --cache {params.cache:q} --output " + S1

rule research_s1_corridors:
    input:
        electric="results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc",
        control="research/04_model_assembly/gate4/ELECTRICITY_INTERCONNECT_CONTROL_SET.csv",
        script="scripts_project/s1_inputs_review.py",
    output:
        "research_inputs/corridors/cross_border_corridors.csv",
    shell:
        "python scripts_project/s1_inputs_review.py corridors --repo . --output {output:q}"

rule research_s1_scenario:
    input:
        electric="results_project/assembly_v1/final_assets/electric_base_2050_unsolved.nc",
        price_layer="results_project/assembly_v1/final_assets/model_cost_layer.json",
        allocation="results_project/assembly_v1/final_allocation/allocation_manifest.json",
        corridors="research_inputs/corridors/cross_border_corridors.csv",
        costs=lambda w: config["source_costs2050"],
        config_base="configs/research/baseline.yaml",
        config_scenario="configs/research/{scenario}.yaml",
        builder="scripts_project/scenario_network.py",
        adapter="scripts_project/sector_adapter.py",
        carbon="scripts_project/country_carbon.py",
        candidates="scripts_project/s1_candidates.py",
        validator="scripts_project/build_research_network.py",
        upstream="scripts/prepare_sector_network.py",
    output:
        receipt=S1 + "/{scenario}/{scenario}_BUILD_RECEIPT.json",
        network=S1 + "/{scenario}/{scenario}_2920_3h_unsolved.nc",
        daily=S1 + "/{scenario}/{scenario}_365_24h_unsolved.nc",
    shell:
        "python scripts_project/scenario_network.py --repo . --scenario {wildcards.scenario} --costs {input.costs:q} --output " + S1 + "/{wildcards.scenario}"
