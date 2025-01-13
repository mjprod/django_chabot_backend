from django.urls import path
from django.views.decorators.cache import cache_page

# Import views from conversation_view, feedback_view, and user_input_view
from .views.conversation_view import (
    CompleteConversationsView,
    PromptConversationView,
    PromptConversationHistoryView,
)
from .views.feedback_view import (
    CaptureFeedbackView,
)
from .views.user_input_view import (
    UserInputView,
)

# Define URL patterns
urlpatterns = [
    # Route for user input
    path("user_input/", UserInputView.as_view(), name="user_input"),
    # Route to start a conversation
    path(
        "prompt_conversation/",
        PromptConversationView.as_view(),
        name="prompt_conversation",
    ),
    path(
        "prompt_conversation_history/",
        PromptConversationHistoryView.as_view(),
        name="prompt_conversation_history",
    ),
    # Route for complete conversations (cached for 5 minutes)
    path(
        "complete_conversations/",
        cache_page(60 * 5)(CompleteConversationsView.as_view()),
        name="complete_conversations",
    ),
    # Route for capturing feedback
    path("capture_feedback/", CaptureFeedbackView.as_view(), name="capture_feedback"),
]
