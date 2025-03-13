import json
import os
import logging
from typing import List, Optional, Dict, Any

logger = logging.getLogger(__name__)


def flatten_data(data: Any) -> List[Dict]:
    """
    If 'data' is a nested list, flatten it and return a list of dictionaries.
    If 'data' is already a list of dictionaries, return it.
    """
    flattened = []
    if isinstance(data, list):
        for item in data:
            if isinstance(item, list):
                flattened.extend(flatten_data(item))
            elif isinstance(item, dict):
                flattened.append(item)
            else:
                logger.error(f"Unexpected item: {item}")
    elif isinstance(data, dict):
        flattened.append(data)
    else:
        logger.error(f"Unexpected data type: {type(data)}")
    return flattened


def load_all_documents() -> List[Dict]:
    base_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    database_files = [
        "database_part_1.json",
    ]

    all_documents = []
    for file_name in database_files:
        file_path = os.path.join(base_dir, file_name)
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            continue

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            docs = flatten_data(data)
            all_documents.extend(docs)
        except Exception as e:
            logger.exception(f"Error reading {file_path}: {e}")

    return all_documents


def get_document_count() -> Optional[int]:
    documents = load_all_documents()
    count = len(documents)
    print(f"Total documents: {count}")
    return count


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

    logger.warning(f"Document with question text '{question_text}' not found.")
    return None


def update_answer_detailed(
    document: Dict, answer_en: str, answer_ms: str, answer_cn: str
):
    """
    Update the value of answer.detailed.en for the given document (identified by its 'id')
    across multiple JSON files. If the document is found in one file, update that file in-place.

    :param document: The document dictionary (must contain the key "id").
    :param new_value: The new value for answer.detailed.en.
    """
    base_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "data"
    )
    database_files = [
        "database_part_1.json",
        "database_part_2.json",
        "database_part_3.json",
        "database_part_4.json",
        "database_part_5.json",
        "database_part_6.json",
        "database_part_7.json",
        "database_part_8.json",
        "database_part_9.json",
    ]

    found = False

    for file_name in database_files:
        file_path = os.path.join(base_dir, file_name)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Flatten the data in case it is nested
            docs = flatten_data(data)
            updated = False

            # Iterate through documents to find the one with the matching id
            for doc in docs:
                if doc.get("id") == document.get("id"):
                    if "answer" in doc and "detailed" in doc["answer"]:
                        doc["answer"]["detailed"]["en"] = answer_en
                        doc["answer"]["detailed"]["ms"] = answer_ms
                        doc["answer"]["detailed"]["cn"] = answer_cn
                        updated = True
                        found = True
                        break  # Document found; update and exit the loop for this file

            if updated:
                # Write back to the same file
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(docs, f, indent=4, ensure_ascii=False)
                logger.debug(
                    f"Document {document.get('id')} updated successfully in {file_name}."
                )
                break  # Exit the overall loop since the document has been updated
            else:
                logger.debug(f"Document {document.get('id')} not found in {file_name}.")
        except Exception as e:
            logger.debug(f"Error updating file {file_path}: {str(e)}")

    if not found:
        logger.debug(f"Document {document.get('id')} not found in any file.")
