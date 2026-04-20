import networkx as nx
import os

import argparse


def main():
    from lm_taxonomies import helm_data as txm_helm_data
    from lm_taxonomies import utils as txm_utils

    # Create an ArgumentParser object
    parser = argparse.ArgumentParser(
        description="Script for testing taxonomy fitness against a dataset test collection."
    )

    # Add arguments for the paths
    parser.add_argument(
        "--taxonomy", "-t", type=str, required=True, help="Path to the taxonomy file"
    )
    parser.add_argument(
        "--data",
        "-d",
        action="append",
        type=str,
        help="Path (or multiple paths) to the HELM data or any other custom dataset.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        required=True,
        help="Output path for the resulting graphs.",
    )
    parser.add_argument(
        "--models",
        "-m",
        type=str,
        required=True,
        help="List of models (separated by commas) to generate graphs for.",
    )

    # Parse arguments from the command line
    args = parser.parse_args()
    TAXONOMY_PATH = args.taxonomy
    HELM_RESULTS_PATHS = args.data
    OUTPUT_PATH = args.output
    MODELS_USE = args.models.split(",")

    # Get taxonomy name
    taxonomy_name = os.path.basename(TAXONOMY_PATH).split(".")[0]
    print('Processing taxonomy: "%s"' % taxonomy_name)

    # Load taxonomy
    print(
        "--------------------------------------------------------------------------------"
    )
    print("Reading taxonomy graph:")
    taxonomy_graph, _, _, _ = txm_utils.load_taxonomy(
        TAXONOMY_PATH, return_all=True, verbose=True, print_prefix="\t"
    )

    # Get all the required datasets from the taxonomy graph
    print(
        "--------------------------------------------------------------------------------"
    )
    print("Reading taxonomy datasets:")
    datasets_list = txm_utils.get_taxonomy_datasets(taxonomy_graph)

    # Read all the required data from HELM
    print(
        "--------------------------------------------------------------------------------"
    )
    helm_samples_dict = dict()
    for data_path in HELM_RESULTS_PATHS:
        print("Analyzing dataset path: %s" % data_path)
        helm_samples_dict = txm_helm_data.read_helm_data(
            data_path,
            datasets_list,
            current_dict=helm_samples_dict,
            verbose=True,
            print_prefix="\t",
        )
    print(
        "--------------------------------------------------------------------------------"
    )
    print("Processing Models:")
    all_graphs = list()
    for target_model in MODELS_USE:
        model_graph = txm_utils.get_model_graph(
            taxonomy_graph, helm_samples_dict, target_model
        )
        print(f"\t{model_graph.name}")
        all_graphs.append(model_graph)

    print(
        "--------------------------------------------------------------------------------"
    )
    print("Saving to disk...")
    try:
        for graph_out in all_graphs:
            nx.drawing.nx_agraph.write_dot(
                graph_out, os.path.join(OUTPUT_PATH, graph_out.name + ".txt")
            )
    except Exception as e:
        print(f"Unable to save graphs: {str(e)}")


# Run the main function if the script is executed directly
if __name__ == "__main__":
    print(
        "--------------------------------------------------------------------------------"
    )
    main()
    print(
        "--------------------------------------------------------------------------------"
    )
    print("Finished.")
