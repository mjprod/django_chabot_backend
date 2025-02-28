from django.urls import path
from django.views.decorators.cache import cache_page

# Import views from conversation_view, feedback_view, and user_input_view
from .views.conversation_view import (
    PromptConversationView,
    ConversationDetailView,
    UpdateKnowledgeView,
    AllConversationsIdsView,
    DeleteConversationView,
    FinaliseConversationView,
    FinaliseAllConversationsView,
    SeparateConversationsView,
    DashboardCountsView,
    UpdateBrainView,
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

from .views.brain import BrainView

# Define URL patterns
urlpatterns = [
    # TODO: DEPRECATED
    path("user_input/", UserInputView.as_view(), name="user_input"),
    # Prompt Conversation
    path("prompt_conversation/",PromptConversationView.as_view(),name="prompt_conversation"),
    path("prompt_conversation_admin/",PromptConversationAdminView.as_view(),name="prompt_conversation_admin",),
    path("conversation/<conversation_id>/",ConversationDetailView.as_view(), name="conversation"),
    path("all_conversations_ids/",AllConversationsIdsView.as_view(), name="all_conversations_ids",),
    # Capture Feedback
    path("capture_feedback/", CaptureFeedbackView.as_view(), name="capture_feedback"),
    path("capture_feedback_compare/", CaptureFeedbackCompareView.as_view(), name="capture_feedback_compare"),
    path("capture_feedback_multi/",CaptureFeedbackMultiView.as_view(),name="capture_feedback_multi",),
    # Brain
    path('update_knowledge/', UpdateKnowledgeView.as_view(), name='update_knowledge'),
    path('categorize_conversation/', SeparateConversationsView.as_view(), name='categorize_conversation'),
    path("delete_conversation/<conversation_id>/", DeleteConversationView.as_view(), name="delete_conversation"),
    path("finalise_conversation/<conversation_id>/", FinaliseConversationView.as_view(), name="finalise_conversation"),
    path("finalise_all_conversation/", FinaliseAllConversationsView.as_view(), name="finalise_all_conversation"),
    path("update_brain/", UpdateBrainView.as_view(), name="update_brain"),
    path("brain/", BrainView.as_view(), name="brain"),

    # Dashboard
    path("dashboard_counts/", DashboardCountsView.as_view(), name="dashboard_counts"),
]
