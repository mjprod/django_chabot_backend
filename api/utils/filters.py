import django_filters
from ..models import Knowledge,SubCategory,KnowledgeContent,Category
from django.db.models import Q

class KnowledgeFilter(django_filters.FilterSet):
    knowledge_uuid = django_filters.UUIDFilter(field_name="knowledge_uuid", lookup_expr="exact", label="Knowledge UUID")
    type = django_filters.ChoiceFilter(field_name="type", choices=Knowledge.TYPE_CHOICES, lookup_expr="iexact", label="Type")
    date_created = django_filters.DateTimeFromToRangeFilter(label="Date Created")
    last_updated = django_filters.DateTimeFromToRangeFilter(label="Last Updated")

    # Filters from category and subcategory
    category = django_filters.NumberFilter(field_name="category__id", lookup_expr="exact", label="Category ID")
    subcategory = django_filters.NumberFilter(field_name="subcategory__id", lookup_expr="exact", label="Subcategory ID")

    # Filters from KnowledgeContent
    status = django_filters.ChoiceFilter(field_name="knowledge_content__status", choices=KnowledgeContent.STATUS_CHOICES, lookup_expr="iexact", label="Status")
    language = django_filters.ChoiceFilter(field_name="knowledge_content__language", choices=KnowledgeContent.LANGUAGE_CHOICES, lookup_expr="iexact", label="Language")
    is_edited = django_filters.BooleanFilter(field_name="knowledge_content__is_edited", label="Is Edited")
    in_brain = django_filters.BooleanFilter(field_name="knowledge_content__in_brain", label="In Brain")

    class Meta:
        model = Knowledge
        fields = ['knowledge_uuid', 'category', 'subcategory', 'type', 
                  'date_created', 'last_updated', 'status', 'language', 
                  'is_edited', 'in_brain']

class SubCategoryFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name="category__id", lookup_expr="exact", label="Category ID")

    class Meta:
        model = SubCategory
        fields = ['category']