from django.views.decorators.cache import cache_page


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
    # PromptConversationDeepSeekView,
    PromptConversationAdminView,
)
from .views.feedback_view import (
    CaptureFeedbackView,
    CaptureFeedbackCompareView,
    CaptureFeedbackMultiView,
)
from .views.brain_view import (
    UpdateReviewStatusView,
    UpdateBrainView,
)



from django.urls import path, include

from rest_framework.routers import DefaultRouter
from .views.knowledge import (
    KnowledgeViewSet,
    KnowledgeContentViewSet, 
    KnowledgeSummaryAPIView,
    KnowledgeContentSummaryAPIView
)

from .views.category import (
    CategoryViewSet, 
    SubCategoryViewSet, 
)

from .views.brain import BrainViewSet


router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'subcategories', SubCategoryViewSet)
router.register(r'knowledge', KnowledgeViewSet)
router.register(r'knowledge-content', KnowledgeContentViewSet)
router.register(r'brain', BrainViewSet)



# Define URL patterns
urlpatterns = [
    path('', include(router.urls)),
    path('knowledge-summary/', KnowledgeSummaryAPIView.as_view(), name='knowledge-summary'),
    path('knowledge-content-summary/', KnowledgeContentSummaryAPIView.as_view(), name='knowledge-content-summary'),







    # Prompt Conversation
    path("prompt_conversation/",PromptConversationView.as_view(),name="prompt_conversation"),
    path("prompt_conversation_admin/",PromptConversationAdminView.as_view(),name="prompt_conversation_admin",),
    path("conversation/<conversation_id>/",ConversationDetailView.as_view(), name="conversation"),
    path("all_conversations_ids/",AllConversationsIdsView.as_view(), name="all_conversations_ids",),
    # Capture Feedback
    path("capture_feedback/", CaptureFeedbackView.as_view(), name="capture_feedback"),
    path("capture_feedback_compare/", CaptureFeedbackCompareView.as_view(), name="capture_feedback_compare"),
    path("capture_feedback_multi/",CaptureFeedbackMultiView.as_view(),name="capture_feedback_multi",),

    path("update_review_status/", UpdateReviewStatusView.as_view(), name="update_review_status"),
    path("update_brain/", UpdateBrainView.as_view(), name="update_brain"),

    # TODO: Wrong place -> move to brain_view
    path('update_knowledge/', UpdateKnowledgeView.as_view(), name='update_knowledge'),
    path('categorize_conversation/', SeparateConversationsView.as_view(), name='categorize_conversation'),
    path("delete_conversation/<conversation_id>/", DeleteConversationView.as_view(), name="delete_conversation"),
    path("finalise_conversation/<conversation_id>/", FinaliseConversationView.as_view(), name="finalise_conversation"),
    path("finalise_all_conversation/", FinaliseAllConversationsView.as_view(), name="finalise_all_conversation"),
    # Dashboard
    path("dashboard_counts/", DashboardCountsView.as_view(), name="dashboard_counts"),
]