from pymongo import MongoClient
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from collections import Counter
import numpy as np

# Configuração do MongoDB
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-staging.0bcs2.mongodb.net"
MONGODB_DATABASE = "chatbotdb"

# Conectar ao MongoDB
try:
    client = MongoClient(
        f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_CLUSTER}/{MONGODB_DATABASE}?retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
    )
    db = client[MONGODB_DATABASE]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()


# Função para buscar dados do banco
def fetch_correct_answers(collection_name="feedback_data"):
    collection = db[collection_name]
    results = collection.find({}, {"correct_answer": 1, "_id": 0})
    return [
        result["correct_answer"] for result in results if "correct_answer" in result
    ]


# Função para agrupar respostas
def rank_topics(data, num_clusters=3):
    # Vetorização de texto usando TF-IDF
    vectorizer = TfidfVectorizer(stop_words="english")
    tfidf_matrix = vectorizer.fit_transform(data)

    # Agrupamento KMeans
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)

    clusters = kmeans.labels_
    terms = vectorizer.get_feature_names_out()

    # Identificar os principais termos por cluster
    clustered_data = {}
    for i in range(num_clusters):
        cluster_indices = np.where(clusters == i)[0]
        cluster_terms = [data[idx] for idx in cluster_indices]
        clustered_data[f"Cluster {i+1}"] = Counter(cluster_terms).most_common()

    return clustered_data


# Buscar dados do MongoDB
data = fetch_correct_answers()

if data:
    # Rankear tópicos
    ranked_topics = rank_topics(data, num_clusters=3)
    print("Ranked Topics:")
    for cluster, topics in ranked_topics.items():
        print(f"{cluster}:")
        for topic, count in topics:
            print(f"  - {topic} (Occurrences: {count})")
else:
    print("No data found in the 'correct_answer' field.")
