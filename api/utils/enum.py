from enum import Enum

class CategoryColor(Enum):
    THIRD_PARTY = (1, "#FAF0F5")
    LOTTO_4D = (2, "#FAF7E3")
    ACCOUNT = (3, "#F0E8F9")
    FEEDBACK = (4, "#F7F1E3")
    FINANCE = (5, "#F0F9F0")
    POINTS_SHOP = (6, "#F0F5FA")
    REFERRAL = (7, "#F0FAF7")
    SECURITY = (8, "#FAE6E6")
    TECHNICAL = (9, "#E6F7FA")
    CUSTOMER_SUPPORT = (10, "#F0D0C0")
    GAME_INQUIRY = (11, "#F0DFC2")
    POLICY_EXPLANATION = (12, "#F0F0C2")
    ENCOURAGEMENT = (13, "#DFF0C2")
    SPORTS_BETTING = (14, "#C2E5D0")

    @property
    def id(self):
        return self.value[0]

    @property
    def color(self):
        return self.value[1]

    @classmethod
    def get_color_by_id(cls, category_id: int) -> str:
        """Returns the hex color for a given category ID."""
        for item in cls:
            if item.id == category_id:
                return item.color
        return "#FFFFFF"  # Default to white if not found


class KnowledgeType(Enum):
    FAQ = 1
    CONVERSATION = 2
    DOCUMENT = 3

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

class KnowledgeContentStatus(Enum):
    NEEDS_REVIEW = 1
    PRE_APPROVED = 2
    APPROVED = 3
    REJECT = 4

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

class KnowledgeContentLanguage(Enum):
    ENGLISH = 1
    MALAYSIAN = 2
    CHINESE = 3

    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]