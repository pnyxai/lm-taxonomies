# Taxonomies

A taxonomy is a collection of skills organized in a hierarchical graph. It defines how basic language capabilities build upon each other and maps those capabilities to measurable benchmark tasks. Each taxonomy is described by a `.tax` file that contains two graphs:

## Structure

### Hierarchy Graph

The hierarchy graph defines how skills relate to each other, flowing upward from basic foundational skills to more complex, derived capabilities:

- **Root Node** (`root_c`): Represents general intelligence—not directly measurable but serves as the apex of the hierarchy
- **Leaf Nodes**: Basic foundational skills with no incoming edges (most primitive capabilities)
- **Intermediate Nodes**: Skills that depend on and build upon other skills
- **Direction**: Edges point upward from simpler to more complex skills (e.g., `leaf_skill -> intermediate_skill -> root_c`)

### Labeling Graph

The labeling graph connects skills to measurable benchmark tasks:

- **Nodes**: Skill nodes from the hierarchy graph
- **Edges**: Point from skills to benchmark tasks (e.g., `skill -> benchmark_task_01`)
- **Benchmarks**: Task names typically correspond to [`lm-eval`](https://github.com/EleutherAI/lm-evaluation-harness) tasks or other standard datasets

## Example: Baby Steps Taxonomy (`babisteps_v0-1`)

The **Baby Steps** taxonomy measures the bare minimum language capabilities a model should have. It focuses on foundational abilities like ordering, tracking, and spatial reasoning.

### Hierarchy Graph Visualization

```
                            root_c
                              |
                    __________|__________
                   |           |         |
            path_finding   size_order  time_tracking
                /  |  \        |          /  \
               /   |   \       |         /    \
           listing |    \      |        /      \
            |      |     \     |       /        \
            |   spatial_  \    |      /      complex_
            |   order      \   |     /       tracking
            |      |        \  |    /         /
            |      |         \ |   /         /
            |______|__________ immediate_order
                    |              |
                    |______________|
                           |
                    simple_tracking
```

### Hierarchy Graph Structure (Text)

```
Leaf Skills (no incoming edges):
├── size_order
├── spatial_order
├── temporal_order
├── listing
└── complex_tracking

Intermediate Skills:
├── immediate_order (depends on: size_order, spatial_order, temporal_order)
├── simple_tracking (depends on: listing, complex_tracking)
├── path_finding (depends on: listing, spatial_order, temporal_order)
└── time_tracking (depends on: temporal_order, complex_tracking)

Root:
└── root_c (general intelligence)
```

## Use Cases

1. **Model Evaluation**: Run benchmark tasks and evaluate model performance on each skill level
2. **Capability Analysis**: Understand which foundational skills a model lacks
3. **Taxonomy Validation**: Verify the taxonomy structure makes sense against benchmark results
4. **Performance Profiling**: Create model profiles showing strengths and weaknesses across the taxonomy

## Available Taxonomies

This folder contains multiple taxonomies for different aspects of language model evaluation:

- **`babisteps_v0-1.tax`** - Foundational language capabilities (ordering, tracking, pathfinding)
- **`coding_and_structured_language_v0.tax`** - Code generation and structured reasoning
- **`foundational_knowledge_v0.tax`** - General knowledge and facts
- **`reasoning_and_logic_v0.tax`** - Logical reasoning and inference
- **`social_and_ethical_v0.tax`** - Social understanding and ethical reasoning
- **`tool_and_instruction_compliance_v0.tax`** - Tool use and instruction following
- **`pnyx_leaderboard_v3.tax`** - Comprehensive taxonomy for the PNYX leaderboard
- **`pnyx_categories_v2.tax`** - Category-based taxonomy structure
- **`liveness_v0-2.tax`** - Liveness and state management capabilities
