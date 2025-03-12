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

    def list(self, request, *args, **kwargs):
        """Override list to add color mapping."""
        queryset = self.filter_queryset(self.get_queryset())  # Apply any filters
        serialized_data = CategorySerializer(queryset, many=True).data

        # Inject color based on category ID
        for category in serialized_data:
            category["color"] = CategoryColor.get_color_by_id(category["id"])

        return Response(serialized_data, status=status.HTTP_200_OK)


class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all()
    serializer_class = SubCategorySerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = SubCategoryFilter