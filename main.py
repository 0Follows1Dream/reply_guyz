import importlib
import time
from threading import Thread
from typing import Callable

from utils.logging import get_logger

# Get a logger for the module
logger = get_logger(__name__)
logger.info("Logging has been set up automatically when get_logger was called!")


def run_script(script_module: str):
    """
    Dynamically imports and runs a Python module.

    Parameters:
    script_module (str): The module path of the script to run.
    """
    logger.info(f"Running script module: {script_module}")
    try:
        module = importlib.import_module(script_module)
        if hasattr(module, "main"):  # Assume the script has a main function to run
            module.main()
        else:
            logger.warning(f"The module {script_module} does not have a main() function.")
        logger.info(f"Successfully completed script: {script_module}")
    except Exception as e:
        logger.error(f"Failed to run script {script_module}: {e}")


def run_threaded(job_func: Callable[[], None]) -> None:
    """
    Run a job function in a separate thread.

    Parameters:
    job_func (Callable[[], None]): The job function to run, expected to take no arguments and return None.

    Returns:
    None: This function starts a thread and does not return any value.
    """
    logger.info(f"Starting job function {job_func.__name__} in a separate thread.")
    job_thread = Thread(target=job_func)
    job_thread.start()


if __name__ == "__main__":
    logger.info("Starting the application...")
    logger.info("Application has finished.")

    # run_threaded(lambda: run_script("module."))
    # schedule.every().sunday.at("03:00").do(run_threaded, function)

    while True:
        time.sleep(3600)  # Sleep for 60 seconds
