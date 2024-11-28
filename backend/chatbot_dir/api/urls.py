# chatbot_project/api/urls.py

from django.urls import path

from .views import (
    AIResponseView,
    CaptureSummaryMultilangView,
    CaptureSummaryView,
    ChatRatingView,
    CorrectBoolView,
    IncorrectAnswerResponseView,
    UserInputView,
    ViewSummaryView,
)

urlpatterns = [
    path("user_input/", UserInputView.as_view(), name="user_input"),
    path("ai_response/", AIResponseView.as_view(), name="ai_response"),
    path("correct_bool/", CorrectBoolView.as_view(), name="correct_bool"),
    path("chat_rating/", ChatRatingView.as_view(), name="chat_rating"),
    path(
        "incorrect_answer_response/",
        IncorrectAnswerResponseView.as_view(),
        name="incorrect_answer_response",
    ),
    path(
        "capture_summary/",
        CaptureSummaryView.as_view(),
        name="capture_summary",
    ),
    path(
        "capture_summary_multilang/",
        CaptureSummaryMultilangView.as_view(),
        name="capture_summary_multilang",
    ),
    path("view_summary/", ViewSummaryView.as_view(), name="view_summary"),
]
