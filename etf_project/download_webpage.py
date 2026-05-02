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

from bs4 import BeautifulSoup

# SELENIUM SETUP
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import aux_funcs # edgar's static methods

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s - %(levelname)s - %(asctime) - %(message)s",
    )
LOGGER = logging.getLogger(__name__)

# CONSTANTS

FINVIZ_ETF_PAGE_BASE = "https://finviz.com/screener.ashx?v=181"

# ETF COLUMN MAPPING - BASED ON STRUCTURE
ETF_COLUMN_MAPPING = {
    6: ['price', 'ticker', 'company', 'industry', 'value', 'country'],
    5: ["dividend"],
    7: ["change_pct"]
}

# SITE INVENTORY - USER DECOMPOSITION
SITE_INVENTORY = {
    "control_plane": ["screener-combo-title", "screener-combo-select"],
    "navigation_tabs": ["Descriptiv", "ExchangeAn", "OverviewVa"],
    "data_rows": ["styled-row"],
    "layout_noise": [
        "header", "navbar", "footer", "modal-elite-ad", "script", "noscript", "iframe",
        "js-elite-features-root", "notifications-container", "notifications-react-root",
        "dialogs-react-root", "root", "IC_D_1x1_1", "portal/_r_5_", "ICUid_Iframe",
        "img", "svg", "use", "js-feature-discovery-root", "screener-presets-root"
    ],
    "pagination_drop": ["pageSelect"],
    "pagination_option": ["option"],
    "navigation_controls": ["screener_pagination", "pages-combo", "is-next", "screener-pages"],
}

FUNCTIONAL_AREAS = {
    "SCREENER_FILTERS": "filter-table-top",
    "DATA": "screener-views-table",
    "PAGINATION": "pageSelect",
    "PAGINATION_NAV": "screener_pagination",
}

# for faster processing flattening instead of lookup 
INV_HASH = {item: category for category, items in SITE_INVENTORY.items() for item in items}

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
def extract_scrape_list_from_tree(dom_tree, webpage_name:str):
    """
    using the pagination tags to extract the URL list for scraping
    """

    match webpage_name:
        case "finviz":
            webpage = "https://finviz.com/"
            string_pattern = "screener.ashx?v=181&r=" # finvzi pattern
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