import django_filters
from ..models import Knowledge,SubCategory,KnowledgeContent,Category
from django.db.models import Q

class KnowledgeFilter(django_filters.FilterSet):
    knowledge_uuid = django_filters.UUIDFilter(field_name="knowledge_uuid", lookup_expr="exact", label="Knowledge UUID")
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='iexact')
    subcategory = django_filters.CharFilter(field_name='subcategory__name', lookup_expr='iexact')
    type = django_filters.ChoiceFilter(choices=Knowledge.TYPE_CHOICES, label="Type")
    date_created = django_filters.DateTimeFromToRangeFilter(label="Date Created")
    last_updated = django_filters.DateTimeFromToRangeFilter(label="Last Updated")

    class Meta:
        model = Knowledge
        fields = ['knowledge_uuid','category', 'subcategory', 'type', 'date_created', 'last_updated']


class SubCategoryFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='iexact')

    class Meta:
        model = SubCategory
        fields = ['category']