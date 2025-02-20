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

# if __name__ == '__main__':
   # doc = get_document_by_id("0027")
   # if doc:
       # print("Documento encontrado:")
       # print(json.dumps(doc, indent=4, ensure_ascii=False))