import json
import os

def get_document_by_id(document_id: str) -> dict:
    # Sobe dois níveis a partir do diretório atual
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    file_path = os.path.join(base_dir, "data", "database_en.json")
    
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for doc in data:
        if doc.get("id") == document_id:
            return doc

    print(f"Documento com ID {document_id} não encontrado.")
    return None

if __name__ == '__main__':
    doc = get_document_by_id("0027")
    if doc:
        print("Documento encontrado:")
        print(json.dumps(doc, indent=4, ensure_ascii=False))