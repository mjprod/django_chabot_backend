import json
import os
import logging

logger = logging.getLogger(__name__)

def get_document_by_id(document_id: str) -> dict:
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    file_path = os.path.join(base_dir, "data", "database_en.json")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        logger.info(f"File not found: {file_path}")

        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for doc in data:
        if doc.get("id") == document_id:
            return doc

    print(f"Document ID {document_id} not found.")
    return None

def get_document_by_question_text(question_text: str) -> dict:
    base_dir = os.path.join(os.path.dirname(__file__), "..")
    file_path = os.path.join(base_dir, "data", "database_en.json")
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        logger.info(f"File not found: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for doc in data:
        # Verifica se o texto da pergunta existe e confere se é igual ao parâmetro passado
        if doc.get("question", {}).get("text") == question_text:
            return doc.get("id")

    print(f"Document with question text '{question_text}' not found.")
    return None