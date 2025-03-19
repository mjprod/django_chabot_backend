import os
from dotenv import load_dotenv

load_dotenv()
app_env = os.getenv("DJANGO_ENV", "local").upper()

MONGODB_URI=os.getenv(f"{app_env}_MONGODB_URI")
MONGODB_DATABASE=os.getenv(f"{app_env}_MONGODB_DATABASE")