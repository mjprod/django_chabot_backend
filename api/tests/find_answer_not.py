from pymongo import MongoClient
from googletrans import Translator
from colorama import Fore, Style

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-staging.0bcs2.mongodb.net"
MONGODB_DATABASE = "chatbotdb"

# Translator configuration
translator = Translator()

# Connect to MongoDB
try:
    client = MongoClient(
        f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/{MONGODB_DATABASE}?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
    )
    db = client[MONGODB_DATABASE]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()

# Ensure that a text index exists for the specified field
def ensure_text_index(collection, field):
    try:
        indexes = collection.index_information()
        if not any(index["key"][0][0] == field and index["key"][0][1] == "text" for index in indexes.values()):
            collection.create_index([(field, "text")], name=f"{field}_text_index")
            print(f"Text index created on field '{field}'")
        else:
            print(f"Text index already exists for field '{field}'")
    except Exception as e:
        print(f"Error creating/verifying text index: {e}")

# Translate text dynamically using Google Translate
def translate_correct_answer(correct_answer):
    translations = {}
    try:
        # Translate to Malay
        translations["ms-MY"] = translator.translate(correct_answer, src="en", dest="ms").text

        # Translate to Chinese
        translations["cn"] = translator.translate(correct_answer, src="en", dest="zh-cn").text

    except Exception as e:
        print(f"Error translating text: {e}")
    return translations

# Search and translate the top correct answer
def search_top_answer_and_translate(query, collection_name="feedback_data"):
    collection = db[collection_name]
    print(Fore.CYAN +f"Searching for: '{query}' in collection '{collection_name}'"+ Style.RESET_ALL)
    try:
        # Use the existing text index (on user_input)
        results = collection.find(
            {
                "$text": {"$search": query}  # Search in the existing text index
            },
            {
                "score": {"$meta": "textScore"},  # Include relevance score
                "correct_answer": 1  # Ensure the `correct_answer` field is included
            }
        ).sort("score", {"$meta": "textScore"})  # Sort by relevance

        results_list = list(results)
        if results_list:
            top_result = results_list[0]  # Select the result with the highest score
            correct_answer = top_result["correct_answer"]
            confidence = top_result["score"]

            print(f"Top Result:")
            print(Fore.GREEN + f"- Correct Answer (EN): {correct_answer} (Confidence: {confidence:.2f})"+ Style.RESET_ALL)

            # Translate the `correct_answer` field to other languages
            translations = translate_correct_answer(correct_answer)

            # Display translations
            print("Translations:")
            for lang, translation in translations.items():
                print(Fore.MAGENTA + f"  {lang.upper()}: {translation}"+ Style.RESET_ALL)
        else:
            print(Fore.RED + "No related correct answers found." + Style.RESET_ALL)
    except Exception as e:
        print(f"Error fetching highest confidence answer: {e}")

# Define test queries
queries = [
    "who is Glauco?",
    "what do you know about Glauco?",
    "is Glauco a person or a deity?",
    "tell me about Glauco in mythology.",
    "can you explain the myth of Glauco?",
    "can you explain the myth of Galuco?",
     "who is Glauco?",
    "what do you know about Glauco?",
    "is Glauco a person or a deity?",
    "tell me about Glauco in mythology.",
    "can you explain the myth of Glauco?",
    "can you explain the myth of Galuco?",
]

# Iterate over queries and search for answers for each one
for query in queries:
    print(f"\n--- Testing Query: '{query}' ---\n")
    search_top_answer_and_translate(query)