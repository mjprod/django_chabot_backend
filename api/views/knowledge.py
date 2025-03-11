from rest_framework.response import Response
from rest_framework import status, viewsets

import rest_framework.exceptions as DRFException
import django.core.exceptions as CoreException

from rest_framework.decorators import action

from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404

from ..models import (
    Category, 
    SubCategory, 
    Knowledge,
    KnowledgeContent
)

from ..api_serializers.knowledge import (
    KnowledgeSerializer,
    KnowledgeContentSerializer,
    CategorySerializer, 
    SubCategorySerializer
)

from ..utils.utils import CustomPagination
from ..utils.filters import KnowledgeFilter, SubCategoryFilter
from ..utils.enum import KnowledgeStatus

import logging
import uuid

from rest_framework import filters


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
                type = data.pop('type', 'FAQ')
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
            serializer.save() 

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        except (Knowledge.DoesNotExist, SubCategory.DoesNotExist, Category.DoesNotExist):
            return Response({"error": "Knowledge resources do not exist."}, status=status.HTTP_400_BAD_REQUEST)
        except CoreException.ValidationError as e:
            return Response({"error": e}, status=status.HTTP_400_BAD_REQUEST)


    # override destroy func
    def destroy(self, request, *args, **kwargs):
        knowledge_content_instance = self.get_object()

        if knowledge_content_instance.status != KnowledgeStatus.REJECT.value:
            raise DRFException.ValidationError("This knowledge cannot be deleted because it is not in 'reject' status.")

        knowledge_content_instance.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request, *args, **kwargs):
        ids = request.data.get('ids', [])

        if not ids:
            raise DRFException.ValidationError("The 'ids' field is required.")

        # Validate that all IDs are valid Knowledge IDs
        knowledge_content_objects = self.get_queryset().filter(id__in=ids, status=KnowledgeStatus.REJECT.value)
        if knowledge_content_objects.count() != len(ids):
            raise DRFException.ValidationError("One or more of the provided IDs do not exist, or cannot be deleted because they are not in 'reject' status.")

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
        
        # ignore other fields if the status is set to "reject"
        if data.get("status") == KnowledgeStatus.REJECT.value:
            data = {"status": KnowledgeStatus.REJECT.value}
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


class KnowledgeViewSet(viewsets.ModelViewSet):
    queryset = Knowledge.objects.all()
    serializer_class = KnowledgeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = KnowledgeFilter

    def create(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied("Create is disabled for this resource.")
    
    def update(self, request, *args, **kwargs):
        raise DRFException.PermissionDenied("Update is disabled for this resource.")


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer



class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SubCategoryFilter


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