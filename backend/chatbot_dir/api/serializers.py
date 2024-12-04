from datetime import datetime

from rest_framework import serializers


class NewUserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    user_id = serializers.CharField()
    session_id = serializers.CharField()
    agent_id = serializers.CharField()
    admin_id = serializers.CharField()


class TranslationSerializer(serializers.Serializer):
    language = serializers.CharField()
    text = serializers.CharField()


# added new serializers for the chat conversation and history
class MessageSerializer(serializers.Serializer):
    role = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.DateTimeField(default=datetime.now)


class NewCaptureSummarySerializer(serializers.Serializer):
    user_input = serializers.CharField()
    ai_response = serializers.CharField()
    correct_bool = serializers.BooleanField()
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    correct_answer = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)


class NewCaptureSummaryMultilangSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=True)
    user_id = serializers.CharField(required=True)
    agent_id = serializers.CharField(required=True)
    admin_id = serializers.CharField(required=True)
    prompt = serializers.CharField(required=True)
    cleaned_prompt = serializers.CharField(required=True)
    generation = serializers.CharField(required=True)
    translations = TranslationSerializer(many=True, required=False, default=[])
    correct_bool = serializers.BooleanField(required=False)
    correct_answer = serializers.CharField(required=False, allow_blank=True)
    chat_rating = serializers.IntegerField(min_value=0, max_value=6, required=False)
    timestamp = serializers.DateTimeField(default=datetime.now)


class NewViewSummarySerializer(serializers.Serializer):
    session_id = serializers.CharField()
    user_id = serializers.CharField()
    agent_id = serializers.CharField()
    admin_id = serializers.CharField()
    timestamp = serializers.DateTimeField()
    Question = serializers.CharField()
    Answer_English = serializers.CharField()
    Answer_Malay = serializers.CharField()
    Answer_Chinese = serializers.CharField()
    Question_correct = serializers.BooleanField()
    Correct_rating = serializers.IntegerField(min_value=1, max_value=5)
    Correct_Answer = serializers.CharField()


class ConversationMetadataSerializer(serializers.Serializer):
    session_id = serializers.CharField()
    user_id = serializers.CharField()
    agent_id = serializers.CharField()
    admin_id = serializers.CharField()
    timestamp = serializers.DateTimeField(default=datetime.now)
    messages = MessageSerializer(many=True)
    translations = TranslationSerializer(many=True)


# Currently used serializers are below: to be removed once history is working on server
class UserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    user_id = serializers.IntegerField(default=0)


class CaptureSummarySerializer(serializers.Serializer):
    user_input = serializers.CharField()
    ai_response = serializers.CharField()
    correct_bool = serializers.BooleanField()
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    correct_answer = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)


class CaptureSummaryMultilangSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=False)
    prompt = serializers.CharField(required=True)
    cleaned_prompt = serializers.CharField(required=True)
    generation = serializers.CharField(required=True)
    translations = serializers.ListField(
        child=serializers.DictField(), required=False, default=[]
    )
    correct_bool = serializers.BooleanField()
    correct_answer = serializers.CharField(required=False, allow_blank=True)
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    metadata = serializers.DictField(required=False, default=dict)


class ViewSummarySerializer(serializers.Serializer):
    Date_time = serializers.DateTimeField()
    User_id = serializers.IntegerField(default=0)
    Question = serializers.CharField()
    Answer_English = serializers.CharField()
    Answer_Malay = serializers.CharField()
    Question_correct = serializers.BooleanField()
    Correct_rating = serializers.IntegerField(min_value=1, max_value=5)
    Correct_Answer = serializers.CharField()
    Metadata = serializers.DictField(required=False)


class AIResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()


class NewAIResponseSerializer(serializers.Serializer):
    answer = serializers.CharField()


class CorrectBoolSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField()


class ChatRatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=6)


class IncorrectAnswerResponseSerializer(serializers.Serializer):
    incorrect_answer = serializers.CharField()


# new AI for admin panels:
class PromptConversationSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True)
    conversation_id = serializers.CharField(required=True)
    user_id = serializers.CharField(required=True)


class MessageDataSerializer(serializers.Serializer):
    role = serializers.CharField()
    content = serializers.CharField()
    timestamp = serializers.DateTimeField()


class CompleteConversationsSerializer(serializers.Serializer):
    conversation_id = serializers.CharField(required=True)
    user_id = serializers.CharField(required=True)
    messages = MessageDataSerializer(many=True, required=True)
    translations = TranslationSerializer(many=True, required=False)
