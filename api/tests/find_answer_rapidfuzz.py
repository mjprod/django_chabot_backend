from pymongo import MongoClient
from colorama import Fore, Style
from rapidfuzz import fuzz


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


def fuzzy_match(query, collection_name="feedback_data", threshold=60):
    """
    Perform fuzzy matching on documents from MongoDB and return ordered results.
    :param query: User's query as a string.
    :param collection_name: Name of the MongoDB collection to search in.
    :param threshold: Minimum similarity score to include a match.
    :return: List of top matches sorted by similarity.
    """
    collection = db[collection_name]

    # Fetch all documents with 'user_input' and 'correct_answer'
    documents = list(collection.find({}, {"user_input": 1, "correct_answer": 1}))

    if not documents:
        print(f"No documents found in collection '{collection_name}'.")
        return []

    print(f"\n--- Testing Query: '{query}' against {len(documents)} documents ---")

    matches = []
    for doc in documents:
        user_input = doc.get("user_input", "")
        similarity = fuzz.partial_ratio(query, user_input)
        if similarity >= threshold:
            matches.append({"similarity": similarity, **doc})

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])

    # Print matches in sorted order
    print("\nSimilarity Scores (Ordered):")
    for match in matches:
        print(f"Similarity: {match['similarity']}% | User Input: {match['user_input']}")

    return matches


        # Define test queries
queries = [
    "你们这边接受什么存款方式？",
    "有什么存款支付选项我可以选？",
    "存款选项有什么？",
    "有哪些存款选项？",
    "押金支付方式有哪些？",
]

# Run Fuzzy Matching for Each Query
for query in queries:
    results = fuzzy_match(query, "feedback_data", threshold=60)
    if results:
        print(f"\nTop Matches for Query: '{query}':")
        for result in results[:3]:  # Print top 3 matches
            print(f"Similarity: {result['similarity']}% | Question: {result['user_input']} | Answer: {result['correct_answer']}")
    else:
        print(f"No relevant matches found for query: '{query}'.")
