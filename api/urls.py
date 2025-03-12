from django.urls import path

from .views.conversation_view import (
    PromptConversationView,
    PromptConversationAdminView,
)

# from .views.brain_view import (
    # ListReviewAndUpdateBrainView,
    # UpdateReviewStatusView,
    # UpdateBrainView,
# )

# Define URL patterns
urlpatterns = [
    # Prompt Conversation
    path("prompt_conversation/", PromptConversationView.as_view(), name="prompt_conversation"),
    path("prompt_conversation_admin/", PromptConversationAdminView.as_view(), name="prompt_conversation_admin",),
    # Brain
    # path("list_review_update_brain/", ListReviewAndUpdateBrainView.as_view(), name="review_update_brain"),
    # path("update_review_status/", UpdateReviewStatusView.as_view(), name="update_review_status"),
    # path("update_brain/", UpdateBrainView.as_view(), name="update_brain"),
]
