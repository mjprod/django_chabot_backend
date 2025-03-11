from enum import Enum

class CategoryColorEnum(Enum):
    FINANCE = "#F0F9F0"
    TECHNOLOGY = "#E6F7FA"
    ACCOUNT = "#F0E8F9"
    FOURDLOTTO = "#FAF7E3"
    SECURITY = "#FAE6E6"
    FEEDBACK = "#F7F1E3"
    POINTSSHOP = "#F0F5FA"
    OTHER = "#F0FAF7"

class KnowledgeStatus(Enum):
    NEEDS_REVIEW = 'needs_review'
    PRE_APPROVED = 'pre_approved'
    APPROVED = 'approved'
    REJECT = 'reject'

    @classmethod
    def choices(cls):
        return [(item.value, item.name.replace('_', ' ').title()) for item in cls]

class Language(Enum):
    ENGLISH = 'en'
    MALAYSIAN = 'ms'
    CHINESE = 'cn'

    @classmethod
    def choices(cls):
        return [(item.value, item.name.title()) for item in cls]

class Type(Enum):
    FAQ = 'FAQ'
    CONVERSATION = 'Conversation'
    DOCUMENT = 'Document'

    @classmethod
    def choices(cls):
        return [(item.value, item.name.title()) for item in cls]
