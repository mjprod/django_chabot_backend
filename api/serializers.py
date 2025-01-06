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


class ConversationMetadataSerializer(BaseSerializer):
    session_id = serializers.CharField(max_length=100)
    user_id = serializers.CharField(max_length=100)
    agent_id = serializers.CharField(max_length=100)
    admin_id = serializers.CharField(max_length=100)
    timestamp = serializers.DateTimeField(default=datetime.now)
    messages = MessageSerializer(many=True)
    translations = TranslationSerializer(many=True)

    def validate_conversation_data(self, data):
        if (
            len(data.get("messages", [])) > 100
        ):  # this will limit the message history to prevent leaks in memory
            raise serializers.ValidationError("Too many messages")
        if len(data.get("translations", [])) > 100:  # this is a limit for translations
            raise serializers.ValidationError("Too many translations")
        return data


class UserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000)
    user_id = serializers.CharField(
        max_length=100, required=False, allow_null=True, allow_blank=True
    )


class PromptConversationSerializer(serializers.Serializer):
    prompt = serializers.CharField(max_length=1000, required=True)
    conversation_id = serializers.CharField(max_length=100, required=True)
    user_id = serializers.CharField(max_length=100, required=True)


class MessageDataSerializer(serializers.Serializer):
    text = serializers.JSONField(allow_null=True)  # For array or string
    sender = serializers.CharField(max_length=100)
    user = serializers.CharField(max_length=100)
    timestamp = serializers.DateTimeField()
    agent_id = serializers.CharField(max_length=100, required=False)

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
        try:
            text_data = data.get("text")
            # Handle both string and array types
            if isinstance(text_data, list):
                # Clean up [object Object] artifacts from arrays
                cleaned_text = []
                for item in text_data:
                    if isinstance(item, str):
                        # Remove [object Object] artifacts
                        cleaned_item = item.replace("[object Object]", "").strip()
                        if cleaned_item:  # Only add non-empty strings
                            cleaned_text.append(cleaned_item)
            else:
                cleaned_text = text_data

            return {
                "text": cleaned_text,
                "sender": data["sender"],
                "user": data.get("user", ""),
                "timestamp": data["timestamp"],
                "agent_id": data.get("agent_id", ""),
            }
        except Exception as e:
            raise serializers.ValidationError(f"Data validation failed: {str(e)}")


class CompleteConversationsSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(max_length=100, required=True)
    messages = MessageDataSerializer(many=True, required=True)

    def validate_messages(self, value):
        if len(value) > 100:
            raise serializers.ValidationError("Too many messages in this conversation")
        return value


class CaptureFeedbackSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(max_length=100)
    user_input = serializers.CharField(max_length=1000)
    ai_response = serializers.CharField(max_length=2000)
    correct_bool = serializers.BooleanField()
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    correct_answer = serializers.CharField(
        max_length=2000, required=False, allow_blank=True
    )
    metadata = serializers.DictField(required=False)

    def validate_metadata(self, value):
        if len(str(value)) > 2000:
            raise serializers.ValidationError("Metadata field is too large")
        return value
