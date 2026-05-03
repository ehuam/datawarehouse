import logging
from urllib.parse import urljoin
from aux_funcs import find_branch_by_name

LOGGER = logging.getLogger(__name__)

def map_landing_page(
        webpage_path: Path,
        type_config: dict,
        functional_areas:dict,
        inv_hash: dict,
        max_depth: int = 12,
)-> dict:
    """
    given a webpage, it will add structural labels
    """
    html_blob = webpage_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_blob, "html.parser")

    dom_tree_data = {
        "name": type_config["name"],
        "data": {
            "tag": "synthetic",
            "semantic_role": "page_root",
            },
        "children": [],
    }

    for label, element_id in functional_areas.items():
        found_node = soup.find(id=element_id)
        if found_node:
            branch = aux_funcs.build_tree_data(
                found_node,
                max_depth=max_depth,
                inventory_hash=inv_hash,
                )
            if branch:
                branch["name"] = f"{label} | {branch['name']}"
                dom_tree_data["children"].append(branch)

    LOGGER.info(f"Mapped DOM tree for '{type_config['name']}' at max depth {max_depth}")

    return dom_tree_data

    
