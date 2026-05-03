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
import progress_utils # edgar's file writing funcs
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

# RECENT WINDOW CHECK - to avoid redownloading
RECENT_WINDOW_MINUTES = 30

# arg parse
def get_args():
    parser = argparse.ArgumentParser(description="Data Scraper for Finviz")
    parse.add_argument(
        "--webpage",
        required=True,
        choices=list(SUPPORTED.keys()),
        help="which webpage to scrape")
    parse.add_argument(
        "--data-request",
        required=True,
        choices=["etf", "aum"],
        help="which data to scrape"
    )
    parse.add_argument("--pages", type=int, default=None, help="number of pages to download default is all")
    parse.add_argument("--headless", action="store_true", help="run selenium in headless mode")
    parse.add_argument(
        "--force",
        action="store_true",
        help="override recent complete batch and rerun."
    )
    
    return parser.parse_args()

def resolve_config(webpage:str, data_type: str) -> tuple[dict, dict]:
    """
    check if webpage is supported 
    """
    if webpage not in SUPPORTED:
        LOGGER.error(f"webpage {webpage} not supported. Supported pages are: {list(SUPPORTED.keys())}")
        raise ValueError(f"unsupported webpage {webpage}")
    data_req_map = SUPPORTED[webpage]
    if data_type not in data_req_map:
        LOGGER.error(f"data type {data_type} not supported for webpage {webpage}. Supported types are: {list(type_map.keys())}")
        raise ValueError(f"unsupported data type {data_type} for webpage {webpage}")
    return type_map[data_type], SITE_CONFIG[webpage]
    

# driver setup - default Firefox
def create_driver(headless: bool = False)-> webDriver.Firefox:
    """
    create a firefox driver
    """
    options = FirefoxOptions()
    if headless:
        options.add_argument("--headless")

    driver = webdriver.Firefox(options=options)
    return driver

# batch folder management
def find_recent_complete_batch(base_dir: Path, webpage: str, data_request: str) -> Path | None:
    """
    checks in folder to see if a progress json exists and is complete
    """
    if not base_dir.exists():
        return None
    
    for folder in base_dir.iterdir():
        if not folder.is_dir():
            continue
            
        progress = progress_utils.read_progress_file(folder)
        if not progress:
            continue
        if progress.get('webpage') != webpage or progress.get('data_request') != data_request:
            continue
        if not progress_utils.is_run_complete(progress):
            continue
        
        created_at = datetime.strptime(progress['created_at'], "%Y%m%d_%H%M%S")
        elapsed = datetime.now() - created_at
        if elapsed < timedelta(minutes=RECENT_WINDOW_MINUTES):
            LOGGER.info(f"recent complete batch found at {folder}, run {elapsed} ago. Use --force to override.")
            return folder
     
    return None
    
def create_batch_folder(base_dir: Path) -> Path:
    """
    create a timestamped folder
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_path = base_dir / f"batch_{timestamp}"
    batch_path.mkdir(parents=True, exist_ok=True)
    LOGGER.info(f"created new folder at {batch_path}")
    return batch_path

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



# downloads

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
        
        
