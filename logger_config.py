import logging
import sys

def setup_logger():
    """
    Sets up a centralized logger for the application.
    """
    # Get the root logger
    logger = logging.getLogger("QuantApp")
    
    # Prevent setting up multiple handlers if this function is called more than once
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.INFO)

    # Create a handler to print logs to the console (standard output)
    handler = logging.StreamHandler(sys.stdout)
    
    # Create a formatter and add it to the handler
    # Format: [Timestamp] [Logger Name] [Log Level]: Message
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add the handler to the logger
    logger.addHandler(handler)
    
    return logger

# Create a logger instance to be imported by other modules
log = setup_logger()
