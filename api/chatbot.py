import logging

from dotenv import load_dotenv

from .brain_db import (
    create_vector_store,
)

# create our gloabl variables
logger = logging.getLogger(__name__)
logger.info("Initializing vector database...")

# Load environment variables
load_dotenv()

# Process docs
try:
    store = create_vector_store()
    logger.info("Vector store creation completed successfully")

except Exception as e: 
    logger.error(f"Failed to create vector store: {str(e)}")
    raise

if store is None:
    store = create_vector_store()