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

    def get_knowledge_content(self, obj):
        # Filter KnowledgeContent with in_brain=False
        filtered_content = obj.knowledge_content.filter(in_brain=False)
        return KnowledgeContentSerializer(filtered_content, many=True).data
