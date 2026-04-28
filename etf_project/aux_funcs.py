"""
aux_funcs.py

A collection of static functions that would distract the user from the intent of the python notebook.

Functions defined:
- extract_node_data : grabs attributes and the first 10 char (head)
input: Beautiful Soup Tag
output: Dictionary

- build_tree_data: maps the hierarchy of the DOM (Domain Object Model)
input: Beautiful Soup Tag
output: Recursive list/graph

- render_dom_tree: converts the data into a visual tree
input: Recursive/graph list
output: Plotly Figure
"""

import logging
from bs4 import BeautifulSoup, Tag

LOGGER: Final[logging.Logger] = logging.getLogger(__name__)

def extract_node_data(node:Tag, head_length:int=10) -> dict:
    """
    extract metadata from a single HTML tag.
    """

    head_text = node.get_text(strip=True)[:head_length] if node.string else ""

    return {
        "tag": node.name,
        "id": node.get('id', ''),
        "classes": ".".join(node.get('class', [])),
        "content_head": text_content,
        "full_label": f"<{node.name=}> class:{node.get('class', '')}"
    }


def build_tree_data(node: BeautifulSoup | Tag, depth:int=0, max_depth:int=3) -> dict:
    """
    build a nested dictionary of the DOM structure with metadata
    """
    if depth > max_depth:
        return None

    node_name = node.name if node.name else "[DOCUMENT_ROOT]"
    
    node = {
        "name": f"{node_name} | {node.get('id', '')}",
        "data": extract_node_data(node) if node.name else {},
        "children": []
        }

    for child in node.find_all(recursive=False):
        child_map = map_dom_to_dict(child, depth + 1, max_depth)
        if child_map:
            node["children"].append(child_map)

    return node
