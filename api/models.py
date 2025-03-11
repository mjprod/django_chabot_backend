from django.db import models
from django.core.exceptions import ValidationError

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
        ('FAQ', 'FAQ'),
        ('Conversation', 'Conversation'),
        ('Document', 'Document'),
    ]

    knowledge_uuid = models.UUIDField(editable=False, null=True, blank=True)
    category = models.ForeignKey(Category, related_name='knowledge_category', on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, related_name='knowledge_subcategory', on_delete=models.SET_NULL, null=True, blank=True)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='FAQ')

    def clean(self):
        if self.subcategory and self.category:
            if self.subcategory.category != self.category:
                raise ValidationError('Subcategory must belong to the specified category.')
        elif self.subcategory and not self.category:
            raise ValidationError('A category must be specified when a subcategory is provided.')
        
        super().clean()
        
    def save(self, *args, **kwargs):
        self.full_clean()  # Ensure the clean method is called
        super().save(*args, **kwargs)


class KnowledgeContent(models.Model):

    STATUS_CHOICES = [
        ('needs_review', 'Needs Review'),
        ('pre_approved', 'Pre-Approved'),
        ('approved', 'Approved'),
        ('reject', 'Reject')
    ]

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('ms', 'Malaysian'),
        ('cn', 'Chinese'),
    ]

    knowledge = models.ForeignKey(Knowledge, related_name='knowledge_content', on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='needs_review')
    is_edited = models.BooleanField(default=False)
    in_brain = models.BooleanField(default=False)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES)
    date_created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    question = models.TextField(blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    content = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['knowledge', 'language'], name='unique_knowledge_language')
        ]