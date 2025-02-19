import json
import os

def update_question_text(file_path, document_id, new_text):
    # Verifica se o arquivo existe
    if not os.path.exists(file_path):
        print(f"Arquivo não encontrado: {file_path}")
        return

    # Carrega os dados do arquivo JSON (assumindo que seja uma lista de documentos)
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Procura o documento com o ID especificado
    found = False
    for doc in data:
        if doc.get("id") == document_id:
            # Atualiza o campo "question.text" com o novo valor
            doc["question"]["text"] = new_text
            found = True
            break

    if not found:
        print(f"Documento com ID {document_id} não encontrado.")
        return

    # Escreve os dados atualizados de volta no arquivo
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print("Documento atualizado com sucesso.")

if __name__ == '__main__':
    # Caminho para o arquivo JSON de teste (certifique-se de que ele exista)
    file_path = "database.json"

    # Defina o ID do documento e o novo texto que deseja atribuir
    document_id = "0027"
    new_text = "Is the deposit system experiencing issues right now?"

    update_question_text(file_path, document_id, new_text)