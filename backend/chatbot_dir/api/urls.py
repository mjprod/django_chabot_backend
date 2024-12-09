# chatbot_project/api/urls.py

from django.urls import path

from .views import (
    CaptureFeedbackView,
    CompleteConversationsView,
    PromptConversationView,
    UserInputView,
)

urlpatterns = [
    path("user_input/", UserInputView.as_view(), name="user_input"),
    path(
        "prompt_conversation/",
        PromptConversationView.as_view(),
        name="prompt_conversation",
    ),
    path(
        "complete_conversations/",
        CompleteConversationsView.as_view(),
        name="complete_conversations",
    ),
    path("capture_feedback/", CaptureFeedbackView.as_view(), name="capture_feedback"),
]
