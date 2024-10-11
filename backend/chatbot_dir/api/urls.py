# chatbot_project/api/urls.py

from django.urls import path

from .views import (
    CaptureInteractionView,
    ChatbotView,
    ChatRatingView,
    CorrectAnswerView,
    CorrectBoolView,
    SubmitFeedbackView,
)

urlpatterns = [
    path("chat/", ChatbotView.as_view(), name="chatbot"),
    path("correct-answer/", CorrectAnswerView.as_view(), name="correct_answer"),
    path("correct-bool/", CorrectBoolView.as_view(), name="correct_bool"),
    path("chat-rating/", ChatRatingView.as_view(), name="chat_rating"),
    path("submit-feedback/", SubmitFeedbackView.as_view(), name="submit_feedback"),
    path(
        "capture_interaction/",
        CaptureInteractionView.as_view(),
        name="capture_interaction",
    ),
]

