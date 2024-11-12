from django.db import models


# the AI Agent class for model
class AIAgent(models.model):
    agent_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    temperature = models.FloatField()
    system_prompt = models.TextField()
    image = models.CharField(
        max_length=255
    )  # this is where we store the image filename
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
