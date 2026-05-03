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
        request:str,
        total_pages:int
) -> Path:
    progress_path = batch_folder / PROGRESS_FILE
    
    progress = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "webpage": webpage,
        "request": request,
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

