# lm_taxonomies Repository Guide for AI Agents

This document describes the structure and functionalities of the `lm_taxonomies` repository to help AI tools understand and navigate the codebase.

## Repository Structure

```
pnyx-lm-taxonomies/
├── lm_taxonomies/          # Main Python package
│   ├── __init__.py         # Package initialization
│   ├── helm_data.py        # HELM benchmark data utilities
│   ├── metrics.py          # Taxonomy metrics calculations
│   ├── utils.py            # Core taxonomy utilities
│   └── config/             # Configuration files (auto-included)
│       ├── helm_tests.json # HELM dataset to test mapping
│       └── models.json     # Model metadata
├── scripts/                # Standalone scripts using the package
│   ├── taxonomy_analyzer/  # Taxonomy analysis tools
│   │   ├── compile_custom_dataset.py
│   │   ├── test_taxonomy.py
│   │   ├── get_helm_data.sh
│   │   └── README.md
│   └── model_profiler/     # Model profiling tools
│       └── create_model_graph_score.py
├── taxonomies/             # Taxonomy definition files
│   ├── babisteps_v0-1.tax  # Foundational language capabilities
│   ├── coding_and_structured_language_v0.tax
│   ├── foundational_knowledge_v0.tax
│   ├── reasoning_and_logic_v0.tax
│   ├── social_and_ethical_v0.tax
│   ├── tool_and_instruction_compliance_v0.tax
│   ├── liveness_v0-2.tax
│   ├── pnyx_categories_v2.tax
│   ├── pnyx_leaderboard_v3.tax
│   └── README.md           # Taxonomy format guide with examples
├── pyproject.toml          # Project configuration (uv managed)
├── README.md               # User-facing documentation
└── AGENTS.md              # This file
```

## Package: lm_taxonomies

The `lm_taxonomies` package provides core functionality for working with language model taxonomies and HELM benchmark data.

### Module: helm_data.py

Utilities for reading and processing HELM (Holistic Evaluation of Language Models) benchmark results.

**Key Functions:**

- `get_model_name_from_test_name(test_name: str) -> str`
  - Extracts model name from HELM test result name
  - Parses the model identifier from the test name string

- `read_helm_data(helm_data_path: str, datasets_list: List[str], verbose: bool = False, print_prefix: str = "", current_dict: dict = {}, parameters_range: Tuple[float, float] = [0, 0]) -> dict`
  - Loads HELM metrics for specified datasets
  - Returns dict with dataset keys and model metrics
  - Supports incremental loading with `current_dict` parameter
  - Respects `HELM_TESTS_CONFIG_PATH` and `MODELS_CONFIG_PATH` environment variables

- `split_helm_result_folder_name(folder_name: str) -> tuple`
  - Parses HELM result folder naming convention
  - Extracts dataset, method, and model information

- `retrieve_helm_model_result_on_prompt_by_id(prompt_id, dataset, metric_name, model, path_to_results, compilation=None, method=None) -> dict`
  - Retrieves metric results for specific prompt and model combination
  - Supports custom compilations and methods

- `retrieve_helm_prompt_by_id(prompt_id, dataset, model, path_to_results, compilation=None, method=None) -> dict`
  - Retrieves prompt data for a specific prompt ID
  - Useful for analyzing individual test cases

- `get_all_test_prompts_by_id(path_to_results) -> dict`
  - Retrieves all prompts organized by ID
  - Comprehensive prompt enumeration

**Configuration:**
- Loads from `config/helm_tests.json`: Maps taxonomy dataset strings to HELM dataset results
- Loads from `config/models.json`: Contains model metadata

### Module: utils.py

Core utilities for taxonomy manipulation, analysis, and evaluation.

**Key Functions:**

- `load_taxonomy(file_path: str, return_all: List = False, verbose: bool = False, print_prefix: str = "") -> nx.DiGraph`
  - Loads taxonomy in graphviz format (two graphs: taxonomy + labeling)
  - Returns NetworkX DiGraph with datasets attached to nodes
  - Validates proper file structure and naming convention
  - Identifies measurable edges (edges with defined datasets on both nodes)

- `get_taxonomy_datasets_per_node(taxonomy_graph: nx.DiGraph) -> dict`
  - Returns dict mapping each node to its associated datasets
  - Extracts dataset correspondency from taxonomy structure

- `get_taxonomy_datasets(taxonomy_graph: nx.DiGraph, allow_duplicates=True) -> List`
  - Returns complete list of all datasets in taxonomy
  - Option to remove duplicates

- `filter_for_full_samples(samples_dict: dict, model_creator: str = "") -> dict`
  - Filters HELM samples to include only complete model results
  - Supports filtering by model creator
  - Ensures all models have data for all datasets

- `get_taxonomy_datasets_metrics_dataframe(samples_dict: dict) -> pd.DataFrame`
  - Converts samples dictionary to DataFrame
  - Rows: datasets, Columns: models
  - Cells: metric values for model on dataset

- `get_taxonomy_datasets_node_dataframe(samples_dict: dict, taxonomy_graph: nx.DiGraph, node_name: str) -> pd.DataFrame`
  - Returns DataFrame for metrics of specific taxonomy node
  - Only includes datasets associated with that node

- `extract_edge_metric(node_name, taxonomy_graph, data_matrix, method_name) -> dict`
  - Extracts metric value for edge from parent to node
  - Uses various distance/correlation methods
  - Returns metric value and related metadata

- `get_taxonomy_nodes_metric(samples_dict: dict, taxonomy_graph: nx.DiGraph, method_name: str, verbose: bool = False) -> dict`
  - Calculates specified metric for all nodes
  - Supports methods: "euclidean_distance", "pearson", "spearman", "cosine", "hamming", "jensen_shannon"
  - Returns node-indexed metric dictionary

- `get_taxonomy_per_edge_metric(samples_dict: dict, taxonomy_graph: nx.DiGraph, method_name: str, verbose: bool = False) -> dict`
  - Calculates metrics for all edges in taxonomy
  - Returns edge-indexed metric dictionary
  - Comprehensive edge evaluation

- `get_model_graph(taxonomy_graph, samples_dict, target_model) -> nx.DiGraph`
  - Generates graph for specific model performance
  - Useful for model-specific analysis

**Dataset Handling:**
- Loads from `config/models.json`: Model metadata required for filtering and categorization

### Module: metrics.py

Statistical metrics for analyzing relationships between taxonomy nodes.

**Key Functions:**

- `apply_to_pairs(df: pd.DataFrame, func: callable) -> pd.DataFrame`
  - Applies a function to all pairs of DataFrame columns
  - Creates symmetric matrix of results (rows and columns are same)
  - Used with correlation and association metrics

- `remove_nans(a: np.array, b: np.array) -> Tuple[np.array, np.array]`
  - Utility to align arrays by removing NaN-containing positions
  - Ensures valid pair-wise comparisons

- `node_pair_mutual_info_regression(a: np.array, b: np.array) -> float`
  - Calculates mutual information between two node performance vectors
  - Uses scikit-learn's mutual_info_regression
  - Returns NaN if either vector is all zeros
  - Listed in `permutation_methods`

- `node_pair_success_association(a: np.array, b: np.array) -> float`
  - Calculates association between nodes based on success patterns
  - Returns proportion where B has higher value than A
  - Bidirectional metric
  - Listed in `permutation_methods`

**Metric Categories:**
- Methods in `permutation_methods`: Applied to all node pairs (permutations)
- Other methods: Applied to triangular elements only (optimize computation)

## Folder: taxonomies

Contains taxonomy definition files (`.tax` files) that define skill hierarchies and their mappings to benchmark tasks.

### Taxonomy File Format

Each `.tax` file contains two graphs described in Graphviz-like syntax:

1. **Hierarchy Graph** (unnamed graph block): Defines parent-child relationships between skills
   - Edge direction: `child_skill -> parent_skill` (flows upward from basic to complex)
   - Root node: `root_c` represents general intelligence (non-measurable)
   - All skills form a directed acyclic graph (DAG) flowing to the root

2. **Labeling Graph** (suffixed with `_labeling`): Maps skills to benchmark tasks
   - Edge direction: `skill -> benchmark_task_name`
   - Task names typically correspond to lm-eval tasks or HELM datasets
   - Enables empirical evaluation of taxonomy nodes

### Available Taxonomies

- **`babisteps_v0-1.tax`** - Foundational language capabilities (ordering, tracking, pathfinding)
- **`coding_and_structured_language_v0.tax`** - Code generation and structured reasoning
- **`foundational_knowledge_v0.tax`** - General knowledge and facts
- **`reasoning_and_logic_v0.tax`** - Logical reasoning and inference
- **`social_and_ethical_v0.tax`** - Social understanding and ethical reasoning
- **`tool_and_instruction_compliance_v0.tax`** - Tool use and instruction following
- **`liveness_v0-2.tax`** - Liveness and state management capabilities
- **`pnyx_categories_v2.tax`** - Category-based taxonomy structure
- **`pnyx_leaderboard_v3.tax`** - Comprehensive taxonomy for the PNYX leaderboard

### Documentation

See `taxonomies/README.md` for detailed format guide, concrete examples using the Baby Steps taxonomy, and ASCII graph visualizations.

## Scripts

Standalone Python scripts that use the `lm_taxonomies` package.

### scripts/taxonomy_analyzer/

**compile_custom_dataset.py**
- Purpose: Compiles HELM dataset instance results into new dataset splits
- Usage: `python scripts/taxonomy_analyzer/compile_custom_dataset.py --compilation <file> --data <path> --output <path>`
- Arguments:
  - `--compilation, -c`: Path to compilation definition file (required)
  - `--data, -d`: Path to HELM data (optional)
  - `--output, -o`: Output path for results (required)
  - `--ignore_wrong_splits, -is`: Whether to continue on split mismatches (default: True)
  - `--verbosity, -v`: Logging verbosity level

**test_taxonomy.py**
- Purpose: Tests taxonomy fitness against dataset test collection
- Main functionality: Evaluates taxonomy structure against HELM model results
- Arguments:
  - `--taxonomy, -t`: Path to taxonomy file (required)
  - `--data, -d`: Paths to HELM data (can specify multiple)
  - `--output, -o`: Output path for graphs (required)
  - `--models, -m`: Comma-separated list of models (required)

**get_helm_data.sh**
- Purpose: Shell script to fetch HELM benchmark data
- Supports automated data retrieval

### scripts/model_profiler/

**create_model_graph_score.py**
- Purpose: Creates model performance graphs and profiling scores
- Generates graphs showing model performance across taxonomy nodes
- Integrates with `helm_data` and `utils` modules for comprehensive profiling
- Arguments:
  - `--taxonomy, -t`: Path to taxonomy file
  - `--data, -d`: Paths to HELM data
  - `--output, -o`: Output path for graphs
  - `--models, -m`: Comma-separated list of models

## Configuration Files

### config/helm_tests.json

Maps taxonomy dataset strings to HELM benchmark test configurations.

**Structure:**
```json
{
  "DatasetName": [
    {
      "name": "helm_dataset_name,method=...",
      "metric": "exact_match",
      "suffix": "",
      "field": "mean",
      "split": "test"
    }
  ]
}
```

- `name`: Partial HELM result name (before model identifier)
- `metric`: Type of metric from stats.json
- `suffix`: Test-specific suffix ("" for any, "---" for none)
- `field`: Metric field to extract (usually "mean")
- `split`: Dataset split ("test" or "validation")

### config/models.json

Contains metadata for models tested in HELM benchmarks.

**Usage:**
- Accessed by `helm_data.py` and `utils.py`
- Used for filtering and categorizing model results
- Supports model creator filtering

## Data Flow

1. **Load Taxonomy**: `load_taxonomy()` → NetworkX DiGraph with dataset metadata
2. **Load HELM Data**: `read_helm_data()` → Dictionary of model metrics per dataset
3. **Align Data**: `filter_for_full_samples()` → Ensure all models have all datasets
4. **Calculate Metrics**: `get_taxonomy_nodes_metric()` → Evaluate each node
5. **Generate Output**: Scripts produce graphs and analysis results

## Key Concepts

### Taxonomy Structure
- Represented as directed acyclic graph (DAG) using NetworkX
- Two components: taxonomy graph and labeling graph
- Nodes represent concepts; edges represent relationships
- Datasets attached to nodes for empirical evaluation

### Datasets
- String identifiers linking taxonomy to HELM benchmark results
- Each node can have multiple datasets
- Measurable edges: both source and target have defined datasets
- Configuration-driven mapping from taxonomy strings to HELM tests

### Metrics
- **Node Metrics**: How well a model performs on a specific concept
- **Edge Metrics**: Relationship quality between parent and child concepts
- **Methods**: Euclidean distance, correlation, information measures, etc.

### Model Profiling
- Per-model performance analysis across taxonomy
- Graph generation for visualization
- Scoring systems for model capability assessment

## Environment Variables

- `HELM_TESTS_CONFIG_PATH`: Override default `config/helm_tests.json` location
- `MODELS_CONFIG_PATH`: Override default `config/models.json` location

## Dependencies

- **networkx**: Graph structure and algorithms
- **pandas**: Data manipulation and analysis
- **numpy**: Numerical computations
- **matplotlib**: Graph visualization
- **tqdm**: Progress bars
- **scikit-learn**: Machine learning utilities (mutual information, etc.)

## Type Hints

The codebase uses Python type hints for clarity:
- `nx.DiGraph`: NetworkX directed graph
- `pd.DataFrame`: Pandas data frame
- `np.array`: NumPy array
- Standard Python types documented in function signatures
