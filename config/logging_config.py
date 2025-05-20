import logging
import os
from datetime import datetime

def setup_logging(enable_logging=True):
    """
    Set up centralized logging configuration for the entire application.
    
    Args:
        enable_logging (bool): Whether to enable logging. If False, only CRITICAL messages will be logged.
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Set up log file with timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(log_dir, f'GlitchController_{timestamp}.log')
    
    # Configure logging level based on enable_logging parameter
    log_level = logging.DEBUG if enable_logging else logging.CRITICAL
    
    # Configure logging with UTF-8 encoding
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s,%(lineno)d,%(name)s,%(levelname)s,%(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # Also log to console
        ]
    )
    
    # Log the start of a new session
    logging.info("=== New logging session started ===")
    logging.info("Log level set to: %s", logging.getLevelName(log_level))
    
    return log_file 