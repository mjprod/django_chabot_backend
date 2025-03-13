import logging
from rich.logging import RichHandler
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn

def setup_logger():
    """
    Setup a logger using rich for colored console logs and optional file logging.
    """
    logger = logging.getLogger("brain_manager")
    if logger.hasHandlers():
        return logger  # Prevent duplicate handlers

    logger.setLevel(logging.INFO)
    
    rich_handler = RichHandler(rich_tracebacks=True, markup=True)
    file_handler = logging.FileHandler("brain_manager.log")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    
    logger.addHandler(rich_handler)
    logger.addHandler(file_handler)
    
    return logger

def get_progress_bar():
    """
    Returns a rich Progress instance for tracking long-running tasks.
    """
    return Progress(
        TextColumn("[bold blue]{task.description}[/]"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
    )

logger = setup_logger()