from pymongo import MongoClient
from rapidfuzz import fuzz
import re
import nltk
from nltk.corpus import stopwords
import jieba
from openai import OpenAI
from datetime import datetime
from sentence_transformers import SentenceTransformer, util

# Load a better model (More accurate for question-answer tasks)
model = SentenceTransformer('sentence-t5-large')

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-dev.0bcs2.mongodb.net"
# MONGODB_CLUSTER = "chatbotdb-staging.0bcs2.mongodb.net"

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
nltk.download("stopwords")
custom_stopwords = {
    "ms_MY": {
        "dan",
        "untuk",
        "dengan",
        "yang",
        "di",
        "ke",
        "atau",
        "pada",
        "adalah",
        "dari",
        "ini",
        "itu",
        "saya",
        "kami",
        "anda",
        "mereka",
        "semua",
        "tersebut",
        "sebuah",
        "oleh",
        "pada",
        "sama",
        "maksud",
        "apa",
        "akan",
        "dapat",
        "belum",
        "lebih",
        # Add more Malay stopwords if needed
    },
    "zh_CN": {
        "的",
        "了",
        "在",
        "是",
        "我",
        "你",
        "他",
        "她",
        "它",
        "我们",
        "你们",
        "他们",
        "这个",
        "那个",
        "的",
        "和",
        "与",
        "就",
        "也",
        "不",
        "都",
        "而",
        "为",
        "上",
        "下",
        "对",
        "和",
        "说",
        "来",
        "去",
        "为",
        "要",
        "自己",
        "有",
        "可以",
        "是不是",
        "等",
        "如果",
    },
    "zh_TW": {
        "的",
        "了",
        "在",
        "是",
        "我",
        "你",
        "他",
        "她",
        "它",
        "我們",
        "你們",
        "他們",
        "這個",
        "那個",
        "的",
        "和",
        "與",
        "就",
        "也",
        "不",
        "都",
        "而",
        "為",
        "上",
        "下",
        "對",
        "和",
        "說",
        "來",
        "去",
        "為",
        "要",
        "自己",
        "有",
        "可以",
        "是不是",
        "等",
        "如果",
    },
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
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
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
        words = re.findall(r"\b[A-Za-z]{2,}\b", text.lower())

    # keywords = [word for word in words if word not in stop_words]
    keywords = [
        word for word in words if word not in stop_words and len(word.strip()) > 1
    ]

    return set(keywords)


def check_answer_mongo_and_openai(user_question, matches):
    if not matches:
        return None

    prompt = f"User question: {user_question}\n\n"
    prompt += "Here are some possible answers found in the database:\n"

    for idx, match in enumerate(matches):
        question = match.get("user_input", "N/A")
        answer = match.get("correct_answer", "N/A")
        prompt += f"\nQ{idx + 1}: {question}\nA{idx + 1}: {answer}\n"

    prompt += f"\nGiven the above answers, please generate the **best possible response** for the user question: '{user_question}'.\n"
    prompt += "Ensure the response is clear, concise, and well-structured. \
        If no answer fully matches, synthesize the best information available."
    prompt += f"\nGenerate a **direct and concise answer** to the user's question: '{user_question}'.\n"
    prompt += """
        You must determine the best possible response to the user's question: '{user_question}'.
        - If at least one answer contains relevant information, **return the best-matching answer exactly as found**.
        - Do **not** modify, rephrase, or summarize the answer. **Return it word-for-word**.
        - If multiple answers match, **prioritize the most recent one (use timestamps)**.
        - If no relevant answer exists, respond with **only**: `"NO"`
        - Do **not** include: "The information provided does not specify details about..." or "I need more context."
        - Do **not** say "Yes, I have information about..." Just return the relevant answer.
    """

    print(prompt)
    api_key = ""
    if not api_key:
        # logger.error("Missing OPENAI_API_KEY environment variable.")
        return None

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are an AI assistant evaluating answers to user questions.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
    )

    final_response = response.choices[0].message.content.strip()

    if "no" in final_response.lower() and len(final_response) < 5:
        return None

    return final_response


def fuzzy_match_with_dynamic_context(query, collection_name="feedback_data_en", threshold=10):
    """
    Find the most semantically similar question-answer pair in MongoDB.

    :param query: User's input query.
    :param collection_name: Name of the MongoDB collection.
    :param threshold: Minimum similarity score to return results.
    :return: List of top matches sorted by similarity.
    """
    collection = db[collection_name]

    # Fetch all documents with 'user_input' (question) and 'correct_answer' (answer)
    # documents = list(collection.find({}, {"user_input": 1, "correct_answer": 1, "timestamp": 1}))
    documents = list(collection.find({}, {"user_input": 1, "correct_answer": 1, "timestamp": 1})
                .sort("timestamp", -1))  # Sort by timestamp (latest first)

    if not documents:
        return []

    # Compute embeddings for the query
    latest_questions = {}
    for doc in documents:
        user_input = doc.get("user_input", "").strip().lower()
        if user_input and user_input not in latest_questions:
            latest_questions[user_input] = doc  # Store only the latest entry

    # Compute embeddings for the query
    query_embedding = model.encode(query, convert_to_tensor=True)

    matches = []

    for doc in latest_questions.values():  # Iterate only through unique latest questions
        user_input = doc.get("user_input", "")
        correct_answer = doc.get("correct_answer", "")
        timestamp = doc.get("timestamp", "")

        # Merge question + answer for better context
        combined_text = f"Q: {user_input} A: {correct_answer}"

        # Compute embeddings for combined question + answer
        document_embedding = model.encode(combined_text, convert_to_tensor=True)

        # Compute similarity using embeddings
        similarity = util.pytorch_cos_sim(query_embedding, document_embedding).item() * 100

        # Word Overlap Score (Ensures proper nouns like 'Glauco' match better)
        query_words = set(query.lower().split())
        answer_words = set(correct_answer.lower().split())
        overlap_score = (len(query_words & answer_words) / max(len(query_words), 1)) * 100

        # Final Weighted Similarity: 90% on Answer, 10% on Overlap Boost
        final_similarity = (similarity * 0.9) + (overlap_score * 0.1)
        final_similarity = min(final_similarity, 100)

        # Only include matches above the threshold
        if final_similarity >= threshold:
            matches.append({
                "similarity": final_similarity,
                "user_input": user_input,
                "correct_answer": correct_answer,
                "timestamp": timestamp
            })

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])

    # Return the first correct_answer if matches exist, otherwise return False
    if matches:
        # Check if the first match has a similarity score greater than 80
        if matches[0]["similarity"] > 80:
            best_answer = matches[0]["correct_answer"]
            print("\nHigh Similarity Match Found:")
            print(best_answer)
            return best_answer  # Return immediately if it's a strong match

        # Otherwise, proceed with OpenAI validation
        limited_matches = matches[:5]

        openai_response = check_answer_mongo_and_openai(query, limited_matches)

        if openai_response:
            print("\nOpenAI Response:")
            print(openai_response)
            return openai_response
        else:
            print("No matches found.")
    else:
        print("No matches found.")


def fuzzy_match_with_dynamic_context_old(query, collection_name="feedback_data", language="en", threshold=10):
    """
    Perform fuzzy matching with dynamic keyword extraction for context.
    :param query: User's query as a string.
    :param collection_name: Name of the MongoDB collection to search in.
    :param threshold: Minimum similarity score to include a match.
    :return: List of top matches sorted by similarity.
    """
    collection = db[collection_name]

    index_information = collection.index_information()
    print(index_information)
    # Fetch all documents with 'user_input' and 'correct_answer'
    documents = list(
        collection.find({}, {"user_input": 1, "correct_answer": 1, "timestamp": 1})
    )

    if not documents:
        print(f"No documents found in collection '{collection_name}'.")
        return []

    # Extract keywords from the query
    # query_keywords = extract_keywords(query, language)

    matches = []

    for doc in documents:
        user_input = doc.get("user_input", "")
        correct_answer = doc.get("correct_answer", "")
        timestamp = doc.get("timestamp", "")

        combined_text = f"{correct_answer} {user_input} {timestamp}".strip()
        similarity = fuzz.partial_ratio(query, combined_text)
        if similarity >= threshold:
            matches.append({"similarity": min(similarity, 100), **doc})

    # Sort matches by similarity in descending order
    matches = sorted(matches, key=lambda x: -x["similarity"])
    # print(f"@@ BEFORE Found {str(matches)} matches.")
    # Ensure timestamp is correctly formatted before sorting
    for match in matches:
        match["timestamp"] = match.get("timestamp", "")  # Ensure field exists
        if isinstance(match["timestamp"], str):  # Convert timestamp string to datetime
            try:
                match["timestamp"] = datetime.fromisoformat(match["timestamp"])
            except ValueError:
                match["timestamp"] = datetime.min  # Set to minimum if invalid format

    # Sort by similarity (descending) and then by timestamp (latest first)
    matches = sorted(
        matches, key=lambda x: (-x["similarity"], -x["timestamp"].timestamp())
    )
    # print(f"@@ AFTER Found {str(matches)} matches.")

    # Return the first correct_answer if matches exist, otherwise return False
    print("\nSimilarity Scores (Ordered):")
    for match in matches:
        print(f"Similarity: {match['similarity']}% | Combined: {match['user_input']} {match['correct_answer']}")

    if matches:
        # Check if the first match has a similarity score greater than 80
        if matches[0]["similarity"] > 80:
            best_answer = matches[0]["correct_answer"]
            print("\nHigh Similarity Match Found:")
            print(best_answer)
            return best_answer  # Return immediately if it's a strong match

        # Otherwise, proceed with OpenAI validation
        limited_matches = matches[:5]

        openai_response = check_answer_mongo_and_openai(query, limited_matches)

        if openai_response:
            print("\nOpenAI Response:")
            print(openai_response)
            return openai_response
        else:
            print("No matches found.")
    else:
        print("No matches found.")


# Define test queries
queries = [
    # "withdram the 4D Game bet?",
    # "What deposit payment methods do you accept? ",
    # "benefits to referring",
    # "Can I get anything for referring a friend?",
    # "Any restrictions to play a games",
    # "what is the authentication process",
    # "Apakah kaedah pembayaran yang anda",
    #  "Apak deposit yang anda terima?",
    # "Berapa lama masa yang diperlukan untuk deposit diproses?",
    "DO you have any information of Glauco?",
]

# Run Fuzzy Matching for Each Query
for query in queries:
    result = fuzzy_match_with_dynamic_context(
        query, "feedback_data_en", threshold=10
    )  # Lower threshold for better results

    # if result:
    # print(f"\n '{result}'")
    # else:
    # print(f"*******--No relevant matches found for query: '{query}'.")
