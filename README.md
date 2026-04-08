# PNYX Taxonomy Tools Package

This repository contains a set of tools and scripts for working with language model skills taxonomies.
The skills taxonomies are a way of presenting language model's linguistic and cognitive skills in a readable and hierarchical way that reveals more than the sum of the benchmarks that compose them.

## Installation

Install the package with `uv`:

```bash
uv sync
```

This installs the `taxonomy_tools` package and all dependencies.

## Usage

### Import the Package

```python
from taxonomy_tools import helm_data, metrics, utils
```

### Available Modules

- **helm_data**: Functions for working with HELM benchmark data
- **metrics**: Calculation and analysis of taxonomy metrics
- **utils**: Utility functions for taxonomy manipulation and analysis

Configuration files are stored in `taxonomy_tools/config/`.

## Scripts

Scripts that use the package are in the `scripts/` directory:

- [**taxonomy_analyzer**](./scripts/taxonomy_analyzer/README.md): Tools for analyzing and testing taxonomies
- [**model_profiler**](./scripts/model_profiler/README.md): Model profiling utilities


## Development

Install dev dependencies:

```bash
uv sync --all-extras
```

This includes `ipykernel` for Jupyter notebook support.

## Requirements

- Python 3.13+

## Sample Taxonomies

Several taxonomies are included for reference, Please refer to the section [README](./taxonomies/README.md).