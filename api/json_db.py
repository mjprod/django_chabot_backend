import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class JsonDB:
    def __init__(self, file_path: str = "temp_database.json"):
        self.file_path = file_path
        self.ensure_database_exists()

    def ensure_database_exists(self):
        try:
            if not os.path.exists(self.file_path):
                initial_data = {
                    "conversations": [],
                    "user_inputs": [],
                    "feedback_data": [],
                    "interactions": [],
                    "complete_conversations": [],  # Add this collection
                }
                self.write_data(initial_data)
            else:
                # Validate existing file
                try:
                    with open(self.file_path, "r") as f:
                        json.load(f)
                except json.JSONDecodeError:
                    # If file is corrupted, recreate it
                    initial_data = {
                        "conversations": [],
                        "user_inputs": [],
                        "feedback_data": [],
                        "interactions": [],
                        "complete_conversations": [],
                    }
                    self.write_data(initial_data)
        except Exception as e:
            print(f"Error initializing database: {str(e)}")

    def read_data(self) -> Dict:
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            # Reset file to initial state if corrupted
            initial_data = {
                "conversations": [],
                "user_inputs": [],
                "feedback_data": [],
                "interactions": [],
                "complete_conversations": [],
            }
            self.write_data(initial_data)
        return initial_data

    def write_data(self, data: Dict):
        with open(self.file_path, "w") as f:
            json.dump(data, f, indent=2)

    def insert_one(self, collection: str, document: Dict) -> str:
        data = self.read_data()
        if collection not in data:
            data[collection] = []
        document["_id"] = str(len(data[collection]))
        document["timestamp"] = datetime.now().isoformat()
        data[collection].append(document)
        self.write_data(data)
        return document["_id"]

    def find_one(self, collection: str, query: Dict) -> Optional[Dict]:
        data = self.read_data()
        if collection not in data:
            return None
        for doc in data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                return doc
        return None

    def find(self, collection: str, query: Dict = None) -> List[Dict]:
        data = self.read_data()
        if collection not in data:
            return []
        if query is None:
            return data[collection]
        return [
            doc
            for doc in data[collection]
            if all(doc.get(k) == v for k, v in query.items())
        ]

    def update_one(
        self, collection: str, query: Dict, update: Dict, upsert: bool = False
    ) -> bool:
        data = self.read_data()
        if collection not in data:
            if not upsert:
                return False
            data[collection] = []

        for doc in data[collection]:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update.get("$set", {}))
                self.write_data(data)
                return True

        if upsert:
            new_doc = {**query, **update.get("$set", {})}
            data[collection].append(new_doc)
            self.write_data(data)
            return True
        return False
