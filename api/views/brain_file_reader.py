import json
import os
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)

def flatten_data(data: Any) -> List[Dict]:
    """
    Se data for uma lista aninhada, achata-a e retorna uma lista de dicionários.
    Se data já for uma lista de dicionários, retorna-a.
    """
    flattened = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                flattened.extend(flatten_data(item))
            elif isinstance(item, dict):
                flattened.append(item)
            else:
                logger.error(f"Item inesperado: {item}")
    elif isinstance(data, dict):
        flattened.append(data)
    else:
        logger.error(f"Tipo de dado inesperado: {type(data)}")
    return flattened

def load_all_documents() -> List[Dict]:
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..", "data")
    database_files = [
        "database_part_1.json",
        "database_part_2.json",
        "database_part_3.json"
    ]
    
    all_documents = []
    for file_name in database_files:
        file_path = os.path.join(base_dir, file_name)
        logger.debug(f"Processando arquivo: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        
            docs = flatten_data(data)
            all_documents.extend(docs)
        except Exception as e:
            logger.exception(f"Erro to read {file_path}: {e}")
    
    logger.debug(f"Total of docs: {len(all_documents)}")
    return all_documents

def get_document_count() -> Optional[Dict]:
    documents = load_all_documents()
    num_datas = len(documents)
    print(f": {num_datas}")
    return num_datas

def get_document_by_id(document_id: str) -> Optional[Dict]:
    documents = load_all_documents()
    for doc in documents:
        if doc.get("id") == document_id:
            return doc

    logger.warning(f"Document ID {document_id} not found.")
    return None

def get_document_by_question_text(question_text: str) -> Optional[str]:
    documents = load_all_documents()
    for doc in documents:
        if doc.get("question", {}).get("text") == question_text:
            return doc.get("id")

    logger.warning(f"Documento com texto de pergunta '{question_text}' não encontrado.")
    return None

def update_answer_detailed_en(document_id: str, new_value: str):
    # Load all documents from JSON files
    documents = load_all_documents()
    updated = False

    # Iterate over the documents to find the one with the matching id
    for doc in documents:
        if doc.get("id") == document_id:
            # Check if the structure answer -> detailed exists
            if "answer" in doc and "detailed" in doc["answer"]:
                doc["answer"]["detailed"]["en"] = new_value
                updated = True
                break

    if updated:
        # Define the output file path for the updated JSON
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "updated_documents.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(documents, f, indent=4, ensure_ascii=False)
        print(f"Document {document_id} updated successfully. New answer.detailed.en: {new_value}")
    else:
        print(f"Document with ID {document_id} not found or 'answer/detailed' structure is missing.")