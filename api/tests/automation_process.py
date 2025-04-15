import json

input_file = "automation.json"
output_file = "automation_final.json"

print("📂 Step 1: Reading file...")

with open(input_file, 'r', encoding='utf-8') as f:
    raw = f.read()

print("🔧 Step 2: Fixing content structure (replacing '][' with ',')...")

# Corrige estrutura
content = "[" + raw.replace("][", ",") + "]"

print("📊 Step 3: Parsing JSON...")

try:
    data = json.loads(content)
except json.JSONDecodeError as e:
    print("❌ Failed to parse JSON:", e)
    exit()

# Flatten se estiver dentro de um array externo
if isinstance(data, list) and len(data) == 1 and isinstance(data[0], list):
    data = data[0]
    print(f"🔄 Flattened nested array. Total items: {len(data)}")
else:
    print(f"ℹ️ Data loaded. Total items: {len(data)}")

# Ver quantos têm question.text
com_texto = [d for d in data if "question" in d and "text" in d["question"]]
print(f"📝 Items with 'question.text': {len(com_texto)}")

# Filtro por tamanho do texto
filtered = [
    d for d in com_texto
    if len(d["question"]["text"]) >= 40
]

print(f"✅ Step 4: Filtered items (text ≥ 40 chars): {len(filtered)}")

if not filtered:
    print("⚠️ No items passed the filter. Check your data or threshold.")

print(f"💾 Step 5: Saving filtered data to '{output_file}'...")

with open(output_file, 'w', encoding='utf-8') as f_out:
    json.dump(filtered, f_out, ensure_ascii=False, indent=2)

print("🏁 Done!")