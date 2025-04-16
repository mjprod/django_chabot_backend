import gc
from datetime import datetime

from rest_framework import serializers


class BaseSerializer(serializers.Serializer):
    def to_representation(self, instance):
        try:
            return super().to_representation(instance)
        finally:
            gc.collect()


class TranslationSerializer(serializers.Serializer):
    language = serializers.CharField(max_length=10)
    text = serializers.CharField(max_length=550)

    def validate_text(self, value):
        if len(value.encode("utf-8")) > 500:
            raise serializers.ValidationError("Text too large")
        return value


# added new serializers for the chat conversation and history
class MessageSerializer(serializers.Serializer):
    role = serializers.CharField(max_length=50)
    content = serializers.CharField(max_length=2000)
    timestamp = serializers.DateTimeField(default=datetime.now)

    def validate_content(self, value):
        if len(value.encode("utf-8")) > 2000:
            raise serializers.ValidationError("Content too large")
        return value




class UserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000)
    user_id = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True
    )


class PromptConversationSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000, required=True)
    conversation_id = serializers.CharField(max_length=100, required=False)
    user_id = serializers.CharField(max_length=100, required=False)


class PromptConversationHistorySerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000, required=True)
    conversation_id = serializers.CharField(max_length=100, required=True)
    user_id = serializers.CharField(max_length=100, required=True)
    use_mongo = serializers.BooleanField(default=True, required=False)


class MessageDataSerializer(serializers.Serializer):
    text = serializers.JSONField(allow_null=True)  # For array or string
    sender = serializers.CharField(max_length=100)
    user = serializers.CharField(max_length=100)
    timestamp = serializers.DateTimeField()
    bot_id = serializers.CharField(max_length=100, required=False)

    def to_representation(self, instance):
        try:
            data = super().to_representation(instance)
            # Map sender to role for test compatibility
            data["role"] = data.pop("sender")
            # Map text to content for test compatibility
            data["content"] = data.pop("text")
            return data
        finally:
            gc.collect()

    def to_internal_value(self, data):
        # Handle incoming data in either format
        if "role" in data and "content" in data:
            # Convert from test format to storage format
            return {
                "text": data["content"],
                "sender": data["role"],
                "user": data.get("user", ""),
                "timestamp": data["timestamp"],
                "bot_id": data.get("bot_id", ""),
            }
        return super().to_internal_value(data)


class CompleteConversationsSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(max_length=100, required=True)
    messages = MessageDataSerializer(many=True, required=True)

    def validate_messages(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Too many messages in this conversation")
        return value


class PromptConversationAdminSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    conversation_id = serializers.CharField(required=True)
    user_id = serializers.CharField(required=True)
    admin_id = serializers.CharField(required=False, default="")
    bot_id = serializers.CharField(required=False, default="")
    language = serializers.CharField(
        max_length=10,
        required=False,
        default="en",
    )
class PromptConversationAgentAiSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    

    def validate_language(self, value):
        """Validate the language code is supported"""
        supported_languages = ["en", "ms_MY", "zh_CN", "zh_TW"]
        if value not in supported_languages:
            raise serializers.ValidationError(
                f"Unsupported language code. Must be one of: {supported_languages}"
            )
        return value


class UpdateAnswerBrain(serializers.Serializer):
    doc_id = serializers.CharField(required=True)
    answer_en = serializers.CharField(required=True)
    answer_ms = serializers.CharField(required=True)
    answer_cn = serializers.CharField(required=True)

class InsertAnswerBrain(serializers.Serializer):
    question = serializers.CharField(required=True)
    answer_en = serializers.CharField(required=True)
    answer_ms = serializers.CharField(required=True)
    answer_cn = serializers.CharField(required=True)