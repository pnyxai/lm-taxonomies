import re
import networkx as nx
import numpy as np
import pandas as pd
from typing import List
import os
import json

current_dir = os.path.dirname(os.path.abspath(__file__))

# Only initialized if needed
models_config = None


def load_taxonomy(
    file_path: str,
    return_all: List = False,
    verbose: bool = False,
    print_prefix: str = "",
) -> any:
    """
    Loads a taxonomy in the graphviz format:

        digraph taxonomy_001 {
            Reasoning -> Deduction;
            ...
            }
        digraph taxonomy_001_labeling {
            Reasoning -> LegalSupport;
            ...
            }

    Returns a networkx representation of it.
    """

    # Load both graphs, taxonomy and labels
    graphs_dict = dict()
    with open(file_path) as f:
        for line in f:
            if len(line) == 0 or re.search("\s+//", line):
                continue

            if "{" in line:
                graph_name = line.split("digraph")[-1].split("{")[0].strip()
                if verbose:
                    print(print_prefix + "Found graph : %s" % graph_name)
                graphs_dict[graph_name] = nx.DiGraph(name=graph_name)
            elif "}" in line:
                continue
            elif " -> " not in line:
                continue
            else:
                # Get nodes
                from_n = (
                    line.split(" -> ")[0].strip().replace(";", "").replace(":", "---")
                )
                to_n = (
                    line.split(" -> ")[-1].strip().replace(";", "").replace(":", "---")
                )
                # Add to graph (wont be duplicated)
                graphs_dict[graph_name].add_node(from_n)
                graphs_dict[graph_name].add_node(to_n)
                # Add edge
                graphs_dict[graph_name].add_edge(from_n, to_n)

    # Check taxonomy file in correct order and naming convention
    assert len(graphs_dict.keys()) == 2
    taxonomy_name = list(graphs_dict.keys())[0]
    assert taxonomy_name + "_labeling" == list(graphs_dict.keys())[1]

    # Add datasets to nodes in the taxonomy graph using the labels graph
    dataset_correspondency = dict()
    for edge in graphs_dict[taxonomy_name + "_labeling"].edges:
        if edge[0] not in dataset_correspondency.keys():
            dataset_correspondency[edge[0]] = list()
        dataset_correspondency[edge[0]].append(edge[1])
    taxonomy_graph = graphs_dict[taxonomy_name]
    labels_graph = graphs_dict[taxonomy_name + "_labeling"]
    nx.set_node_attributes(taxonomy_graph, dataset_correspondency, name="datasets")

    # Get the measurable edges, those with defined datasets in both nodes
    undefined_edges = list()
    measurable_edges = list()
    for edge in taxonomy_graph.edges:
        if (
            taxonomy_graph.nodes[edge[0]].get("datasets", None) is None
        ) or taxonomy_graph.nodes[edge[1]].get("datasets", None) is None:
            undefined_edges.append(edge)
        else:
            measurable_edges.append(edge)
    if verbose:
        print(
            print_prefix
            + "%d undefined edges of %d edges (%d are potentially measurable)"
            % (len(undefined_edges), len(taxonomy_graph.edges), len(measurable_edges))
        )

    # Check if the graph contains the same dataset in two nodes that are on the
    # same dependency path

    # Get nodes without outgoing connections
    base_nodes = [
        node for node, out_degree in taxonomy_graph.out_degree() if out_degree == 0
    ]

    def recursive_explore(node_path, dataset_list):
        """
        Given a node path and a list of datasets already assigned, checks if the
        incoming edges contain any of these datasets, if thats the case, it
        throws an error.
        For each incoming edge the function calls itself with the updated dataset
        and node path list. This is repeated until the root of the graph is found,
        which has no incoming edges.
        This works because taxonomies are rather small because they should be
        easily understood by humans.
        """
        # Get the node to analyze, the last from the given path
        node = node_path[-1]
        for edge in taxonomy_graph.in_edges(node):
            if node != edge[1]:
                # We don't care on outgoing edges from the analyzed node.
                continue
            else:
                # Get list of datasets used here
                dataset_list_aux = taxonomy_graph.nodes[edge[0]].get("datasets", [])
                for dataset in dataset_list_aux:
                    if dataset in dataset_list:
                        print(print_prefix + "Error in path : ")
                        for node in node_path:
                            print(print_prefix + "\t%s" % node_path)
                        raise ValueError(
                            "Detected downstream dataset sharing in node %s with %s on dataset %s"
                            % (node, edge[0], dataset)
                        )
                # Go deeper
                recursive_explore(
                    node_path + [edge[0]], dataset_list + dataset_list_aux
                )
        return

    # For each node, go up and make sure no dataset is shared among its paths up
    for node in base_nodes:
        # Explore path
        recursive_explore([node], taxonomy_graph.nodes[node].get("datasets", []))

    # All ok, return graph
    if return_all:
        return taxonomy_graph, labels_graph, undefined_edges, measurable_edges
    else:
        return taxonomy_graph


def get_taxonomy_datasets_per_node(taxonomy_graph: nx.classes.digraph.DiGraph) -> dict:
    """
    Returns the lists of all datasets assigned to each node
    """
    dataset_correspondency = dict()
    for node in taxonomy_graph.nodes:
        datasets = taxonomy_graph.nodes[node].get("datasets", None)
        if datasets is not None:
            dataset_correspondency[node] = datasets
    return dataset_correspondency


def get_taxonomy_datasets(taxonomy_graph: nx.classes.digraph.DiGraph) -> List:
    """
    Gets a list of unique datasets to be used in the given taxonomy.
    """

    dataset_correspondency = get_taxonomy_datasets_per_node(taxonomy_graph)

    datasets_list = list()
    for val in dataset_correspondency.values():
        for dataset in val:
            if dataset not in datasets_list:
                datasets_list.append(dataset)

    return datasets_list


def inintialize_helm_data():
    global models_config

    if models_config is None:
        print("Initializing data, please wait...")
        # This config file contains data for each of the models that HELM tested (and potentially more)
        models_config_path = os.environ.get(
            "MODELS_CONFIG_PATH", os.path.join(current_dir, "config", "models.json")
        )
        with open(models_config_path) as f:
            models_config = json.load(f)


def filter_for_full_samples(samples_dict: dict, model_creator: str = "") -> dict:
    """
    Given a samples dictionary, containing datasets and the corresponding tested
    models, filters all models that were not tested on ALL the datasets.
    """
    global models_config

    # If not initialized
    inintialize_helm_data()

    # Keep only the models that were tested on all datasets
    included_dataset_count = dict()
    for dataset in samples_dict.keys():
        for model in samples_dict[dataset].keys():
            if model not in included_dataset_count.keys():
                included_dataset_count[model] = 1
            else:
                included_dataset_count[model] += 1
    # Get the models included in all datasets
    use_models = [
        model
        for model, count in included_dataset_count.items()
        if count == len(samples_dict.keys())
    ]

    if len(model_creator) > 0:
        keep_list = list()
        creators_added = list()
        for model in use_models:
            this_cfg = models_config.get(model, None)
            keep = True

            if model_creator == "unique":
                # Check if there is a model of this family in the list
                for aux_model in use_models:
                    aux_cfg = models_config.get(aux_model, None)
                    if this_cfg["creator"] == aux_cfg["creator"] and aux_model != model:
                        if this_cfg["parameters"] < aux_cfg["parameters"]:
                            # keep the one with more parameters
                            keep = False
                            break
                        elif this_cfg["parameters"] == aux_cfg["parameters"]:
                            # Keep only the first we find
                            if this_cfg["creator"] in creators_added:
                                keep = False
                                break
            else:
                # The argument is the name of the family to keep
                if model_creator != this_cfg["creator"]:
                    keep = False

            if keep:
                keep_list.append(model)
                creators_added.append(this_cfg["creator"])
        use_models = keep_list

    use_models.sort()
    samples_fullytested_dict = dict()
    for dataset in samples_dict.keys():
        filtered_dict = {
            k: v for k, v in samples_dict[dataset].items() if k in use_models
        }
        # Also sort
        samples_fullytested_dict[dataset] = dict(sorted(filtered_dict.items()))
    # just check
    for dataset in samples_fullytested_dict.keys():
        assert len(samples_fullytested_dict[dataset].keys()) == len(use_models)

    return samples_fullytested_dict


def get_taxonomy_datasets_metrics_dataframe(samples_dict: dict) -> pd.DataFrame:
    """
    Receives a filtered sample dictionary (only with fully tested models) and
    creates a dataframe containing the taxonomy metrics for each dataset and model
    """

    # Matrix of [nodes x models]
    metrics_data_matrix = np.zeros(
        (
            len(samples_dict.keys()),
            len(samples_dict[list(samples_dict.keys())[0]].keys()),
        )
    )
    metrics_count_matrix = np.zeros_like(metrics_data_matrix)
    for idx, key in enumerate(samples_dict.keys()):
        metrics_data_matrix[idx, :] += list(samples_dict[key].values())
        metrics_count_matrix[idx, :] += 1
    metrics_count_matrix[metrics_count_matrix == 0] = 1  # Just to avoid NaNs
    # average
    metrics_data_matrix /= metrics_count_matrix

    # Create dataframe
    metric_data_df = pd.DataFrame(
        metrics_data_matrix.T,
        index=list(samples_dict[list(samples_dict.keys())[0]].keys()),
        columns=list(samples_dict.keys()),
    )

    return metric_data_df


def get_taxonomy_datasets_node_dataframe(
    samples_dict: dict,
    taxonomy_graph: nx.classes.digraph.DiGraph,
    verbose: bool = False,
    print_prefix: str = "",
) -> pd.DataFrame:
    """
    Receives a filtered sample dictionary (only with fully tested models) and
    the taxonomy graph and creates a dataframe containing the taxonomy metrics
    for each taxonomy node and model.
    """

    # Get models names
    use_models = list(samples_dict.values())[0]

    # Matrix of [nodes x models]
    data_matrix = np.zeros((len(taxonomy_graph.nodes), len(use_models)))
    count_matrix = np.zeros_like(data_matrix)
    node_names = list(taxonomy_graph.nodes)
    for idx, node in enumerate(node_names):
        node_dataset_list = taxonomy_graph.nodes[node].get("datasets", None)
        if node_dataset_list is None:
            if verbose:
                print(
                    print_prefix
                    + "No dataset with fully tested models for node : %s" % node
                )

        else:
            # get the datasets data
            for dataset in taxonomy_graph.nodes[node]["datasets"]:
                values_dict = samples_dict.get(dataset, None)
                # Now fill matrix, data is already sorted
                if values_dict is None:
                    if verbose:
                        print(
                            print_prefix + "No values found for dataset : %s" % dataset
                        )
                else:
                    data_matrix[idx, :] += list(values_dict.values())
                    count_matrix[idx, :] += 1
    # average
    count_matrix[count_matrix == 0] = 1  # To avoid NaNs
    data_matrix /= count_matrix

    data_df = pd.DataFrame(data_matrix.T, index=use_models, columns=node_names)
    return data_df


def get_model_graph(taxonomy_graph, samples_dict, target_model):
    """
    Given a taxonomy graph and the nodes data, extract the scores for each node
    for the requested model.
    """
    model_graph = nx.DiGraph(name=f"{taxonomy_graph.name}_{target_model}")
    for edge in taxonomy_graph.edges:
        model_graph.add_edge(edge[0], edge[1])

    attributes = dict()
    for node in model_graph.nodes:
        scores = list()
        if node == "root_c":
            continue
        all_datasets = list(taxonomy_graph.nodes[node]["datasets"])
        all_datasets.sort()
        for dataset in all_datasets:
            # Get this dataset
            this_dataset = samples_dict.get(dataset, None)
            if this_dataset is not None:
                # Keep only the selected model
                this_score = this_dataset.get(target_model, None)
                if this_score is not None:
                    scores.append(this_score)
        if len(scores) == 0:
            scores = [np.nan]
        attributes[node] = {
            "names": all_datasets,
            "values": scores,
            "median": np.median(scores),
            "avg": np.mean(scores),
            "max": np.max(scores),
            "min": np.min(scores),
        }

    nx.set_node_attributes(model_graph, attributes, "scores")

    return model_graph
