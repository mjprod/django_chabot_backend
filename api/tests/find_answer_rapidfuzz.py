from pymongo import MongoClient
from rapidfuzz import fuzz
import re
import nltk
from nltk.corpus import stopwords
import jieba

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

# Download NLTK stopwords (if not already downloaded)
nltk.download('stopwords')
custom_stopwords = {
    "ms_MY": {
        "dan", "untuk", "dengan", "yang", "di", "ke", "atau", "pada", "adalah", "dari", "ini", "itu", "saya", "kami", "anda",
        "mereka", "semua", "tersebut", "sebuah", "oleh", "pada", "sama", "maksud", "apa", "akan", "dapat", "belum", "lebih"
        # Add more Malay stopwords if needed
    },
    "zh_CN": {
        "的", "了", "在", "是", "我", "你", "他", "她", "它", "我们", "你们", "他们", "这个", "那个", "的", "和", "与", "就", "也",
        "不", "都", "而", "为", "上", "下", "对", "和", "说", "来", "去", "为", "要", "自己", "有", "可以", "是不是", "等", "如果"
    },
    "zh_TW": {
        "的", "了", "在", "是", "我", "你", "他", "她", "它", "我們", "你們", "他們", "這個", "那個", "的", "和", "與", "就", "也",
        "不", "都", "而", "為", "上", "下", "對", "和", "說", "來", "去", "為", "要", "自己", "有", "可以", "是不是", "等", "如果"
    }
}

def get_stopwords(language="en"):
    """
    Dynamically fetch stopwords for a given language.
    :param language: The language code (e.g., 'en', 'ms-MY', 'zh_CN')
    :return: A set of stopwords for the specified language
    """
    try:
        # Try fetching stopwords from NLTK
        return set(stopwords.words(language))
    except:
        # If NLTK stopwords are unavailable, use custom stopwords
        return custom_stopwords.get(language, set())

# Function to extract dynamic keywords (improved version)
def extract_keywords(text, language="en"):
    """
    Dynamically extract significant words from the text (excluding common stopwords).
    :param text: Text from which keywords will be extracted
    :param language: Language of the input text
    :return: List of keywords
    """
    stop_words = get_stopwords(language)  # Dynamically get stopwords
    # Remove stopwords and non-alphabetic characters, and extract keywords
    # words = re.findall(r'\b[A-Za-z]{2,}\b', text.lower())  # Use lowercase for better matching

    if language in ["zh_CN", "zh_TW"]:
        # Tokenize Chinese text using jieba
        words = jieba.cut(text)
    else:
        # Extract words from non-Chinese text
        words = re.findall(r'\b[A-Za-z]{2,}\b', text.lower())

    # keywords = [word for word in words if word not in stop_words]
    keywords = [word for word in words if word not in stop_words and len(word.strip()) > 1]

    return set(keywords)


def fuzzy_match_with_dynamic_context(query, collection_name="feedback_data", language = "en", threshold=50):
    """
    Perform fuzzy matching with dynamic keyword extraction for context.
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

    # Extract keywords from the query
    query_keywords = extract_keywords(query, language)
    print(f"Query Keywords: {query_keywords}")

    matches = []

    for doc in documents:
        user_input = doc.get("user_input", "")
        correct_answer = doc.get("correct_answer", "")
        combined_text = f"{user_input} {correct_answer}".strip()

        # Extract keywords from the document
        document_keywords = extract_keywords(combined_text, language)
        # print(f"Document Keywords: {document_keywords}")

        # Calculate fuzzy similarity
        similarity = fuzz.partial_ratio(query, combined_text)

        # Calculate keyword overlap score
        overlap_score = len(query_keywords & document_keywords) / max(len(query_keywords), 1) * 100

        # Combine similarity and keyword overlap for the final score
        final_score = (similarity * 0.6 + overlap_score * 0.4)

        # Only include matches above the threshold
        if final_score >= threshold:
            matches.append({"similarity": min(final_score, 100), **doc})

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])

    # Print matches in sorted order
    print("\nSimilarity Scores (Ordered):")
    for match in matches:
        print(f"Similarity: {match['similarity']}% | Combined: {match['user_input']} {match['correct_answer']}")

    return matches


# Define test queries
queries = [
    # "withdram the 4D Game bet?",
    # "What deposit payment methods do you accept? ",
    # "benefits to referring",
    # "Can I get anything for referring a friend?",
    # "Any restrictions to play a games",
    # "what is the authentication process",
    "Apakah kaedah pembayaran yang anda",
    "Apak deposit yang anda terima?",
    "Berapa lama masa yang diperlukan untuk deposit diproses?"
]

# Run Fuzzy Matching for Each Query
for query in queries:
    results = fuzzy_match_with_dynamic_context(query, "feedback_data_ms_MY", "ms_MY", threshold=50)  # Lower threshold for better results
    if results:
        print(f"\nTop Matches for Query: '{query}':")
        for result in results[:3]:  # Print top 3 matches
            print(
                (
                    f"Similarity: {result['similarity']}% | "
                    f"Question: {result['user_input']} | "
                    f"Answer: {result['correct_answer']}"
                )
            )
    else:
        print(f"*******--No relevant matches found for query: '{query}'.")