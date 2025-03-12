from rest_framework import serializers
from ..models import Category, SubCategory, Knowledge, KnowledgeContent

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = '__all__'


class KnowledgeContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KnowledgeContent
        fields = '__all__'


class KnowledgeSerializer(serializers.ModelSerializer):
    knowledge_content = serializers.SerializerMethodField()
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)

    class Meta:
        model = Knowledge
        fields = ['id', 'knowledge_uuid', 'category', 'subcategory', 'type', 'knowledge_content']

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
            return None  # Exclude this Knowledge object from response
        return data
    

class KnowledgeContentIDListSerializer(serializers.Serializer):
    knowledge_content_ids = serializers.ListField(
        child=serializers.IntegerField(),  # Each item in the list is an integer (ID)
        required=True
    )
