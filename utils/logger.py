import logging
from rich.logging import RichHandler
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn

def setup_logger():
    """
    Setup a logger using rich for colored console logs and optional file logging.
    This is safe to use in Django projects.
    """
    rich_handler = RichHandler(rich_tracebacks=True, markup=True)

    logger = logging.getLogger("brain")
    logger.setLevel(logging.INFO)

    # Avoid duplicate handlers if setup_logger() is called multiple times
    if not logger.hasHandlers():
        logger.addHandler(rich_handler)

        # Optional: File handler (useful in production or debugging)
        file_handler = logging.FileHandler("brain.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
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

# Initialize logger when imported
logger = setup_logger()
