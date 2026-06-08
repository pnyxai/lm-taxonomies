import pytest
import networkx as nx

from lm_taxonomies.utils import (
    load_taxonomy,
    get_taxonomy_node_prompt_blocks,
    get_taxonomy_hierarchy_prompt_blocks,
    NODE_DESCRIPTION_TEMPLATE,
)

TAXONOMY_PATH = "taxonomies/general_skills_v2-1-full.tax"


@pytest.fixture
def taxonomy_graph():
    return load_taxonomy(TAXONOMY_PATH)


class TestGetTaxonomyNodePromptBlocks:
    def test_returns_dict(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        assert isinstance(result, dict)

    def test_excludes_root_c(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        assert "root_c" not in result

    def test_contains_all_nodes(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        expected_nodes = [n for n in taxonomy_graph.nodes if n != "root_c"]
        assert len(result) == len(expected_nodes)
        for node in expected_nodes:
            assert node in result

    def test_block_format(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        sample_key = list(result.keys())[0]
        block = result[sample_key]
        assert "SKILL:" in block
        assert "DESCRIPTION:" in block
        assert "REQUIRES:" in block
        assert "ENABLES:" in block

    def test_replaces_underscores(self, taxonomy_graph):
        result_original = get_taxonomy_node_prompt_blocks(taxonomy_graph, replace_underscores=False)
        result_replaced = get_taxonomy_node_prompt_blocks(taxonomy_graph, replace_underscores=True)

        # Dict keys should remain the same
        assert list(result_original.keys()) == list(result_replaced.keys())

        # Find a node with underscores
        node_with_underscore = [n for n in result_original.keys() if "_" in n][0]
        assert "_" in result_original[node_with_underscore].split("SKILL:")[1].split("\n")[0]
        assert " " in result_replaced[node_with_underscore].split("SKILL:")[1].split("\n")[0]
        assert "_" not in result_replaced[node_with_underscore].split("SKILL:")[1].split("\n")[0]

    def test_no_underscores_when_replaced(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph, replace_underscores=True)
        for block in result.values():
            assert "_" not in block.split("SKILL:")[1].split("\n")[0]

    def test_root_c_only_child_empty_enables(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        for node in taxonomy_graph.nodes:
            if node == "root_c":
                continue
            successors = list(taxonomy_graph.successors(node))
            if len(successors) == 1 and "root_c" in successors:
                block = result[node]
                enables_section = block.split("ENABLES:")[1].split("\n")[0].strip()
                assert enables_section == ""

    def test_requires_excludes_root_c(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        for block in result.values():
            requires_section = block.split("REQUIRES:")[1].split("ENABLES:")[0]
            assert "root_c" not in requires_section

    def test_block_uses_template(self, taxonomy_graph):
        result = get_taxonomy_node_prompt_blocks(taxonomy_graph)
        sample_key = list(result.keys())[0]
        block = result[sample_key]
        template_lines = NODE_DESCRIPTION_TEMPLATE.split("\n")
        assert block.startswith(f"SKILL:")
        assert "\nDESCRIPTION:\n" in block
        assert "\nREQUIRES:\n" in block
        assert "\nENABLES:" in block


class TestGetTaxonomyHierarchyPromptBlocks:
    def test_returns_string(self, taxonomy_graph):
        result = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph)
        assert isinstance(result, str)

    def test_contains_separators(self, taxonomy_graph):
        result = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph)
        separator = "\n---\n"
        assert separator in result

    def test_contains_all_blocks(self, taxonomy_graph):
        result = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph)
        block_count = len(result.split("\n---\n"))
        expected_count = sum(1 for n in taxonomy_graph.nodes if n != "root_c")
        assert block_count == expected_count

    def test_top_down_ordering(self, taxonomy_graph):
        result = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph, direction="top-down")
        blocks = result.split("\n---\n")
        first_block = blocks[0]
        first_skill = first_block.split("\n")[0].replace("SKILL: ", "")
        # First block should be adjacent to root_c (depth 1)
        preds = list(taxonomy_graph.predecessors(first_skill))
        assert preds == ["root_c"] or (len(preds) == 0 and first_skill == taxonomy_graph.nodes.__iter__().__next__())

    def test_bottom_up_ordering(self, taxonomy_graph):
        result = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph, direction="bottom-up")
        blocks = result.split("\n---\n")
        last_block = blocks[-1]
        last_skill = last_block.split("\n")[0].replace("SKILL: ", "")
        # Last block should be a shallow node (depth 1, adjacent to root_c)
        preds = [p for p in taxonomy_graph.predecessors(last_skill) if p != "root_c"]
        assert len(preds) == 0  # No non-root_c predecessors = depth 1

    def test_replaces_underscores_in_hierarchy(self, taxonomy_graph):
        result_original = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph, replace_underscores=False)
        result_replaced = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph, replace_underscores=True)

        # Original should have underscores
        assert "_" in result_original

        # Replaced should have spaces instead
        for block in result_replaced.split("\n---\n"):
            skill_line = block.split("\n")[0]
            assert "_" not in skill_line

    def test_default_direction_is_bottom_up(self, taxonomy_graph):
        result_default = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph)
        result_explicit = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph, direction="bottom-up")
        assert result_default == result_explicit

    def test_contains_skill_names(self, taxonomy_graph):
        result = get_taxonomy_hierarchy_prompt_blocks(taxonomy_graph)
        for node in taxonomy_graph.nodes:
            if node == "root_c":
                continue
            assert f"SKILL: {node}" in result
