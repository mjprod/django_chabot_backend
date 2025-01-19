from pymongo import MongoClient
from colorama import Fore, Style

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-dev.0bcs2.mongodb.net"
MONGODB_DATABASE = "chatbotdb"


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


# Search and translate the top correct answer
def search_top_answer_and_translate(queries, collection_name="feedback_data"):
    collection = db[collection_name]

    collection.create_index(
        [("user_input", "text"), ("correct_answer", "text")],
        weights={"user_input": 10, "correct_answer": 5},
    )
    print(
        Fore.CYAN
        + f"Searching for: '{queries}' in collection '{collection_name}'"
        + Style.RESET_ALL
    )

    try:
        # Text search
        results = (
            collection.find(
                {"$text": {"$search": query}},
                {
                    "score": {"$meta": "textScore"},
                    "user_input": 1,
                    "correct_answer": 1,
                    "metadata": 1,
                },
            )
            .sort([("score", {"$meta": "textScore"})])
            .limit(3)
        )  # Top 3 results

        results_list = list(results)

        # Fallback to regex if no text search results
        if not results_list:
            print(
                Fore.YELLOW
                + "No text search results, falling back to regex..."
                + Style.RESET_ALL
            )
            regex_query = {
                "$or": [
                    {"user_input": {"$regex": f".*{query}.*", "$options": "i"}},
                    {"correct_answer": {"$regex": f".*{query}.*", "$options": "i"}},
                ]
            }
            results = collection.find(regex_query).limit(3)  # Limit to 3 results
            results_list = list(results)

        # Print results
        if results_list:
            print(Fore.GREEN + "Top 3 Search Results:" + Style.RESET_ALL)
            for result in results_list:
                print(
                    f"Score: {result.get('score', 'N/A')}, User Input: {result.get('user_input')}, "
                    f"Correct Answer: {result.get('correct_answer')}"
                )
        else:
            print(Fore.RED + "No related results found." + Style.RESET_ALL)

    except Exception as e:
        print(Fore.RED + f"Error: {e}" + Style.RESET_ALL)


# Define test queries
queries = [
    "你们这边接受什么存款方式？",
    "有什么存款支付选项我可以选？",
    "存款选项有什么？",
    "有哪些存款选项？",
    "押金支付方式有哪些？",
]

# Iterate over queries and search for answers for each one
for query in queries:
    print(f"\n--- Testing Query: '{query}' ---\n")
    search_top_answer_and_translate(query)
