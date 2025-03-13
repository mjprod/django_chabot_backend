from django.urls import path, include

from .views.conversation_view import (
    PromptConversationView,
    PromptConversationAdminView,
)

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
    path("prompt_conversation/", PromptConversationView.as_view(), name="prompt_conversation"),
    path("prompt_conversation_admin/", PromptConversationAdminView.as_view(), name="prompt_conversation_admin"),
]