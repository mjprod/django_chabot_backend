from django.core.management.base import BaseCommand
from pymongo import MongoClient
from django.conf import settings


class Command(BaseCommand):
    help = "Create MongoDB indexes for collections"

    def handle(self, *args, **kwargs):
        try:
            # Conectar ao MongoDB
            client = MongoClient(settings.MONGODB_URI)
            db = client[settings.MONGODB_DATABASE]

            # Criar índices
            db.user_inputs.create_index([("user_id", 1)])
            db.user_inputs.create_index([("timestamp", -1)])
            db.conversations.create_index([("session_id", 1)])
            db.conversations.create_index([("user_id", 1)])
            db.interactions.create_index([("timestamp", -1)])

            self.stdout.write(
                self.style.SUCCESS("MongoDB indexes created successfully!")
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error creating indexes: {str(e)}"))
