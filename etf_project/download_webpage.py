"""
Because we are running this from a notebook we need to be careful on how we are getting the scraped web page data.
What we decided to do was to have a file hold all the methods to get the web page data. it should also accept an argument
as to how many pages it should download. We do this because it takes about 1 hour to download 552 pages. Also the user may
have already downloaded the data and it should not be called again.

We have then decided to move the methods from the notebook here.
"""

import os
import time
from datetime import datetime, timedelta
import logging
from pathlib import Path
import argparse


from bs4 import BeautifulSoup

# SELENIUM SETUP
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

import aux_funcs # edgar's static methods

# config setup
import config.finviz as finviz_config

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(asctime) - %(message)s",
    )
LOGGER = logging.getLogger(__name__)

# Supported Web pages
SUPPORTED = {
    "finviz": {
        "etf": finviz_config.ETF,
        "aum": finviz_config.AUM
    }   
}

SITE_CONFIG = {
    "functional_areas": finviz_config.FUNCTIONAL_AREAS,
    "inventory_hash": finviz_config.INV_HASH,
    "base_urls": finviz_config.BASE_URL,
}



def get_args():
    parser = argparse.ArgumentParser(description="ETF Scraper for Finviz")
    parse.add_argument("--pages", type=int, default=None, help="number of pages to download default is all")
    parse.add_argument("--headless", action="store_true", help="run browser in headless mode")
    parse.add_argument("--webpage", choices=['etf', 'aum'], default='etf', help="which webpage to scrape")
    return parser.parse_args()

def create_driver(headless: bool = False)-> webDriver.Firefox:
    """
    create a firefox driver
    """
    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    return driver

# create a folder for the batch etf pages downloaded
def get_timestamp_folder(base_folder: Path) -> Path:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_folder = base_folder / f"batch_{timestamp}"
    batch_folder.mkdir(exist_ok=True)
    logger.info(f"Created batch folder: {batch_folder}")
    return batch_folder


# get the scrape plan
def extract_scrape_list_from_tree(dom_tree, webpage_name:str) -> list[dict]:
    """
    using the pagination tags to extract the URL list for scraping
    only supports finviz.
    """

    match webpage_name:
        case "etf":

        case "aum":
            webpage = "https://finviz.com/"
            string_pattern = "screener?v=191&r="
            target_branch = "PAGINATION | select | pagination_drop"
        case _ :        
            LOGGER.error(f'No URL pattern defined for {webpage_name}. Check the function implementation.')
            raiseValueError(f'no pattern defined for {webpage_name}')
    drop_branch = find_branch_by_name(dom_tree, target_branch)
        
    if not drop_branch:
        LOGGER.warning("No PAGINATION_DROP label found in tree. Check functional ares mapping")
        return []

    scrape_urls = []
    UNWANTED_CHARS = ['/']
    
    for idx, option in enumerate(drop_branch.get('children', [])):
        data = option.get('data', {})
        r_value = data.get('value')
        label = data.get('content_head')

        if r_value:
            target_path = f"{string_pattern}{r_value}"
            full_url = urljoin(webpage, target_path)

            clean_label = label
            for char in UNWANTED_CHARS:
                clean_label = clean_label.replace(char, '')


        scrape_urls.append({
            "index": idx,
            "url": full_url,
            "label": clean_label.strip() if label else r_value,
            "offset": r_value
            })
    LOGGER.info(f"extracted {len(scrape_urls)} URLs from pagination drop-down for {webpage_name}")
    return scrape_urls


# moving method from note book
# bulk download
def execute_bulk_download(driver, scrape_plan, batch_folder):
    total = len(scrape_plan)
    wait =  WebDriverWait(driver, 15)
    
    for task in scrape_plan:
        file_name = f"page_{task['index']:03d}_offset_{task['offset']}.html"
        save_path = Path(batch_folder) / file_name
        
        if save_path.exists():
            logger.info(f"skipping {task['index']} - already exists")
            continue
        try:
            logger.info(f'downloading [{task["index"]}/{total}] {task['label']}')
            driver.get(task['url'])
            
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "styled-row")))
            
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            meta_script = f"""
                var m = document.createElement('meta');
                m.name = 'scrape_metadata';
                m.content = 'label={task['index']}|offset={task['offset']}|timestamp={timestamp}';
                document.head.appendChild(m);
            """
            driver.execute_script(meta_script)
            
            save_path.write_text(driver.page_source, encoding='utf-8')
            
            # polite delay
            time.sleep(5)
        except Exception as e:
            logger.error(f"failed to download {task['label']}: {e}")
            continue
            
    logger.info(f"Bulk download complete. Files saved to {batch_folder}")

# supporting re runs
def get_latest_batch_folder(base_dir='webpages') -> Path | bool:
    """
    we want to check if a folder was recently created to avoid redownloading data.
    """
    path = Path(base_dir)
    if not path.exists():
        LOGGER.info(f'no existing data folder found at {base_dir}.')
        return False
    
    batches = [directory for directory in path.iterdir() if directory.is_dir()]
    if not batches:
        LOGGER.info(f'no existing batch folders found in {base_dir}.')
        return False
    
    latest_batch = max(batches, key=lambda d: d.stat().st_mtime)
    elapsed_time = datetime.datetime.now() - datetime.datetime.fromtimestamp(latest_batch.stat().st_mtime)
    
    if elapsed_time < timedelta(minutes=15):
        LOOGER.info(f"last batch folder {latest_batch} created {elapsted_time}; returning last")
        return latest_batch
    
def initialize_batch_folder(base_dir='webpages') -> None:
    """
    create a folder if one does not exist.
    if a recent folder exist return the path to user and exit
    """
    check_folder = get_latest_batch_folder(base_dir)
    match check_folder:
        case Path() as folder:
            LOGGER.info(f"recent batch found at {folder}")
            raise FilexistsError(f"recent batch found at {folder}")
        case False:
            LOGGER.info(f"no recent batch found, creating new batch folder.")
   
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_path = Path(base_dir) / timestamp
    batch_path.mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"created new batch folder at {batch_path}")
    return batch_path

def download_landing_page(driver, url, base_path):
    webpage_path = base_path / 'finviz_etf_page_one.html'
    if not webpage_path.exists():
        try:
            driver.get(url)
            logger.info('Explicit wait for page to load')
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "styled-row")))
            
            with open(webpage_path, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info(f"{url=} saved to {webpage_path}")
            
        except Exception as e:
            logger.error(f"error fetching {url=}: {e}")
        
        finally:
            driver.quit()
            logger.info("Selenium WebDriver closed")
    logger.info(f"{webpage_path} already exists. Skipping download.")
    return webpage_path

def map_landing_page(webpage_path, max_depth=12):
    html_blob = webpage_path.read_text(encoding='utf-8')
    soup = BeautifulSoup(html_blob, 'html.parser')
    
    dom_tree_data = {
    "name": "ETF_SCREENER_AGGREGATE",
    "data": {"tag": "synthetic", "semantic_role": "page_root"},
    "children": []
    }
    
    for label, element_id in FUNCTIONAL_AREAS.items():
        found_node = soup.find(id=element_id)
        if found_node:
            branch = aux_funcs.build_tree_data(
                found_node,
                max_depth=max_depth,
                inventory_hash=INV_HASH
            )
            if branch:
                branch["name"] = f"{label} | {branch['name']}"
                dom_tree_data["children"].append(branch)
    LOGGER.info(f"mapped dom tree starting from {soup.body.name}; max depth {max_depth}")

def main():
    args = get_args()
    
    pages_to_download = args.pages
    
    driver = create_driver(headless=args.headless)
    CWD = Path.cwd()
    base_dir = CWD / "webpages"
    
    webpage = args.webpage
    
    try:
        first_page_url = download_landing_page(driver, FINVIZ_ETF_PAGE_BASE, base_dir)
        dom_tree = map_landing_page(first_page_url)

        full_scrape_plan = extract_scrape_list_from_tree(dom_tree, webpage)

        if args.pages:
            scrape_plan = full_scrape_plan[:args.pages]
            logger.info(f"limited scrape plan to first {args.pages} pages")

        recent_batch = get_latest_batch_folder(base_dir)
        batch_folder = None
        
        
