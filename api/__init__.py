default_app_config = "api.apps.YourAppConfig"

# from utils.logger import logger, get_progress_bar
# from .services.chatbot_service.brain import Brain
# from .services.chatbot_service.chatbot import ChatBot
# from .services.mongodb.mongodb_client import MongoDBClient
# from .services.chatbot_service.config import MONOGODB_LOW_CONFIDENCE_COLLECTION

# # load old conversation brain on app starts
# Brain()

# # temp solution for now to check if the existing low_confidence_response have response provided with answer generated based on past conversations
# # this process can be removed in the future
# logger.info(f"Processing the {MONOGODB_LOW_CONFIDENCE_COLLECTION} collection")
# # access the chatbot and mongodb_client singleton instances
# chatbot = ChatBot()
# mongodb_client = MongoDBClient()

# query = {
#     'generation_old_conversation': {'$exists': False}
# }

# low_confidence_responses, count = mongodb_client.query(collection=MONOGODB_LOW_CONFIDENCE_COLLECTION, query = query)
# logger.info(f"{count} of conversations need an UPDATE!")

# try:
#     for low_confidence_response in low_confidence_responses:
#         user_prompt=low_confidence_response.get("user_prompt")
#         generation_old_conversation= chatbot.query(user_prompt)
#         logger.info(f"Question: {user_prompt}")
#         logger.info(f"Response: {generation_old_conversation}")
#         # TODO: update the db document with a new key field : generation_old_conversation
#         # its hitting the limit
# except KeyError as e:
#     logger.error(f"key[{e}] not found")