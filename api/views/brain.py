from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.exceptions import NotFound,ValidationError,PermissionDenied
from rest_framework.decorators import action

from django_filters.rest_framework import DjangoFilterBackend


from ..models import ( 
    Knowledge
)

from ..api_serializers.knowledge import (
    KnowledgeSerializer,
)

from ..utils.utils import CustomPagination
from ..utils.filters import KnowledgeFilter

import logging


logger = logging.getLogger(__name__)


class BrainViewSet(viewsets.ModelViewSet):
    # only filter the one is_brain == true
    queryset = Knowledge.objects.all()
    serializer_class = KnowledgeSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = KnowledgeFilter
    pagination_class = CustomPagination

    # POST 
    # if status==approved,
    # add to chromadb
    # if success
    # change in_brain to true 

    # POST 
    # remove from brain
    # if success
    # change in_brain to false
    # status == needs_approval