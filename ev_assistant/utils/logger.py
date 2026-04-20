import logging
import google.cloud.logging
import os

def setup_logger():
    logger = logging.getLogger("ev_assistant")
    logger.setLevel(logging.INFO)
    
    # Use Cloud Logging if running on GCP
    if os.environ.get("K_SERVICE"):
        client = google.cloud.logging.Client()
        client.setup_logging()
    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
    return logger

logger = setup_logger()
