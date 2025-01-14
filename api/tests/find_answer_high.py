from pymongo import MongoClient
from googletrans import Translator
from colorama import Fore, Style
from transformers import pipeline
import random
from difflib import SequenceMatcher

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-staging.0bcs2.mongodb.net"
MONGODB_DATABASE = "chatbotdb"

# Translator configuration
translator = Translator()

# Initialize paraphrase pipeline
paraphrase_pipeline = pipeline(
    "text2text-generation", model="t5-base", tokenizer="t5-base"
)

# Connect to MongoDB
try:
    client = MongoClient(
        f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@"
        f"{MONGODB_CLUSTER}/{MONGODB_DATABASE}?"
        f"retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
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
        if not any(
            index["key"][0][0] == field and index["key"][0][1] == "text"
            for index in indexes.values()
        ):
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
        translations["ms-MY"] = translator.translate(
            correct_answer, src="en", dest="ms"
        ).text

        # Translate to Chinese
        translations["cn"] = translator.translate(
            correct_answer, src="en", dest="zh-cn"
        ).text

    except Exception as e:
        print(f"Error translating text: {e}")
    return translations


# Check similarity to avoid repeating the original text
def is_similar(text1, text2, threshold=0.8):
    return SequenceMatcher(None, text1, text2).ratio() >= threshold


# Filter similar or nonsensical paraphrases
def filter_valid_paraphrases(paraphrases, original_text, threshold=0.8):
    unique_phrases = []
    for phrase in paraphrases:
        if not is_similar(phrase, original_text, threshold) and len(phrase.strip()) > 5:
            unique_phrases.append(phrase)
    return unique_phrases


# Generate dynamic paraphrases with validation
def rephrase_correct_answer_dynamic(text):
    try:
        paraphrases = paraphrase_pipeline(
            f"paraphrase: {text}",
            max_length=50,
            num_return_sequences=3,
            do_sample=True,
            top_k=50,
            top_p=0.9,
            repetition_penalty=1.2,
        )
        rephrased_options = [
            p["generated_text"] for p in paraphrases if "generated_text" in p
        ]
        valid_phrases = filter_valid_paraphrases(rephrased_options, text)

        return random.choice(valid_phrases) if valid_phrases else text
    except Exception as e:
        print(f"Error during rephrasing: {e}")
        return text  # Fallback to the original text


# Search, rephrase, and translate the top correct answer
def search_top_answer_and_translate(query, collection_name="feedback_data"):
    collection = db[collection_name]
    print(
        Fore.CYAN
        + f"Searching for: '{query}' in collection '{collection_name}'"
        + Style.RESET_ALL
    )
    try:
        # Use the existing text index (on user_input)
        results = collection.find(
            {"$text": {"$search": query}},  # Search in the existing text index
            {
                "score": {"$meta": "textScore"},  # Include relevance score
                "correct_answer": 1,  # Ensure "corret_answer"
            },
        ).sort(
            "score", {"$meta": "textScore"}
        )  # Sort by relevance

        results_list = list(results)
        if results_list:
            top_result = results_list[0]  # Select the result with the highest score
            correct_answer = top_result["correct_answer"]
            confidence = top_result["score"]

            print("Top Result:")
            print(
                Fore.GREEN + f"- Correct Answer (EN): {correct_answer} "
                f"(Confidence: {confidence:.2f})" + Style.RESET_ALL
            )

            # Generate and display a rephrased version of the answer
            rephrased_answer = rephrase_correct_answer_dynamic(correct_answer)
            print(
                Fore.BLUE
                + f"- Paraphrased Answer (EN): {rephrased_answer}"
                + Style.RESET_ALL
            )

            # Translate the `correct_answer` field to other languages
            translations = translate_correct_answer(correct_answer)

            # Display translations
            print("Translations:")
            for lang, translation in translations.items():
                print(
                    Fore.MAGENTA + f"  {lang.upper()}: {translation}" + Style.RESET_ALL
                )
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
    "How can I get my money refund?",
    "How can I get my money back?",
    "How can I get a money?",
    "How can I optimize your query!",
]

# Iterate over queries and search for answers for each one
for query in queries:
    print(f"\n--- Testing Query: '{query}' ---\n")
    search_top_answer_and_translate(query)
