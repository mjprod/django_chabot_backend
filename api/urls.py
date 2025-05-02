from django.urls import path
from django.views.decorators.cache import cache_page

from .views.conversation_view import (
    PromptConversationView,
    ConversationDetailView,
    AllConversationsIdsView,
    PromptConversationAdminView,
    PromptConversationAgentAIView,
    PromptImageView,
)

from .views.brain_view import (
    UpdateBrainView,
    InsertBrainView,
)

# Define URL patterns
urlpatterns = [
    # Prompt Conversation
    path("prompt_conversation/",PromptConversationView.as_view(),name="prompt_conversation"),
    path("prompt_conversation_admin/",PromptConversationAdminView.as_view(),name="prompt_conversation_admin",),
    path("prompt_conversation_image/",PromptImageView.as_view(),name="prompt_conversation_image",),
    path("prompt_conversation_agent_ai/",PromptConversationAgentAIView.as_view(),name="prompt_conversation_agent_ai",),
    path("conversation/<conversation_id>/",ConversationDetailView.as_view(), name="conversation"),
    path("all_conversations_ids/",AllConversationsIdsView.as_view(), name="all_conversations_ids",),

    # Brain
    path("update_brain/", UpdateBrainView.as_view(), name="update_brain"),
    path("insert_brain/", InsertBrainView.as_view(), name="insert_brain"),
]
