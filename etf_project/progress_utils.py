import json
import logging
from datetime import datetime
from pathlib import pathlib

LOGGER = loggging.getLogger(__name__)

PROGRESS_FILE = 'progress.json'
ERROR_LOG_FILE = 'errors.json'

def create_progress_file(
        batch_folder: Path,
        webpage:str,
        data_request:str,
        total_pages:int
) -> Path:
    progress_path = batch_folder / PROGRESS_FILE
    
    progress = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "webpage": webpage,
        "data_request": data_request,
        "total_pages":  total_pages,
        "completed": []
    }
    
    progress_path.write_text(json.dumps(progress, indent=4), encoding='utf-8')
    LOGGER.info(f"progress file created at {progress_path}")
    return progress_path

def read_progress_file(batch_folder: Path) -> dict | None:
    """
    check if a progress file was created
    """
    progress_path = batch_folder / PROGRESS_FILE
    if progress_path.exists():
        try:
            return json.loads(progress_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            LOGGER.error(f"failed to read progress file: {e}")
            raiseFileError()
    LOGGER.info('no progress file found')
    return None

def mark_complete(batch_folder: Path, page: dict) -> None:
    """
    write to json after html page has been downloaded
    """
    progress = read_progress_file(batch_folder)
    if progress is None:
        LOGGER.error("No progess file found.")
        raise FileNotFoundError("no progress file found")
    
    progress['completed'].append({
        "index": page['index'],
        "url": page['url'],
        "label": page['label']
        "offset": page["offset"]
        "completed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })
    
    progress_path = batch_folder / PROGRESS_FILE
    progress_path.write_text(json.dumps(progress, indent=4), encoding='utf-8')
    
def get_completed_urls(batch_folder: Path) -> set[str]:
    """
    pick up where we left off
    """
    progress = read_progress_file(batch_folder)
    if not progress:
        return set()
    return {entry['url'] for entry in progress.get('completed', [])}

def is_run_complete(progress:dict) -> bool:
    """
    check if all pages have been downloaded
    """
    return len(progress.get("completed", [])) == progress.get("total_pages", -1)


# error log
def log_error(batch_folder: Path, page:dict, error: Exception) -> None:
    """
    add an error entry
    """
    error_path = batch_folder / ERROR_LOG_FILE
    error_record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "index": page.get('index'),
        "url": page.get('url'),
        "label": page.get('label'),
        "offset": page.get("offset"),
        "error": str(error)
    }
    with open(error_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(error_record) + "\n")
        
    LOGGER.error(f"logged error for {page.get('index')} to {error_path}: {error}")