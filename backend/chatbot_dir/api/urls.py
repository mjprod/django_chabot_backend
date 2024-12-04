# chatbot_project/api/urls.py

from django.urls import path

from .views import (
    AgentConversationsView,
    AIResponseView,
    CaptureSummaryMultilangView,
    CaptureSummaryView,
    ChatRatingView,
    CompleteConversationsView,
    ConversationHistoryView,
    ConversationMessagesView,
    CorrectBoolView,
    IncorrectAnswerResponseView,
    NewAIResponseView,
    NewUserInputView,
    PromptConversationView,
    UserConversationsView,
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
    # New conversation history endpoints
    path("new_ai_response/", NewAIResponseView.as_view(), name="new_ai_response"),
    path("conversations/", NewUserInputView.as_view(), name="new-conversation"),
    path(
        "conversations/<str:session_id>/",
        ConversationHistoryView.as_view(),
        name="conversation-history",
    ),
    path(
        "conversations/<str:session_id>/messages/",
        ConversationMessagesView.as_view(),
        name="conversation-messages",
    ),
    path(
        "conversations/user/<int:user_id>/",
        UserConversationsView.as_view(),
        name="user-conversations",
    ),
    path(
        "conversations/agent/<str:agent_id>/",
        AgentConversationsView.as_view(),
        name="agent-conversations",
    ),
    # new API for conversation
    path(
        "prompt_conversation",
        PromptConversationView.as_view(),
        name="prompt_conversation",
    ),
    path(
        "complete_conversations",
        CompleteConversationsView.as_view(),
        name="complete_conversations",
    ),
]
