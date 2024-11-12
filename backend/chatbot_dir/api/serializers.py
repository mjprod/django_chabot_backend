from rest_framework import serializers

from .models import AIAgent


class UserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField()


class AIResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()


class CorrectBoolSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField()


class ChatRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=6)


class IncorrectAnswerResponseSerializer(serializers.Serializer):
    incorrect_answer = serializers.CharField()


class CaptureSummarySerializer(serializers.Serializer):
    user_input = serializers.CharField()
    ai_response = serializers.CharField()
    correct_bool = serializers.BooleanField()
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    incorrect_answer_response = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)


class ViewSummarySerializer(serializers.Serializer):
    Date_time = serializers.DateTimeField()
    Question = serializers.CharField()
    Answer = serializers.CharField()
    Question_correct = serializers.BooleanField()
    Correct_rating = serializers.IntegerField(min_value=1, max_value=5)
    Correct_Answer = serializers.CharField()
    Metadata = serializers.DictField(required=False)


# this is the create agent serializer, it dictates what formatting the request needs to be


class AIAgentSerializer(serializers.Serializer):
    class Meta:
        model = AIAgent
        fields = ["agent_id", "name", "temperature", "system_prompt", "image"]
