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
    head_text = raw_text[:head_length] if raw_text else ""

    node_data_dict = {
        "tag": node.name,
        "id": node.get('id', ''),
        "classes": ".".join(node.get('class', [])),
        "href": node.get('href', ''),
        "content_head": head_text,
        "full_label": f"<{node.name}> class:{node.get('class', '')}"
    }

    match_value = node.get(boxover_pattern) if boxover_pattern else None

    if match_value:
        node_data_dict["boxover_match"] = match_value

    return node_data_dict


def build_tree_data(
        node: BeautifulSoup | Tag,
        depth:int=0,
        max_depth:int=3,
        tag_pattern = None,
        ignore_list:set = None,
) -> dict:
    """
    build a nested dictionary of the DOM structure with metadata
    """
    if depth > max_depth:
        return None

    if ignore_list and node.name in ignore_list:
        return None
        

    node_name = node.name if node.name else "[DOCUMENT_ROOT]"
    
    node_dict = {
        "name": f"{node_name} | {node.get('id', '')}",
        "data": extract_node_data(node, boxover_pattern=tag_pattern) if node.name else {},
        "children": []
        }

    for child in node.find_all(True,recursive=False):
        match child:
            case Tag() as c:
                child_map = build_tree_data(
                    c,
                    depth + 1,
                    max_depth,
                    tag_pattern,
                    ignore_list)
                if child_map:
                    node_dict["children"].append(child_map)

    return node_dict
