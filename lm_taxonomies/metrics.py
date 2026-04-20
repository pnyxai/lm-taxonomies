from sklearn.feature_selection import mutual_info_regression
from scipy.stats import spearmanr, kendalltau

import collections
import numpy as np
import itertools
import pandas as pd
from typing import Tuple
import networkx as nx


# All methods will be calculated on every node combination (using function
# "apply_to_pairs") if they are in this list, otherwise it means that they will
# only be calculated on the triangular elements, not on the diagonal or the
# mirrored pairs.
permutation_methods = ["mutual_information", "success_association"]


def apply_to_pairs(df, func):
    """Applies a function to all combinations of pairs of columns in a DataFrame.

    Args:
    df: The pandas DataFrame.
    func: The function to apply to each pair of columns.

    Returns:
    A DataFrame containing the results of applying the function to each pair.
    """

    columns = df.columns.values
    num_cols = len(columns)
    columns_idxs = [i for i in range(num_cols)]
    pairs = itertools.permutations(columns_idxs, 2)

    metric_mat = np.zeros((num_cols, num_cols))
    # Triang
    for col1, col2 in pairs:
        result = func(df[columns[col1]].values, df[columns[col2]].values)
        metric_mat[col1, col2] = result
    # Diag
    for col in columns_idxs:
        result = func(df[columns[col]].values, df[columns[col]].values)
        metric_mat[col, col] = result

    return pd.DataFrame(metric_mat, columns=df.columns.values, index=df.columns.values)


def remove_nans(a: np.array, b: np.array) -> Tuple[np.array, np.array]:
    these = 0 == (np.isnan(a) + np.isnan(b))
    a = a[these]
    b = b[these]
    return a, b


################################################################################
# Node Pair Metrics
################################################################################
# All metrics starting with "node_pair_" are meant to be used with the function
# "apply_to_pairs" or the "corr" method of a Pandas.DataFrame


def node_pair_mutual_info_regression(a: np.array, b: np.array) -> float:
    a, b = remove_nans(a, b)
    a = a.reshape(-1, 1)
    if np.sum(a) == 0 or np.sum(b) == 0:
        return np.nan
    return mutual_info_regression(a, b)[0]


def node_pair_success_association(a: np.array, b: np.array) -> float:
    """
    This metric calculates a value that reflects the association between A and B
    defined as the proportion of the total where B has a higher value than A.
    """
    a, b = remove_nans(a, b)

    # Number of A smaller than B, ignore NaNs
    num_asb = np.nan_to_num(np.sum(a <= b), 0)
    # Number of total non-NaN entries
    support = np.sum(0 == (np.isnan(a) + np.isnan(b)))

    return num_asb / support


def get_taxonomy_nodes_metric(
    data_df: pd.DataFrame,
    taxonomy_graph: nx.classes.digraph.DiGraph,
    verbose: bool = False,
    print_prefix: str = "",
    method: str = "pearson",
) -> Tuple[np.array, np.array]:
    """
    Using the taxonomy nodes data and the graph calculates a metric on pairs of
    nodes. By default it calculates the full correlations between nodes, but
    several other custom methods are available.
    The result is a metrics matrix and also a version with only values where
    valid edges are defined.
    """

    if method == "mutual_information":
        method_use = node_pair_mutual_info_regression
    elif method == "success_association":
        method_use = node_pair_success_association
    else:
        method_use = method

    # calculate metric.
    if method not in permutation_methods:
        # We abuse the pandas "corr" method here.
        metrics_matrix = data_df.corr(method=method_use)
    else:
        # Do the calculation on each permutation
        metrics_matrix = apply_to_pairs(data_df, method_use)

    # Filter metrics matrix for edges positions only
    metrics_matrix_filtered = np.zeros_like(metrics_matrix.values)
    nodes_array = np.array(taxonomy_graph.nodes())
    for edge in taxonomy_graph.edges:
        # Get adj matrix locations
        x = np.argwhere(nodes_array == edge[0])[0][0]
        y = np.argwhere(nodes_array == edge[1])[0][0]
        metric_val = metrics_matrix.values[x, y]
        if not np.isnan(metric_val):
            metrics_matrix_filtered[x, y] = metric_val
    if verbose:
        print(print_prefix + "Total edges:")
        print(print_prefix + "%d" % len(taxonomy_graph.edges))
        print(print_prefix + "Measurable edges with data:")
        print(
            print_prefix
            + "%d" % len(metrics_matrix_filtered[metrics_matrix_filtered != 0])
        )

    # Create a dictionary with metrics over the taxonomy
    graph_json = dict()
    # Get nodes without incoming connections, the most higher level abilities
    root_nodes = [
        node for node, in_degree in taxonomy_graph.in_degree() if in_degree == 0
    ]
    # Apply recursively
    for root in root_nodes:
        graph_json[root] = dict()
        graph_json[root]["nodes"] = extract_edge_metric(
            root, taxonomy_graph, metrics_matrix.values, method
        )

    return metrics_matrix, metrics_matrix_filtered, graph_json


def extract_edge_metric(node_name, taxonomy_graph, data_matrix, method_name) -> dict:
    """
    Get a node metric to its downstream nodes and return the data as dict
    """
    nodes_array = np.array(taxonomy_graph.nodes())
    node_dict = dict()
    for edge in taxonomy_graph.out_edges(node_name):
        node_dict[edge[1]] = dict()

        # Get adj matrix locations
        x = np.argwhere(nodes_array == edge[0])[0][0]
        y = np.argwhere(nodes_array == edge[1])[0][0]
        corr_val = data_matrix[x, y]
        node_dict[edge[1]][method_name] = corr_val

        # Go down
        node_dict[edge[1]]["nodes"] = extract_edge_metric(
            edge[1], taxonomy_graph, data_matrix, method_name
        )

    return node_dict


def get_taxonomy_per_edge_metric(
    taxonomy_graph: nx.classes.digraph.DiGraph,
    samples_dict: dict,
    method: str = "pearson",
    verbose: bool = False,
    print_prefix: str = "",
) -> np.array:
    """
    Calculates the taxonomy edges metric values using all possible data,
    this means that models are kept if they were tested on all datasets between
    two nodes that define an edge. The result is a metric value with
    potentially more models (data points) but the metrics of the different
    edges are calculated with different number of samples.
    The used sample dictionary is the unfiltered one.
    Returns a metrics matrix with values assigned only to valid edges.
    """

    # Calculate the metrics matrix but using all the shared models between datasets edges
    metrics_matrix_imbalanced = np.zeros(
        (len(taxonomy_graph.nodes), len(taxonomy_graph.nodes))
    )
    nodes_array = np.array(taxonomy_graph.nodes())
    for edge in taxonomy_graph.edges:
        # Get adj matrix locations
        x = np.argwhere(nodes_array == edge[0])[0][0]
        y = np.argwhere(nodes_array == edge[1])[0][0]
        # get the models shared
        datasets_0 = taxonomy_graph.nodes[edge[0]].get("datasets", [])
        datasets_1 = taxonomy_graph.nodes[edge[1]].get("datasets", [])
        models_use_0 = list()
        models_use_1 = list()
        for dataset in datasets_0:
            values_dict = samples_dict.get(dataset, None)
            # Now fill matrix, data is already sorted
            if values_dict is not None:
                models_use_0 += list(values_dict.keys())
        for dataset in datasets_1:
            values_dict = samples_dict.get(dataset, None)
            # Now fill matrix, data is already sorted
            if values_dict is not None:
                models_use_1 += list(values_dict.keys())
        # Remove not shared
        element_counts = collections.Counter(models_use_0)
        models_use_0 = list()
        for key in element_counts.keys():
            if element_counts[key] == max(list(element_counts.values())):
                models_use_0.append(key)
        element_counts = collections.Counter(models_use_1)
        models_use_1 = list()
        for key in element_counts.keys():
            if element_counts[key] == max(list(element_counts.values())):
                models_use_1.append(key)
        # keep shared between nodes
        models_here_use = list()
        for model in models_use_0:
            if model in models_use_1:
                models_here_use.append(model)
        # Now build the metrics for each node in this edge
        values_0 = np.zeros(len(models_here_use))
        values_1 = np.zeros(len(models_here_use))
        for idx, model in enumerate(models_here_use):
            count = 0
            for dataset in datasets_0:
                values_dict = samples_dict.get(dataset, None)
                if values_dict is not None:
                    values_0[idx] += values_dict[model]
                    count += 1
            if count != 0:
                values_0[idx] /= count
            count = 0
            for dataset in datasets_1:
                values_dict = samples_dict.get(dataset, None)
                if values_dict is not None:
                    values_1[idx] += values_dict[model]
                    count += 1
            if count != 0:
                values_1[idx] /= count
        if np.sum(values_0) != 0 and np.sum(values_1) != 0:
            if method == "pearson":
                metrics_matrix_imbalanced[x, y] = np.corrcoef(values_0, values_1)[1, 0]
            elif method == "spearman":
                metrics_matrix_imbalanced[x, y], _ = spearmanr(values_0, values_1)
            elif method == "kendall":
                metrics_matrix_imbalanced[x, y], _ = kendalltau(values_0, values_1)
            elif method == "mutual_information":
                metrics_matrix_imbalanced[x, y] = node_pair_mutual_info_regression(
                    values_0, values_1
                )
            elif method == "success_association":
                metrics_matrix_imbalanced[x, y] = node_pair_success_association(
                    values_0, values_1
                )
            else:
                raise ValueError("Unknown method for metric : %s" % method)
        else:
            metrics_matrix_imbalanced[x, y] = np.nan

    # Create a dictionary with metrics over the taxonomy
    graph_json = dict()
    # Get nodes without incoming connections, the most higher level abilities
    root_nodes = [
        node for node, in_degree in taxonomy_graph.in_degree() if in_degree == 0
    ]
    # Apply recursively
    for root in root_nodes:
        graph_json[root] = dict()
        graph_json[root]["nodes"] = extract_edge_metric(
            root, taxonomy_graph, metrics_matrix_imbalanced, method
        )

    return metrics_matrix_imbalanced, graph_json
