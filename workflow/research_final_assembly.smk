# Final Assembly V1 DAG: accepted input data, immutable qualified stock,
# new allocations and unbound recipe. No solver target.
FINALALLOC = ROOT + "/final_allocation"
FINALASSETS = ROOT + "/final_assets"
rule research_final_allocate:
    input:
        registry="research_inputs/assembly_v1/registry.json",
        source=lambda w: config["source_reference"],
        ports=lambda w: config["source_ports"],
        airports=lambda w: config["source_airports"],
        previous_registry=lambda w: config["final_reuse_registry"],
        script="scripts_project/allocate_assembly_inputs.py",
    output:
        manifest=FINALALLOC + "/allocation_manifest.json",
        arrays=FINALALLOC + "/allocations.npz",
    params:
        reuse=lambda w: config["final_reuse_allocation"],
    shell:
        "python scripts_project/allocate_assembly_inputs.py --registry {input.registry:q} --reference {input.source:q} --ports {input.ports:q} --airports {input.airports:q} --reuse {params.reuse:q} --reuse-registry {input.previous_registry:q} --output " + FINALALLOC

rule research_final_assets:
    input:
        allocation=FINALALLOC + "/allocation_manifest.json",
        arrays=FINALALLOC + "/allocations.npz",
        registry="research_inputs/assembly_v1/registry.json",
        decisions="research_inputs/assembly_v1/sources/ASSEMBLY_V1_FINAL_DECISIONS.json",
        electric=lambda w: config["frozen_gate4_assets"] + "/electric_base_2050_unsolved.nc",
        stock=lambda w: config["frozen_gate4_assets"] + "/SELECTED_ASSET_SURVIVAL_2050.json",
        contract=lambda w: config["frozen_gate4_assets"] + "/SELECTED_INTEGRATION_CONTRACT.json",
        costs=lambda w: config["source_costs2050"],
        builder="scripts_project/build_complete_assembly.py",
        fragment="scripts_project/build_research_assets.py",
        fixed_accounts="scripts_project/fixed_accounts.py",
        fixed_scope="scripts_project/fixed_account_scope.py",
        fixed_decision="research_inputs/assembly_v1/sources/ANIMAL_WASTE_FIXED_ACCOUNT_DECISION.json",
        price_code="scripts_project/price_basis.py",
        architecture="scripts_project/carrier_architecture.py",
        carbon_code="scripts_project/carbon_architecture.py",
        price_layer=lambda w: config["frozen_gate4_assets"] + "/model_cost_layer.json",
        source_manifest=lambda w: config["frozen_gate4_assets"] + "/ELECTRIC_BASE_ASSET_MANIFEST.json",
    params:
        source=lambda w: config["frozen_gate4_assets"],
    output:
        bundle=FINALASSETS + "/asset_bundle.json",
        electric=FINALASSETS + "/electric_base_2050_unsolved.nc",
        recipe=FINALASSETS + "/carrier_fragment.json",
        carbon=FINALASSETS + "/carbon_component_map.json",
    shell:
        "python scripts_project/build_complete_assembly.py --repo . --source-assets {params.source:q} --allocation " + FINALALLOC + " --output " + FINALASSETS + " --costs {input.costs:q}"

rule research_final_complete_unsolved:
    input:
        bundle=FINALASSETS + "/asset_bundle.json",
        electric=FINALASSETS + "/electric_base_2050_unsolved.nc",
        recipe=FINALASSETS + "/carrier_fragment.json",
        carbon=FINALASSETS + "/carbon_component_map.json",
        registry="research_inputs/assembly_v1/registry.json",
        pins="research_inputs/assembly_v1/manifest.json",
        allocations=FINALALLOC + "/allocation_manifest.json",
        arrays=FINALALLOC + "/allocations.npz",
        assembler="scripts_project/build_research_network.py",
        validator="scripts_project/validate_fullsc_final.py",
        fixed_accounts="scripts_project/fixed_accounts.py",
        fixed_scope="scripts_project/fixed_account_scope.py",
        fixed_decision="research_inputs/assembly_v1/sources/ANIMAL_WASTE_FIXED_ACCOUNT_DECISION.json",
        shared="scripts_project/assembly_components.py",
        price="scripts_project/price_basis.py",
        carbon_architecture="scripts_project/carbon_architecture.py",
    output:
        network=ROOT + "/research_fullsc_2050_assembly_v1_unsolved.nc",
        manifest=ROOT + "/FULLSC_ASSEMBLY_V1_NETWORK_MANIFEST.json",
    shell:
        "python scripts_project/build_research_network.py --repo . --allocation " + FINALALLOC + " --assets {input.bundle:q} --output {output.network:q} --report {output.manifest:q}"
