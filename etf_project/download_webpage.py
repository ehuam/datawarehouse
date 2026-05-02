"""
Because we are running this from a notebook we need to be careful on how we are getting the scraped web page data.
What we decided to do was to have a file hold all the methods to get the web page data. it should also accept an argument
as to how many pages it should download. We do this because it takes about 1 hour to download 552 pages. Also the user may
have already downloaded the data and it should not be called again.

We have then decided to move the methods from the notebook here.
"""

import os
import time
import datetime
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
