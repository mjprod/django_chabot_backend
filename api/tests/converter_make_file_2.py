import json
from datetime import datetime, timezone

# Caso você não tenha criado o ALL_DATA_fixed.json com os campos de context,
# pode modificar o script para extrair os valores do campo original.
with open('ALL_DATA_fixed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

new_data = []
for i, record in enumerate(data, start=357):
    new_record = {}
    new_record["id"] = f"{i:04d}" 

    text = record.get("user_input_en", "")
    variations = [
        record.get("user_input_en", ""),
        record.get("user_input_ms", ""),
        record.get("user_input_cn", "")
    ]

    
    languages = {
        "en": record.get("user_input_en", ""),
        "ms": record.get("user_input_ms", ""),
        "cn": record.get("user_input_cn", "")
    }
    
    subcategory = record.get("subcategory", "")

    new_record["question"] = {
        "text": text,
        "variations": variations,
        "intent": subcategory,
        "languages": languages
    }

    detailed = {
        "en": record.get("context_en", ""),
        "ms": record.get("context_ms", ""),
        "cn": record.get("context_cn", "")
    }
    new_record["answer"] = {
        "detailed": detailed,
        "conditions": []
    }

    # Metadata
    category = record.get("category", "")
    
    now = datetime.now(timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')
    new_record["metadata"] = {
        "category": [category] if category else [],
        "subCategory": subcategory,
        "difficulty": 2,
        "confidence": 0.5,
        "dateCreated": now,
        "lastUpdated": now,
        "version": "1.0",
        "source": "",
        "status": "active"
    }

    new_record["context"] = {
        "relatedTopics": [],
        "prerequisites": [],
        "followUpQuestions": {
            "en": [],
            "ms": [],
            "cn": []
        }
    }

    # Usage
    new_record["usage"] = {
        "searchFrequency": 0,
        "successRate": 0,
        "lastQueried": None
    }
    new_record["review_status"] = []
    new_data.append(new_record)

with open('ALL_DATA_transformed.json', 'w', encoding='utf-8') as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print("file done - ALL_DATA_transformed.json")