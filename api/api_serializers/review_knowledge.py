# For MONGODB, no need

from rest_framework import serializers
from bson import ObjectId


class ReviewKnowledgeSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        (0, "needs_approve"),
        (1, "pre_approved"),
        (2, "approved"),
        (3, "reject")
    ]

    LANGUAGE_CHOICES = [
        ("en", "English"),
        ("my", "Malay"),
        ("cn", "Chinese")
    ]

    id = serializers.CharField(required=True)
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, required=True)
    question = serializers.CharField(required=False)
    answer = serializers.CharField(required=False)
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)


class BulkDeleteSerializer(serializers.Serializer):
    ids = serializers.ListField(
        child=serializers.CharField(),
        required=True
    )

    def validate_ids(self, value):
        """
        Validate that all provided IDs in the list are valid MongoDB ObjectId strings.
        """
        if not value:
            raise serializers.ValidationError("The list of IDs cannot be empty.")
        
        for _id in value:
            if not self.is_valid_object_id(_id):
                raise serializers.ValidationError(f"Invalid ObjectId format: {_id}")
        
        return value

    def is_valid_object_id(self, _id):
        """
        Helper method to check if a string is a valid MongoDB ObjectId.
        """
        try:
            ObjectId(_id)
            return True
        except Exception:
            return False
