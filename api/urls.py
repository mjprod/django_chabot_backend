from django.urls import path
from django.views.decorators.cache import cache_page

# Import views from conversation_view, feedback_view, and user_input_view
from .views.conversation_view import (
    PromptConversationView,
    ConversationDetailView,
    UpdateKnowledgeView,
    AllConversationsIdsView,
    DeleteConversationView,
    # PromptConversationDeepSeekView,
    PromptConversationAdminView,
)
from .views.feedback_view import (
    CaptureFeedbackView,
    CaptureFeedbackCompareView,
    CaptureFeedbackMultiView,
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
      "conversation/<conversation_id>/",ConversationDetailView.as_view(), name="conversation",
    ),
    path(
       "all_conversations_ids/",AllConversationsIdsView.as_view(), name="all_conversations_ids",
    ),
    path('update_knowledge/', UpdateKnowledgeView.as_view(), name='update_knowledge'),
    path("delete_conversation/<conversation_id>/", DeleteConversationView.as_view(), name="delete_conversation"),
    # path(
    #    "prompt_conversation_deepseek/",
    #    PromptConversationDeepSeekView.as_view(),
    #    name="prompt_conversation_deepseek",
    # ),
    # Route for capturing feedback
    path("capture_feedback/", CaptureFeedbackView.as_view(), name="capture_feedback"),
    # Route for capturing feedback compare
    path("capture_feedback_compare/", CaptureFeedbackCompareView.as_view(), name="capture_feedback_compare"),
    # Route for capturing feedback
    path(
        "capture_feedback_multi/",
        CaptureFeedbackMultiView.as_view(),
        name="capture_feedback_multi",
    ),
    # Route for prompt_conversation_admin
    path(
        "prompt_conversation_admin/",
        PromptConversationAdminView.as_view(),
        name="prompt_conversation_admin",
    ),
]
