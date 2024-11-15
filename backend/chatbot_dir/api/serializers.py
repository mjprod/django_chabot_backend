from rest_framework import serializers


class UserInputSerializer(serializers.Serializer):
    prompt = serializers.CharField()
    # added user_id field for when users are added
    user_id = serializers.IntegerField(default=0)


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
    ai_response = serializers.DictField()
    correct_bool = serializers.BooleanField()
    chat_rating = serializers.IntegerField(min_value=0, max_value=6)
    incorrect_answer_response = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.DictField(required=False)


# added the english and malay fields to the view summary call
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
