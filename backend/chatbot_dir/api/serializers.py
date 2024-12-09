from datetime import datetime

from rest_framework import serializers


class TranslationSerializer(serializers.Serializer):
    language = serializers.CharField()
    text = serializers.CharField()


# added new serializers for the chat conversation and history
class MessageSerializer(serializers.Serializer):
    role = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.DateTimeField(default=datetime.now)


class ConversationMetadataSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    user_id = serializers.CharField()
    agent_id = serializers.CharField()
    admin_id = serializers.CharField()
    timestamp = serializers.DateTimeField(default=datetime.now)
    messages = MessageSerializer(many=True)
    translations = TranslationSerializer(many=True)


class UserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    user_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)


class PromptConversationSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    conversation_id = serializers.CharField(required=True)
    user_id = serializers.CharField(required=True)


class MessageDataSerializer(serializers.Serializer):
    text = serializers.JSONField(allow_null=True)  # For array or string
    sender = serializers.CharField()
    user = serializers.CharField()
    timestamp = serializers.DateTimeField()
    agent_id = serializers.CharField(required=False)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Map sender to role for test compatibility
        data["role"] = data.pop("sender")
        # Map text to content for test compatibility
        data["content"] = data.pop("text")
        return data

    def to_internal_value(self, data):
        # Handle incoming data in either format
        if "role" in data and "content" in data:
            # Convert from test format to storage format
            return {
                "text": data["content"],
                "sender": data["role"],
                "user": data.get("user", ""),
                "timestamp": data["timestamp"],
                "agent_id": data.get("agent_id", ""),
            }
        return super().to_internal_value(data)


class CompleteConversationsSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(required=True)
    messages = MessageDataSerializer(many=True, required=True)


class CaptureFeedbackSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(required=True)
    user_input = serializers.CharField(required=True)
    ai_response = serializers.CharField(required=True)
    correct_bool = serializers.BooleanField(required=True)
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    correct_answer = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False, default=dict)
