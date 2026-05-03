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

def extract_scrape_plan(
        dom_tree,
        type_config: dict,
        site_config: dict
        ) -> list[dict]:
    """
    using the pagination tags to extract the URL list for scraping
    """
    base_url = site_config['base_url']
    string_pattern = type_config['string_pattern']
    target_branch = 'PAGINATION | select | pagination_drop ' # this is done when mapping landing page

    drop_branch = aux_funcs.find_branch_by_name(dom_tree, target_branch) # dropdown for pagination

    if not drop_branch:
        LOGGER.warning(f"could not find pagination drop label in {type_config['name']}")
        return []

    scrape_urls = []
    unwanted_chars = ["/"]

    for idx, option in enumerate(drop_branch.get('children', [])):
        data = option.get('data', {})
        r_value = data.get('value')
        label = data.get('content_head')

        if r_value:
            target_path = f"{string_pattern}{r_value}"
            full_url = urljoin(base_url, target_path)

            clean_label = label
            for char in unwanted_chars:
                clean_label = clean_label.replace(char, "")

        scrape_urls.append({
            "index": idx,
            "url": full_url,
            "label": clean_label.strip(),
            "offset": r_value,
            })


    LOGGER.info(f"extracted {len(scrape_urls)} URLS using pagination label for '{type_config['name']}'")
    return scrape_urls
        
        
