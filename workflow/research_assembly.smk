# Standalone Research DAG. No include of upstream solve/final_adjustment rules.
# snakemake -s workflow/research_assembly.smk --cores 1 --config ...
rule research_fullsc_unsolved:
    input:
        registry="research_inputs/assembly_v1/registry.json",
        pins="research_inputs/assembly_v1/manifest.json",
        allocation=lambda w: config["research_allocation_dir"] + "/allocation_manifest.json",
        arrays=lambda w: config["research_allocation_dir"] + "/allocations.npz",
        assets=lambda w: config["research_asset_manifest"],
    output:
        network="results_project/assembly_v1/research_fullsc_2050_unsolved.nc",
        report="results_project/assembly_v1/build_receipt.json",
    params:
        allocation=lambda w: config["research_allocation_dir"],
    shell:
        "python scripts_project/build_research_network.py --repo . --allocation {params.allocation:q} --assets {input.assets:q} --output {output.network:q} --report {output.report:q}"
