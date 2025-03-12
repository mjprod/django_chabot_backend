from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

import logging

# from ..serializers import (
#    UpdateAnswerBrain,
# )

# from api.chatbot import (
#   update_document_by_custom_id,
# )

logger = logging.getLogger(__name__)

"""
class ListReviewAndUpdateBrainView(APIView):
    def get(self, request, *args, **kwargs):
        db = None
        try:
            db = MongoDB.get_db()
            query = {
                "$expr": {
                    "$lt": [
                        {"$size": {"$ifNull": ["$review_status", []]}},
                        3
                    ]
                }
            }
            results = list(db.review_and_update_brain.find(query))
        
            for doc in results:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
        
            return Response(results, status=status.HTTP_200_OK)
    
        except Exception as e:
                logger.exception("Error retrieving session ids")
                return Response(
                {"error": f"Error retrieving session ids: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
"""
'''
class UpdateReviewStatusView(APIView):
    def post(self, request, *args, **kwargs):
        """
        Update the review_status field of a document.
        Expects a JSON payload with:
            - doc_id: your custom document id (e.g. "0072")
            - review_status: a list of language codes (e.g. ["en", "ms"])
        """
        data = request.data
        doc_id = data.get("doc_id")
        review_status = data.get("review_status")
        review_text = data.get("review_text")

        if not doc_id or not review_status:
            return Response(
                {"error": "doc_id and review_status are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        db = None
        try:

            db = MongoDB.get_db()
            # Build the field path for the answer text, e.g., "answer.detailed.en"
            field_path = f"answer.detailed.{review_status}"
            
            # Update operation:
            #  - $set to update the specific language answer text
            #  - $addToSet to add the language code to review_status if not already present
            result = db.review_and_update_brain.update_one(
                {"id": doc_id},
                {
                    "$set": {field_path: review_text},
                    "$addToSet": {"review_status": review_status}
                }
            )
            
            if result.modified_count > 0:
                return Response(
                    {"message": f"Document {doc_id} updated successfully."},
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {"error": f"Document {doc_id} not found or not updated."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            logger.exception("Error updating review_status")
            return Response(
                {"error": f"Error updating review_status: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
'''

"""
class UpdateBrainView(APIView):
    def get(self, request):
        try:
            # Validate input data
            input_serializer = UpdateAnswerBrain(data=request.data)
            if not input_serializer.is_valid():
                logger.error(f"Validation failed: {input_serializer.errors}")
                return Response(
                    {"error": "Invalid input data", "details": input_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            doc_id = input_serializer.validated_data["doc_id"]
            answer_en = input_serializer.validated_data["answer_en"]
            answer_ms = input_serializer.validated_data["answer_ms"]
            answer_cn = input_serializer.validated_data["answer_cn"]

            conversations = update_document_by_custom_id(
                doc_id, answer_en, answer_ms, answer_cn)
            
            data = {
                "conversations": conversations,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Error retrieving dashboard counts: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )    
"""


'''
    def update_chroma_document(doc_id, new_data):
    """
    Update an existing document in the ChromaDB collection.
    :param store: The ChromaDB collection object
    :param doc_id: The unique ID of the document to update
    :param new_data: Dictionary containing updated data fields
    """
    try:

        if store:  # Only search if store was successfully created
            search_results = search_by_id(store, "0068")  # Replace "0001" with your ID
            print("Search Results:", search_results)
        else:
            print("Vector store creation failed, cannot perform search.")

        return True
        all_docs = store.get()

        for key, value in all_docs.items():
                print(f"{key}: {value}")

        existing_docs = store.get(ids=[doc_id], include=["documents", "metadatas"])
        
        if not existing_docs["documents"]:
            print(f"Document with ID {doc_id} not found.")
            return False

        # Retrieve the existing document
        existing_doc = json.loads(existing_docs["documents"][0])  # Convert back to dictionary if stored as JSON string

        # Merge the existing document with new data
        updated_doc = {**existing_doc, **new_data}

        # Remove the old document before re-adding
        store.delete(ids=[doc_id])

        # Reinsert the updated document
        store.add(
            documents=[json.dumps(updated_doc)],  # Store as JSON string
            ids=[doc_id],
            metadatas=[updated_doc.get("metadata", {})]
        )

        print(f"Document with ID {doc_id} updated successfully.")
        return True

    except Exception as e:
        print(f"Error updating document: {e}")
        return False
    
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
                "category": ",".join(existing_metadata.get("category", [])),
                "subCategory": existing_metadata.get("subCategory", ""),
                "difficulty": existing_metadata.get("difficulty", 0),
                "confidence": existing_metadata.get("confidence", 0.0),
                "intent": doc["question"].get("intent", ""),
                "variations": ", ".join(doc["question"].get("variations", [])),
                "conditions": ", ".join(doc["answer"].get("conditions", [])),
            },
        )

        store.add_documents(documents=[new_document])
        return (f"ID '{custom_id}' updated ")
    except Exception as e:
        print(f"Error to update document: {str(e)}")
'''
