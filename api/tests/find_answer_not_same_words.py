from pymongo import MongoClient
from difflib import SequenceMatcher
import random

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-staging.0bcs2.mongodb.net"
MONGODB_DATABASE = "chatbotdb"

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

# Ensure text index
def ensure_text_index(collection, field):
    try:
        indexes = collection.index_information()
        # Check if a text index already exists for the specified field
        if not any(index["key"][0][0] == field and index["key"][0][1] == "text" for index in indexes.values()):
            collection.create_index([(field, "text")], name=f"{field}_text_index")
            print(f"Text index created on field '{field}'")
        else:
            print(f"Text index already exists for field '{field}'")
    except Exception as e:
        print(f"Error creating/verifying text index: {e}")

# Check similarity
def is_similar(text1, text2, threshold=0.8):
    # Determine if two strings are similar based on the threshold
    ratio = SequenceMatcher(None, text1, text2).ratio()
    return ratio >= threshold

# Simple Rephrasing Function
def rephrase_text(text):
    # Generate a rephrased version of the provided text
    rephrases = [
        f"In other words: {text}",
        f"A different way to say it: {text}",
        f"To put it differently: {text}",
        f"Essentially: {text}",
        f"In simpler terms: {text}",
    ]
    return random.choice(rephrases)

# Search and respond with rephrased answers
def search_and_rephrase_answers(query, collection_name="feedback_data"):
    collection = db[collection_name]
    ensure_text_index(collection, "correct_answer")  # Ensure text index on the field

    print(f"Searching for: '{query}' in collection '{collection_name}'")
    try:
        # Perform a text search on the 'correct_answer' field
        results = collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}, "correct_answer": 1, "metadata.translations": 1}
        ).sort("score", {"$meta": "textScore"})  # Sort by text score

        results_list = list(results)
        if results_list:
            print(f"Found {len(results_list)} related results.")

            merged_results = []
            seen_answers = []

            for result in results_list:
                answer = result.get("correct_answer", "")
                raw_translations = result.get("metadata", {}).get("translations", [])
                score = result.get("score", 0)

                # Normalize translations to a dictionary
                translations = {}
                if isinstance(raw_translations, list):
                    for item in raw_translations:
                        if isinstance(item, dict) and "language" in item and "text" in item:
                            translations[item["language"]] = item["text"]
                elif isinstance(raw_translations, dict):
                    translations = raw_translations

                # Check for similar answers in seen_answers
                is_duplicate = False
                for seen in seen_answers:
                    if is_similar(answer, seen["correct_answer"]):
                        # Merge translations
                        for lang, text in translations.items():
                            if lang not in seen["translations"]:
                                seen["translations"][lang] = text
                        is_duplicate = True
                        break

                if not is_duplicate:
                    seen_answers.append({
                        "correct_answer": answer,
                        "translations": translations,
                        "score": score
                    })

            # Sort by confidence score
            merged_results = sorted(seen_answers, key=lambda x: x["score"], reverse=True)

            for result in merged_results:
                rephrased_answer = rephrase_text(result["correct_answer"])
                print(f"- Correct Answer: {rephrased_answer} (Confidence: {result['score']:.2f})")
                print(f"  Translations: {result['translations']}")
            return merged_results
        else:
            print("No related correct answers found.")
            return None
    except Exception as e:
        print(f"Error searching for correct answers: {e}")
        return None

# Dynamic Query
query = "What do you know about Glauco"
merged_results = search_and_rephrase_answers(query)