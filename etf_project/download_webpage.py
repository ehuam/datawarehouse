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

# SELENIUM SETUP
from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urljoin

import aux_funcs # edgar's static methods
import progress_utils # edgar's file writing funcs
import scrape_plan # edgar's scraping funcs
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
    "finviz": {
        "functional_areas": finviz_config.FUNCTIONAL_AREAS,
        "inventory_hash": finviz_config.INV_HASH,
        "base_url": finviz_config.BASE_URL,
    }
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
        "--init",
        action="store_true",
        help="download the landing page"
    )
    parse.add_argument(
        "--force",
        action="store_true",
        help="override recent complete batch and rerun."
    )
    
    return parser.parse_args()

def resolve_config(webpage:str, data_request_type: str) -> tuple[dict, dict]:
    """
    check if webpage is supported 
    """
    if webpage not in SUPPORTED:
        LOGGER.error(f"webpage {webpage} not supported. Supported pages are: {list(SUPPORTED.keys())}")
        raise ValueError(f"unsupported webpage {webpage}")
    data_req_map = SUPPORTED[webpage][data_request_type]
    if data_request_type not in data_req_map:
        LOGGER.error(f"data type {data_request_type} not supported for webpage {webpage}. Supported types are: {list(data_req_map.keys())}")
        raise ValueError(f"unsupported data request {data_request_type} for webpage {webpage}")
    return data_req_map[data_request_type], SITE_CONFIG[webpage]
    

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

# moving method from note book




# downloads

def download_landing_page(
        driver,
        first_page_url,
        batch_folder,
        request_type_config:dict):
    file_name = f"{request_type_config['name'].lower()}_landing.html"
    webpage_path = base_path / file_name 
    
    if webpage_path.exists():
        LOGGER.info(f'landing page already exists at {webpage_page}; skipping download')
        return webpage_path
    
    try:
        driver.get(first_page_url)
        LOGGER.info('Explicit wait for page to load')
        wait = WebDriverWait(driver, 15)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "styled-row")))
        
        with open(webpage_path, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info(f"{first_page_url} saved to {webpage_path}")
        
    except Exception as e:
        logger.error(f"error fetching {first_page_url}: {e}")
    
    finally:
        driver.quit()
        LOGGER.info("Selenium WebDriver closed")
    LOGGER.info(f"{webpage_path} already exists. Skipping download.")
    return webpage_path


# bulk download
def execute_bulk_download(driver, scrape_plan, batch_folder: Path):
    total = len(scrape_plan)
    wait =  WebDriverWait(driver, 15)
    
    for task in scrape_plan:
        match task["url"] in completed_urls:
            case True:
                LOGGER.info(f"skipping {task['index']} - already downloaded")
                continue
        
        file_name = f"page_{task['index']:03d}_offset_{task['offset']}.html"
        save_path = batch_folder / file_name
        
        try:
            LOGGER.info(f'downloading [{task["index"]}/{total}] {task['label']}')
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
            
            # mark complete after file is written
            progress_utils.mark_complete(batch_folder, task)
            
            # polite delay
            time.sleep(5)
        except Exception as e:
            LOGGER.error(f"failed to download {task['label']}: {e}")
            progress_utils.log_error(batch_folder, task, e)
            continue
            
    LOGGER.info(f"Bulk download complete. Files saved to {batch_folder}")
    
    
def main():
    args = get_args()
    
    pages_to_download = args.pages
    
    driver = create_driver(headless=args.headless)
    CWD = Path.cwd()
    base_dir = CWD / "webpages"
    
    webpage = args.webpage

