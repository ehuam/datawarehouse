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

LOGGER = logging.getLogger(__name__)

def extract_node_data(node:Tag, head_length:int=10, boxover_pattern:str=None) -> dict:
    """
    extract metadata from a single HTML tag.
    """
    raw_text = node.get_text(strip=True)

    node_data_dict = {
        "tag": node.name,
        "id": node.get('id', ''),
        "classes": ".".join(node.get('class', [])),
        "href": node.get('href'),
        "content_head": raw_text[:head_length] if raw_text else None,
        "full_label": f"<{node.name}> class:{node.get('class', '')}",
    }

    match_value = node.get(boxover_pattern) if boxover_pattern else None

    if match_value:
        node_data_dict["boxover_match"] = match_value

    no_empty_kv_pairs = {k: v for k,v in node_data_dict.items() if v}
        
    return no_empty_kv_pairs


def build_tree_data(
        node: BeautifulSoup | Tag,
        depth:int=0,
        max_depth:int=10,
        tag_pattern = None,
        inventory_hash: dict = None,
) -> dict:
    """
    build a nested dictionary of the DOM structure with metadata
    """
    if depth > max_depth:
        return None

    node_classes = node.get('class', [])
    raw_keys = [node.name, node.get('id')] + node_classes
    search_keys = [key for key in raw_keys if key]
    
    node_data = extract_node_data(node, boxover_pattern=tag_pattern) if node.name else {}

    for key in search_keys:
        if inventory_hash and key in inventory_hash:
            role = inventory_hash[key]

            if role == "layout_noise":
                return None
            
            node_data["semantic_role"] = role
            break
    
    node_name = node.name if node.name else "[DOCUMENT_ROOT]"
    
    node_dict = {
        "name": f"{node_name} | {node_data.get('semantic_role', '')}",
        "data": node_data,
        "children": []
        }

    for child in node.find_all(True,recursive=False):
        child_map = build_tree_data(
                    child,
                    depth + 1,
                    max_depth,
                    tag_pattern,
                    inventory_hash)
        if child_map:
            node_dict["children"].append(child_map)

    return node_dict
