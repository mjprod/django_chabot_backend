from rest_framework import serializers
import logging
from ..models import Category, SubCategory, Knowledge, KnowledgeContent, Context
from api.utils.enum import CategoryColor


logger = logging.getLogger(__name__)

class CategorySerializer(serializers.ModelSerializer):
    color = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'color']
    
    def get_color(self, obj):
        return CategoryColor.get_color_by_id(obj.id)


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = '__all__'


class KnowledgeContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeContent
        fields = '__all__'


class ContextSerializer(serializers.ModelSerializer):
    class Meta:
        model = Context
        fields = '__all__'


class KnowledgeListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = super().to_representation(data)
        return [item for item in data if item is not None] 


class KnowledgeSerializer(serializers.ModelSerializer):
    knowledge_content = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    context = ContextSerializer(read_only=True)

    class Meta:
        model = Knowledge
        fields = ['id', 'knowledge_uuid', 'category', 'subcategory', 'type', 'context', 'knowledge_content']
        list_serializer_class = KnowledgeListSerializer

    # def get_knowledge_content(self, obj):
    #     # Filter KnowledgeContent with in_brain=False
    #     filtered_content = obj.knowledge_content.filter(in_brain=False)
    #     return KnowledgeContentSerializer(filtered_content, many=True).data or None


    def get_knowledge_content(self, obj):
        status_filter = self.context.get('status', None)
        language_filter = self.context.get('language', None)
        is_edited_filter = self.context.get('is_edited', None)

        # Filter KnowledgeContent based on in_brain=False only!
        init_knowledge_content_qs = obj.knowledge_content.filter(in_brain=False)
        knowledge_content_qs = init_knowledge_content_qs  # Initialize with in_brain=False filter


        if status_filter:
            knowledge_content_qs = knowledge_content_qs.filter(status=status_filter)

        if language_filter:
            knowledge_content_qs = knowledge_content_qs.filter(language=language_filter)

        if is_edited_filter is not None: 
            knowledge_content_qs = knowledge_content_qs.filter(is_edited=is_edited_filter)

        if knowledge_content_qs.exists():
            return KnowledgeContentSerializer(init_knowledge_content_qs, many=True).data 
        else:
            return None
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get("knowledge_content"):  # If knowledge_content is empty after filtering
            logger.info((f"Removing knowledge object {instance.id}") )
            return None  # Exclude this Knowledge object from response
        return data
    


class KnowledgeContentIDListSerializer(serializers.Serializer):
    knowledge_content_ids = serializers.ListField(
        child=serializers.IntegerField(),  # Each item in the list is an integer (ID)
        required=True
    )
