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
    """
    Carrega os documentos dos três arquivos JSON e retorna uma lista com todos eles,
    garantindo que a estrutura seja uma lista de dicionários.
    """
    base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
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
            logger.error(f"Arquivo não encontrado: {file_path}")
            continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Achata a estrutura caso necessário
            docs = flatten_data(data)
            all_documents.extend(docs)
        except Exception as e:
            logger.exception(f"Erro ao ler {file_path}: {e}")
    
    logger.debug(f"Total de documentos carregados: {len(all_documents)}")
    return all_documents

def get_document_count() -> Optional[Dict]:
    documents = load_all_documents()
    num_registros = len(documents)
    print(f"Número de registros: {num_registros}")
    return num_registros

def get_document_by_id(document_id: str) -> Optional[Dict]:
    """
    Busca e retorna o documento (como dict) que possui o ID informado.
    """
    documents = load_all_documents()
    for doc in documents:
        if doc.get("id") == document_id:
            return doc

    logger.warning(f"Documento com ID {document_id} não encontrado.")
    return None

def get_document_by_question_text(question_text: str) -> Optional[str]:
    """
    Busca o documento pelo texto da pergunta e retorna apenas o seu ID.
    """
    documents = load_all_documents()
    for doc in documents:
        # Verifica se o campo "question" existe e se o "text" confere com o parâmetro passado
        if doc.get("question", {}).get("text") == question_text:
            return doc.get("id")

    logger.warning(f"Documento com texto de pergunta '{question_text}' não encontrado.")
    return None