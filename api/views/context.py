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

from api.models import (
    Context
)

from api.api_serializers.knowledge import (
    Context,
)

from api.utils.utils import CustomPagination



logger = logging.getLogger(__name__)


class ContextViewSet(viewsets.ModelViewSet):
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)

    # override create()
    def create(self, request, *args, **kwargs):
        pass