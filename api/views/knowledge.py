import logging
import uuid

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status, viewsets
from rest_framework.decorators import action
import rest_framework.exceptions as DRFException

import django.core.exceptions as CoreException
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q

from ..models import (
    Category, 
    SubCategory, 
    Knowledge,
    KnowledgeContent
)

from ..api_serializers.knowledge import (
    KnowledgeSerializer,
    KnowledgeContentSerializer,
)

from ..utils.utils import CustomPagination
from ..utils.filters import KnowledgeFilter
from ..utils.enum import KnowledgeContentStatus, KnowledgeType


logger = logging.getLogger(__name__)


class KnowledgeContentViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    queryset = KnowledgeContent.objects.filter(in_brain=False)
    serializer_class = KnowledgeContentSerializer

    # override create()
    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        knowledge_uuid = data.pop('knowledge_uuid', None)

        try:
            knowledge={}

            if knowledge_uuid:
                knowledge = Knowledge.objects.get(knowledge_uuid=knowledge_uuid)
            else:
                category_id = data.pop('category', None)
                subcategory_id = data.pop('subcategory', None)
                type = data.pop('type', KnowledgeType.FAQ.value)
                category = Category.objects.get(id=category_id) if category_id else None
                subcategory = SubCategory.objects.get(id=subcategory_id) if subcategory_id else None

                knowledge = Knowledge.objects.create(
                    knowledge_uuid=uuid.uuid4(),
                    type=type,
                    category=category,
                    subcategory=subcategory
                )

            restricted_fields = ['status', 'is_edited', 'in_brain', 'date_created', 'last_updated']

            for field in restricted_fields:
                data.pop(field, None)

            data['knowledge'] = knowledge.id

            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)

            # TODO: generate other knowledge content for two languages

            serializer.save() 

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except (Knowledge.DoesNotExist, SubCategory.DoesNotExist, Category.DoesNotExist):
            return Response({"error": "Knowledge, category or subcategory do not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except CoreException.ValidationError as e:
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)


    # override destroy func
    def destroy(self, request, *args, **kwargs):
        knowledge_content_instance = self.get_object()

        if knowledge_content_instance.status != KnowledgeContentStatus.REJECT.value or knowledge_content_instance.in_brain == True:
            raise DRFException.ValidationError(
                "This knowledge cannot be deleted because it is either not in 'reject' status or it is already in the brain."
            )
        knowledge_content_instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])

        if not ids:
            raise DRFException.ValidationError("The 'ids' field is required.")

        # Validate that all IDs are valid Knowledge IDs and can be deleted
        knowledge_content_objects = self.get_queryset().filter(id__in=ids, status=KnowledgeContentStatus.REJECT.value)
        invalid_entries = self.get_queryset().filter(id__in=ids, in_brain=True)
        
        if knowledge_content_objects.count() != len(ids) or invalid_entries.exists():
            raise DRFException.ValidationError(
                "One or more of the provided IDs do not exist, are not in 'reject' status, or cannot be deleted because they are already in the brain."
            )

        knowledge_content_objects.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


    # override partial_update
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        data = request.data.copy()

        # allowed fields for partial update
        allowed_fields = ['question', 'answer', 'content', 'status', 'language']
        invalid_fields = [field for field in data.keys() if field not in allowed_fields]
        if invalid_fields:
            raise DRFException.ValidationError(f"Cannot update the following fields: {', '.join(invalid_fields)}")
    
        allowed_statuses = {
            KnowledgeContentStatus.REJECT.value,
            KnowledgeContentStatus.PRE_APPROVED.value,
            KnowledgeContentStatus.NEEDS_REVIEW.value,
        }
        
        # it will raise error if other statuses being passed in this PATCH api (can only updated with NEEDS_APPROVAL/ PRE_APPROVED/ REJECT)
        if "status" in data and data["status"] not in allowed_statuses:
            allowed_names = [status.name for status in KnowledgeContentStatus if status.value in allowed_statuses]
            raise DRFException.ValidationError(f"Invalid status. Allowed values: {', '.join(allowed_names)}")
        
        # ignore other fields if the status is set to "reject"
        if data.get("status") == KnowledgeContentStatus.REJECT.value:
            data = {"status": KnowledgeContentStatus.REJECT.value}
        else:
            # If the status is not 'reject', check if other fields have been edited
            is_edited = False
            if not getattr(instance, "is_edited"):
                for field in data.keys():
                    instance_value = getattr(instance, field)
                    data_value = data.get(field)
                    if instance_value != data_value:
                        is_edited = True

            if is_edited:
                data['is_edited'] = is_edited

        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)



    # Customise post bulk change any status to a new status 
    # input: knowledege content ids, change tostatus
    @action(detail=False, methods=['post'], url_path="bulk-update-status")
    def bulk_update_status(self, request):
        """
        Custom endpoint to bulk update the status of multiple KnowledgeContent records.
        Input: List of knowledge content IDs and the new status.
        """

        # TODO: write a serialiser for the input!
        knowledge_content_ids = request.data.get('knowledge_content_ids')
        new_status = request.data.get('new_status')

        if not knowledge_content_ids or new_status is None:
            return Response(
                {"error": "Both 'knowledge_content_ids' and 'new_status' are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate if the new status is a valid choice
        valid_statuses = [choice[0] for choice in KnowledgeContent.STATUS_CHOICES]
        if new_status not in valid_statuses:
            return Response(
                {"error": f"Invalid status. Valid choices are: {valid_statuses}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update KnowledgeContent records
        updated_count = KnowledgeContent.objects.filter(id__in=knowledge_content_ids).update(status=new_status)

        return Response(
            {"message": f"Successfully updated {updated_count} records."},
            status=status.HTTP_200_OK
        )


class KnowledgeViewSet(viewsets.ModelViewSet):
    queryset = Knowledge.objects.all()  # This allows DRF to infer the `basename`
    serializer_class = KnowledgeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = KnowledgeFilter
    pagination_class = CustomPagination

    def get_serializer_context(self):
        context = super().get_serializer_context()
        
        # Get multiple filter parameters from the request
        status = self.request.query_params.get('status', None)
        language = self.request.query_params.get('language', None)
        is_edited = self.request.query_params.get('is_edited', None)
        
        # Add the filters to the context if provided
        if status:
            context['status'] = status
        if language:
            context['language'] = language
        if is_edited is not None:  # Check if it's provided (True/False)
            context['is_edited'] = is_edited
        
        return context
    
    def get_queryset(self):
        return Knowledge.objects.filter(knowledge_content__in_brain=False).distinct()

    def create(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied("Create is disabled for this resource.")
    
    def update(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied("Update is disabled for this resource.")


class KnowledgeSummaryAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Get 'in_brain' filter from query parameters (defaults to False if not provided)
        in_brain_value = request.query_params.get('in_brain', 'false').lower() == 'true'

        knowledge_summary = Category.objects.annotate(
            knowledge_count=Count(
                'knowledge_category',
                filter=Q(knowledge_category__knowledge_content__in_brain=in_brain_value),
                distinct=True
            )
        ).values('id','name', 'knowledge_count').order_by('-knowledge_count') 

        return Response({"categories": list(knowledge_summary)})


    
class KnowledgeContentSummaryAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # Get 'in_brain' filter from query parameters (defaults to False if not provided)
        in_brain_value = request.query_params.get('in_brain', 'false').lower() == 'true'

        # Aggregate knowledge count per category where related KnowledgeContent has in_brain=False
        knowledge_summary = Category.objects.annotate(
            knowledge_count=Count(
                'knowledge_category', 
                filter=Q(knowledge_category__knowledge_content__in_brain=in_brain_value)
            )
        ).values('id', 'name', 'knowledge_count')

        formatted_summary = [
            {
                "id": item["id"],
                "name": item["name"],
                "knowledge_content_count": item["knowledge_count"]
            }
            for item in knowledge_summary
        ]

        return Response({"categories": list(formatted_summary)})




# class KnowledgeContentSummaryAPIView(APIView):

#     def get(self, request, *args, **kwargs):
#         # Aggregate knowledge content count per category
#         category_summary = Category.objects.annotate(
#             knowledge_content_count=Count('knowledge_category__knowledge_content')
#         ).values('id', 'name', 'knowledge_content_count')

#         return Response({"categories": list(category_summary)})


# class KnowledgeViewSet(viewsets.ModelViewSet):
#     queryset = Knowledge.objects.all()
#     serializer_class = KnowledgeSerializer
#     filter_backends = (DjangoFilterBackend,)
#     filterset_class = KnowledgeFilter
#     pagination_class = CustomPagination

#     def get_queryset(self):
#         # Return only Knowledge objects where in_brain is False
#         return Knowledge.objects.filter(in_brain=False)

#     def get_object(self):
#        return get_object_or_404(self.get_queryset(), pk=self.kwargs["pk"])

#     def create(self, request, *args, **kwargs):
#         data = request.data.copy()

#         # Remove fields that should not be passed
#         restricted_fields = ['status', 'is_edited', 'in_brain', 'date_created', 'last_updated']
#         for field in restricted_fields:
#             data.pop(field, None)

#         serializer = self.get_serializer(data=data)
#         serializer.is_valid(raise_exception=True)

#         self.perform_create(serializer)
#         headers = self.get_success_headers(serializer.data)

#         return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


#     # override partial_update
#     def partial_update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         data = request.data.copy()

#         # allowed fields for partial update
#         allowed_fields = ['question', 'answer', 'content', 'status']
#         invalid_fields = [field for field in data.keys() if field not in allowed_fields]
#         if invalid_fields:
#             raise ValidationError(f"Cannot update the following fields: {', '.join(invalid_fields)}")
        
#         # ignore other fields if the status is set to "reject"
#         if data.get("status") == KnowledgeStatus.REJECT.value:
#             data = {"status": KnowledgeStatus.REJECT.value}
#         else:
#             # If the status is not 'reject', check if other fields have been edited
#             is_edited = False
#             if not getattr(instance, "is_edited"):
#                 for field in data.keys():
#                     instance_value = getattr(instance, field)
#                     data_value = data.get(field)
#                     if instance_value != data_value:
#                         is_edited = True

#             if is_edited:
#                 data['is_edited'] = is_edited

#         serializer = self.get_serializer(instance, data=data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         self.perform_update(serializer)

#         return Response(serializer.data)