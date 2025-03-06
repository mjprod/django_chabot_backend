default_app_config = "api.apps.YourAppConfig"

import logging
from .services.chatbot_service.brain import Brain

# load old conversation brain on app starts
Brain()