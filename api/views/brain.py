from rest_framework.response import Response
from rest_framework import status, viewsets
import rest_framework.exceptions as DRFException
from rest_framework.decorators import action

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend

from ..models import ( 
    Brain,
    KnowledgeContent
)

from ..api_serializers.brain import BrainSerializer
from ..api_serializers.knowledge import KnowledgeContentIDListSerializer

from ..utils.utils import CustomPagination
from ..utils.enum import KnowledgeContentStatus

from api.services.brain_manager import BrainManager
from api.services.config import CHROMA_BRAIN_COLLECTION


import logging


logger = logging.getLogger(__name__)

# TODO: This viewset needs to be set at Admin Level
class BrainViewSet(viewsets.ModelViewSet):
    brain_manager = BrainManager()
    queryset = Brain.objects.all()
    serializer_class = BrainSerializer
    filter_backends = (DjangoFilterBackend,)
    pagination_class = CustomPagination

    @action(detail=False, methods=["post"], url_path="bulk-add-to-brain")
    def bulk_add_to_brain(self, request, *args, **kwargs):
        """
        Bulk create Brain entries.
        - Only allows KnowledgeContent with APPROVED status.
        - Prevents duplicates if already in Brain Table.
        - Adds to chromadb (TODO).
        - Updates 'in_brain' field in KnowledgeContent.
        """
        serializer = KnowledgeContentIDListSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            knowledge_content_ids = set(serializer.validated_data.get("knowledge_content_ids"))

        knowledge_content_qs = KnowledgeContent.objects.filter(id__in=knowledge_content_ids)
        existing_ids = set(knowledge_content_qs.values_list("id", flat=True))  # IDs that exist in DB

        # Identify invalid IDs (not even in the KnowledgeContent)
        invalid_ids = knowledge_content_ids - existing_ids

        # Filter only approved knowledge that are not already in Brain
        valid_for_brain = knowledge_content_qs.filter(
            status=KnowledgeContentStatus.APPROVED.value,
            in_brain=False
        )

        valid_ids = set(valid_for_brain.values_list("id", flat=True))

        already_in_brain_ids = existing_ids - valid_ids  # IDs that exist but are not valid for Brain (wrong status/in_brain=True)
        failed_ids = invalid_ids | already_in_brain_ids  # Combine both sets

        successfully_processed = []

        # Start transaction to ensure consistency
        with transaction.atomic():
            brain_instances = [
                Brain(knowledge_content=kc) for kc in valid_for_brain
            ]
            Brain.objects.bulk_create(brain_instances)  # Bulk create for efficiency

            # Add to Chroma DB
            self.brain_manager.add_documents(CHROMA_BRAIN_COLLECTION, valid_for_brain)

            # Update 'in_brain' flag in KnowledgeContent
            KnowledgeContent.objects.filter(id__in=valid_ids).update(in_brain=True)

            successfully_processed = list(valid_ids)

        response_data = {
            "success": list(successfully_processed),
            "failed": list(failed_ids),
        }

        if failed_ids and not successfully_processed:
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)  # All failed
        elif failed_ids:
            return Response(response_data, status=status.HTTP_207_MULTI_STATUS)  # Some failed, some succeeded

        return Response(response_data, status=status.HTTP_201_CREATED)  # All successful


    @action(detail=False, methods=['post'], url_path='bulk-remove-from-brain')
    def bulk_remove_from_brain(self, request, *args, **kwargs):
        """
        Handles bulk deletion of knowledge_content_ids entries.
        - Removes them from chromadb. (TODO)
        - Remove from Brain DB table
        - Updates `in_brain` to False.
        - Resets `status` to NEEDS_REVIEW in KnowledgeContent.
        """
        serializer = KnowledgeContentIDListSerializer(data=request.data)
        
        # Validate the input data
        if serializer.is_valid(raise_exception=True):
            knowledge_content_ids = serializer.validated_data.get("knowledge_content_ids")

            brain_instances = Brain.objects.filter(knowledge_content_id__in=knowledge_content_ids)

            existing_knowledge_content_ids = set(brain_instances.values_list("knowledge_content_id", flat=True))
            non_existent_ids = set(knowledge_content_ids) - existing_knowledge_content_ids

            if not brain_instances.exists():
                return Response(
                    {"detail": "No valid Brain records found for the provided IDs."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            with transaction.atomic():

                # Remove from brain db and chromadb vector store
                brain_instances.delete()
                self.brain_manager.delete_documents(CHROMA_BRAIN_COLLECTION, existing_knowledge_content_ids)

                KnowledgeContent.objects.filter(id__in=existing_knowledge_content_ids).update(
                    in_brain=False,
                    status=KnowledgeContentStatus.NEEDS_REVIEW.value
                )

            response_data = {
                "success": list(existing_knowledge_content_ids),
                "failed": list(non_existent_ids),
            }

            return Response(response_data, status=status.HTTP_207_MULTI_STATUS if non_existent_ids else status.HTTP_200_OK)


    # this api will delete entire chromadb collection! can be a dangerious operation!
    @action(detail=False, methods=['post'], url_path='sync-brain-knowledge')
    def sync_brain_knowledge(self, request):
        """
        Reloads the Brain database:
        - Clears existing Brain entries.
        - Inserts all KnowledgeContent where in_brain=True.
        - Re-add to ChromaDB.
        """
        with transaction.atomic():
            # Delete all existing Brain records
            Brain.objects.all().delete()
    
            # Fetch KnowledgeContent where in_brain=True
            knowledge_content_qs = KnowledgeContent.objects.filter(in_brain=True)

            brain_instances = [Brain(knowledge_content=kc) for kc in knowledge_content_qs]
            Brain.objects.bulk_create(brain_instances)

            # Re-add knowledge content to ChromaDB
            self.brain_manager.delete_collection(CHROMA_BRAIN_COLLECTION)
            self.brain_manager.load_knowledge_content_to_collection(CHROMA_BRAIN_COLLECTION)
            
        return Response(
            {"message": "Brain database synced successfully", "inserted_count": len(brain_instances)},
            status=status.HTTP_200_OK
        )
    

    @action(detail=False, methods=['post'], url_path='get-brain-docs')
    def get_brain_doc_by_ids(self, request):

        serializer = KnowledgeContentIDListSerializer(data=request.data)
        
        # Validate the input data
        if serializer.is_valid(raise_exception=True):
            knowledge_content_ids = serializer.validated_data.get("knowledge_content_ids")
            result = self.brain_manager.get_by_ids(CHROMA_BRAIN_COLLECTION, knowledge_content_ids)

        return Response({"message": result}, status=status.HTTP_200_OK)
    

    # override update
    def update(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied(
            "Direct updates to knowledge in the Brain are not permitted. Please delete the existing knowledge first, and add new knowledge through the admin panel for review."
        )
    
    # override partial update
    def partial_update(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied(
            "Direct updates to knowledge in the Brain are not permitted. Please delete the existing knowledge first, and add new knowledge through the admin panel for review."
        )
    

    def create(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied("Use bulk create instead of single create.")

        # override
    def destroy(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied("Use bulk delete instead of single delete.")