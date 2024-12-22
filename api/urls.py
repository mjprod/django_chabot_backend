# chatbot_project/api/urls.py

from django.urls import path
from django.views.decorators.cache import cache_page

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
        cache_page(60 * 5)(CompleteConversationsView.as_view()),  # Cache for 5 minutes
        name="complete_conversations",
    ),
    path("capture_feedback/", CaptureFeedbackView.as_view(), name="capture_feedback"),
]
