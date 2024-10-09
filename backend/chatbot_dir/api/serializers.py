# chatbot_project/api/serializers.py

from rest_framework import serializers

class CorrectAnswerSerializer(serializers.Serializer):
    prompt = serializers.CharField()

class CorrectBoolSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField()

class ChatRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=6)