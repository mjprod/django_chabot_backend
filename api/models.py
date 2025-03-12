from django.db import models
from django.core.exceptions import ValidationError
from .utils.enum import KnowledgeType, KnowledgeContentStatus, KnowledgeContentLanguage

import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)


class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name='subcategory_category', on_delete=models.CASCADE)  # Linking to Category
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    

class Knowledge(models.Model):

    TYPE_CHOICES = [
        (KnowledgeType.FAQ.value, 'FAQ'),
        (KnowledgeType.CONVERSATION.value, 'Conversation'),
        (KnowledgeType.DOCUMENT.value, 'Document'),
    ]

    knowledge_uuid = models.UUIDField(editable=False, unique=True)
    category = models.ForeignKey(Category, related_name='knowledge_category', on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, related_name='knowledge_subcategory', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.IntegerField(choices=TYPE_CHOICES, default=KnowledgeType.FAQ.value)

    def clean(self):
        if self.subcategory and self.category:
            if self.subcategory.category != self.category:
                raise ValidationError('Subcategory must belong to the specified category.')
        elif self.subcategory and not self.category:
            raise ValidationError('A category must be specified when a subcategory is provided.')
        
        super().clean()
        
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class KnowledgeContent(models.Model):

    STATUS_CHOICES = [
        (KnowledgeContentStatus.NEEDS_REVIEW.value, 'Needs Review'),
        (KnowledgeContentStatus.PRE_APPROVED.value, 'Pre-Approved'),
        (KnowledgeContentStatus.APPROVED.value, 'Approved'),
        (KnowledgeContentStatus.REJECT.value, 'Reject')
    ]

    LANGUAGE_CHOICES = [
        (KnowledgeContentLanguage.ENGLISH.value, 'English'),
        (KnowledgeContentLanguage.MALAYSIAN.value, 'Malaysian'),
        (KnowledgeContentLanguage.CHINESE.value, 'Chinese'),
    ]


    knowledge = models.ForeignKey(Knowledge, related_name='knowledge_content', on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUS_CHOICES, default=KnowledgeContentStatus.NEEDS_REVIEW.value)
    is_edited = models.BooleanField(default=False)
    in_brain = models.BooleanField(default=False)
    language = models.IntegerField(choices=LANGUAGE_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    question = models.TextField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['knowledge', 'language'], name='unique_knowledge_language')
        ]
    
    def save(self, *args, **kwargs):
        # Check if there is a related Brain instance
        if Brain.objects.filter(knowledge_content=self).exists():
            self.in_brain = True
        else:
            self.in_brain = False
        super().save(*args, **kwargs)

class Brain(models.Model):
    knowledge_content = models.ForeignKey(KnowledgeContent, related_name='knowledge_content', on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)