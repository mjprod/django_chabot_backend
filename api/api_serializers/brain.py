from rest_framework import serializers
from ..models import Brain

class BrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brain
        fields = '__all__'