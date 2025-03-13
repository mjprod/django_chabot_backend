import logging
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import status

from django_filters.rest_framework import DjangoFilterBackend

from ..models import (
    Category, 
    SubCategory, 
)

from ..api_serializers.knowledge import (
    CategorySerializer, 
    SubCategorySerializer
)

from ..utils.filters import SubCategoryFilter
from ..utils.enum import CategoryColor


logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SubCategoryFilter