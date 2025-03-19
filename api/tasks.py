from celery import shared_task
import logging
from datetime import datetime, timedelta
from api.services.conversation_streaming_manager import ConversationStreamingManager

logger = logging.getLogger("api")

@shared_task
def streaming_conversations_to_sap():
    current_date = datetime.now()

    # Get the date two days before the current date
    two_days_ago = current_date - timedelta(days=2)
    formatted_date = two_days_ago.strftime('%Y-%m-%d')

    manager = ConversationStreamingManager()
    manager.streaming_conversations_from_db(formatted_date)
    logger.info(f"Task executed at {current_date} for streamed conversations on date: {formatted_date}")