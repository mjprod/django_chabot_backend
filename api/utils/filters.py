import django_filters
from ..models import Knowledge,SubCategory,KnowledgeContent,Category
from django.db.models import Q

class KnowledgeFilter(django_filters.FilterSet):
    knowledge_uuid = django_filters.UUIDFilter(field_name="knowledge_uuid", lookup_expr="exact", label="Knowledge UUID")
    type = django_filters.CharFilter(field_name="type", lookup_expr="iexact")
    date_created = django_filters.DateTimeFromToRangeFilter(label="Date Created")
    last_updated = django_filters.DateTimeFromToRangeFilter(label="Last Updated")

    # Filters from category and subcategory
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='iexact')
    subcategory = django_filters.CharFilter(field_name='subcategory__name', lookup_expr='iexact')

    # Filters from KnowledgeContent
    status = django_filters.CharFilter(field_name="knowledge_content__status", lookup_expr='iexact')
    language = django_filters.CharFilter(field_name="knowledge_content__language", lookup_expr='iexact')
    is_edited = django_filters.BooleanFilter(field_name="knowledge_content__is_edited", label="Is Edited")
    in_brain = django_filters.BooleanFilter(field_name="knowledge_content__in_brain", label="In Brain")

    class Meta:
        model = Knowledge
        fields = ['knowledge_uuid', 'category', 'subcategory', 'type', 'date_created', 'last_updated', 'status', 'language', 'is_edited', 'in_brain']

class SubCategoryFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='iexact')

    class Meta:
        model = SubCategory
        fields = ['category']