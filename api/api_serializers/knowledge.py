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
    knowledge_content = KnowledgeContentSerializer(many=True, read_only=True)
    category = CategorySerializer(read_only=True)
    subcategory = SubCategorySerializer(read_only=True)
    class Meta:
        model = Knowledge
        fields = '__all__'
