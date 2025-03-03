import json
import re

import json

with open('ALL_DATA.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for record in data:
    key = "推測上文 (Assumed Context) (原語 --- English --- 中文)"
    if key in record:
        # Remove e obtém o valor do campo
        value = record.pop(key).strip()
        # Divide a string usando " --- " e remove aspas extras
        parts = [part.strip().strip('"') for part in value.split("---")]
        if len(parts) >= 3:
            record["context_ms"] = parts[0]
            record["context_en"] = parts[1]
            record["context_cn"] = parts[2]
        else:
            print("Formato inesperado no registro id:", record.get("id"), ":", value)

with open('ALL_DATA_fixed.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Arquivo transformado salvo como ALL_DATA_fixed.json")