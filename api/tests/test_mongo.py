from pymongo import MongoClient
from urllib.parse import quote_plus
import certifi
import logging

# Enable detailed logging for debugging
logging.basicConfig(level=logging.DEBUG)

try:
    # Encode username and password
    username = quote_plus("jared.mjpro@gmail.com")
    password = quote_plus("w33k4@H-p6.A*4$")

    # MongoDB URI
    uri = f"mongodb+srv://{username}:{password}@chatbotdb.ooyoj.mongodb.net/ChatbotDB?retryWrites=true&w=majority"

    # Create a MongoDB client with SSL/TLS enabled
    client = MongoClient(
        uri,
        tls=True,  # Enable TLS
        tlsCAFile=certifi.where(),  # Use trusted CA certificates
        serverSelectionTimeoutMS=5000,  # Timeout after 5 seconds
    )

    # Test connection with a ping
    db = client.get_database("ChatbotDB")
    print("Connected successfully:", db.command("ping"))

except Exception as e:
    print("Connection failed:", e)
