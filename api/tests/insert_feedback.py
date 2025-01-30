from pymongo import MongoClient
from datetime import datetime
import logging
import json

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-dev.0bcs2.mongodb.net"

MONGODB_DATABASE = "chatbotdb"

def insert_feedback(user_input, correct_answer, language="en"):
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

    # Criar o documento para inserção
    translated_data = {
        "user_input": user_input,
        "correct_answer": correct_answer,
        "ai_response": "",
        "correct_bool": False,
        "chat_rating": 0,
        "conversation_id": "",
        "timestamp": datetime.now().isoformat(),
        "metadata": {
            "translations": [],
            "confidence": 0.0,
        },
    }

    # Definir a coleção baseada no idioma
    language_collections = {
        "en": "feedback_data_en",
        "ms_MY": "feedback_data_ms_MY",
        "zh_CN": "feedback_data_zh_CN",
        "zh_TW": "feedback_data_zh_TW",
    }

    collection_name = language_collections.get(language)
    if not collection_name:
        raise ValueError(f"Unsupported language: {language}")

    try:
        # Conectar ao banco de dados
       
        collection = db[collection_name]

        # Inserir o documento no MongoDB
        result = collection.insert_one(translated_data)
        logger.info(f"Feedback inserido com sucesso: ID {result.inserted_id}")

        # Fechar conexão
        client.close()

        return {"message": "Feedback saved successfully", "id": str(result.inserted_id)}

    except Exception as e:
        logger.error(f"Erro ao inserir no MongoDB: {e}")
        return {"error": f"Database operation failed: {str(e)}"}


# Simulação de JSON recebido (pode ser de um arquivo ou API)
json_data = '''[
    {
        "user_input": "您接受哪些存款支付方式？",
        "correct_answer": "你好！我们目前接受以下存款支付方式：ATM转账、网上转账和电子钱包（E-Wallet）。每种方式都是安全的，处理时间在5-30分钟内。在存款页面选择最适合您的方式。"
    },
   
]'''

# Exemplo de uso
if __name__ == "__main__":
    # Converter JSON string para objeto Python (lista de dicionários)
    data = json.loads(json_data)

    # Iterar sobre o JSON e chamar a função insert_feedback()
    for entry in data:
        user_input = entry["user_input"]
        correct_answer = entry["correct_answer"]
    
        # Definir o idioma baseado no contexto (ajuste conforme necessário)
        language = "zh_CN"  # Exemplo para chinês simplificado, mude conforme necessário

        # Chamar a função insert_feedback
        result = insert_feedback(user_input, correct_answer, language)

        # Exibir o resultado
        print(result)
