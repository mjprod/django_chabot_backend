from enum import Enum
import random

# AI Models
OPENAI_MODEL_GPT_4 = "gpt-4o-mini"
OPENAI_MODEL_GPT_3_5 = "gpt-3.5-turbo"
#TODO - should be smarter, if we have a model ilimited, we should avoid using it here
def getModelRandom():
    return random.choice([OPENAI_MODEL_GPT_4, OPENAI_MODEL_GPT_3_5])

OPENAI_MODEL = getModelRandom()

# OPENAI_MODEL = "text-embedding-ada-002"
OPENAI_MODEL_EN_TO_CN = "gpt-4o-mini"

COHERE_MODEL = "embed-multilingual-v3.0"
OPENAI_TIMEOUT = 30

# Max Tokens
class MaxTokens(Enum):
    LOW = 150
    MEDIUM = 300
    HIGH = 500

MAX_TOKENS = MaxTokens.MEDIUM.value

class MaxTemperatures(Enum):
    LOW = 0.1
    MEDIUM = 0.7
    HIGH = 1.0

MAX_TEMPERATURE = MaxTemperatures.LOW.value

# Embedding and Search Parameters
EMBEDDING_CHUNK_SIZE = 1000
EMBEDDING_OVERLAP = 200

# Retrieve and Rank Parameters
MMR_SEARCH_K = 5
MMR_FETCH_K = 8
MMR_LAMBDA_MULT = 0.8

# URL we send the payload to for translation
URL_TRANSLATE_EN_TO_MS = "https://api.mesolitica.com/translation"

# Language Default
LANGUAGE_DEFAULT = "en"
