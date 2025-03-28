from django.urls import path
from django.views.decorators.cache import cache_page

from .views.conversation_view import (
    PromptConversationView,
    ConversationDetailView,
    UpdateKnowledgeView,
    AllConversationsIdsView,
    DeleteConversationView,
    DeletePreBrainView,
    FinaliseConversationView,
    FinaliseAllConversationsView,
    SeparateConversationsView,
    DashboardCountsView,
    # PromptConversationDeepSeekView,
    PromptConversationAdminView,
)
from .views.feedback_view import (
    CaptureFeedbackView,
    CaptureFeedbackCompareView,
    CaptureFeedbackMultiView,
)
from .views.brain_view import (
    ListReviewAndUpdateBrainView,
    UpdateReviewStatusView,
    UpdateBrainView,
    InsertBrainView,
    PreBrainView
)

# Define URL patterns
urlpatterns = [
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
    path("list_review_update_brain/", ListReviewAndUpdateBrainView.as_view(), name="review_update_brain"),
    path("update_review_status/", UpdateReviewStatusView.as_view(), name="update_review_status"),
    path("update_brain/", UpdateBrainView.as_view(), name="update_brain"),
    path("insert_brain/", InsertBrainView.as_view(), name="insert_brain"),
    path("get_pre_brain/", PreBrainView.as_view(), name="get_pre_brain"),
    path("delete_pre_brain/<_id>/", DeletePreBrainView.as_view(), name="delete_pre_brain"),

    # TODO: Wrong place -> move to brain_view
    path('update_knowledge/', UpdateKnowledgeView.as_view(), name='update_knowledge'),
    path('categorize_conversation/', SeparateConversationsView.as_view(), name='categorize_conversation'),
    path("delete_conversation/<conversation_id>/", DeleteConversationView.as_view(), name="delete_conversation"),
    path("finalise_conversation/<conversation_id>/", FinaliseConversationView.as_view(), name="finalise_conversation"),
    path("finalise_all_conversation/", FinaliseAllConversationsView.as_view(), name="finalise_all_conversation"),
    # Dashboard
    path("dashboard_counts/", DashboardCountsView.as_view(), name="dashboard_counts"),
]
