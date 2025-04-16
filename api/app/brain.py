from langchain_community.vectorstores import Chroma

from api.chatbot import (
    store,
)

from api.views.brain_file_reader import (
    get_document_by_id,
    update_answer_detailed,
    insert_new_document,
    get_next_id_from_json
)
    
def search_by_id(store: Chroma, custom_id: str):
    results = store.get(
        where={"id": custom_id},
        include=["documents", "metadatas"]
    )
    return results

def update_document_by_custom_id(custom_id: str, answer_en: str, answer_ms: str, answer_cn: str):
    try:
        search_results = store.get(
            where={"id": custom_id},
            include=["metadatas","documents"]
        )

        if not search_results['ids']:
            print(f"Document ID '{custom_id}' not found.")
            return

        document_id = search_results['ids'][0]
        doc = get_document_by_id(document_id) 
        
        if doc:
            update_answer_detailed(doc, answer_en, answer_ms, answer_cn)

        existing_metadata = search_results['metadatas'][0]
        document = search_results['documents'][0]
        question_text = document.split("\n")[0].replace("Question: ", "").strip()

        new_document = CustomDocument(
            id=custom_id,
            page_content=(
                f"Question: {question_text}\n"
                f"Answer: {answer_en}"
            ),
            metadata={
                "id": doc.get("id", ""),
                "category": ",".join(existing_metadata.get("category", [])),
                "subCategory": existing_metadata.get("subCategory", ""),
                "difficulty": existing_metadata.get("difficulty", 0),
                "confidence": existing_metadata.get("confidence", 0.0),
                "intent": doc["question"].get("intent", ""),
                "variations": ", ".join(doc["question"].get("variations", [])),
                "conditions": ", ".join(doc["answer"].get("conditions", [])),
            },
        )

        store.add(documents=[new_document])
        return (f"ID '{custom_id}' updated ")
    except Exception as e:
        print(f"Error to update document: {str(e)}")

def reload_vector_store(collection_name="RAG", persist_directory="./chroma_db", embedding_model=None):
    return Chroma(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_function=embedding_model
    )
         
def insert_document(question_text, answer_en: str, answer_ms: str, answer_cn: str):
    try:
        
        new_id = get_next_id_from_json()
        if not new_id:
            return "Error obtaining the next ID."
    
        new_document = {
            "id": new_id,
            "question": {
            "text": question_text,
            "variations": [],
            "intent": "general_inquiry",
            "languages": {
                "en": "",
                "ms": "",
                "cn": ""
            }
        },
        "answer": {
            "detailed": {
                "en": answer_en,
                "ms": answer_ms,
                "cn": answer_cn
            },
            "conditions": []
        },
        "metadata": {
            "category": ["general"],
            "subCategory": "general_inquiry",
            "difficulty": 0,
            "confidence": 0.5,
            "dateCreated": "",
            "lastUpdated": "",
            "version": "1.0",
            "source": "",
            "status": "active"
        },
        "context": {
            "relatedTopics": [],
            "prerequisites": [],
            "followUpQuestions": {
                "en": [],
                "ms": [],
                "cn": []
            }
        },
        "usage": {
            "searchFrequency": 0,
            "successRate": 0,
            "lastQueried": None
        },
        "review_status": []
        }

        insert_new_document(new_document)

        new_document = CustomDocument(
            id=new_id,
            page_content=(
                f"Question: {question_text}\n"
                f"Answer: {answer_en}"
            ),
            metadata={
                "id": new_id,
                "category": ",".join(["general"]),
                "subCategory": "general_inquiry",
                "difficulty":  0,
                "confidence": 0.5,
                "intent": "general_inquiry",
                "variations": ",".join(["general"]),
                "conditions": ",".join(["general"])
            },
        )

        store.add_documents(documents=[new_document])
        store.persist()
        return (f"ID '{new_id}' updated ")
    
    except Exception as e:
        print(f"Error to update document: {str(e)}")

        
