import json

# Carrega os dados transformados
with open('ALL_DATA_transformed.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

chunk_size = 100
total_records = len(data)
num_parts = (total_records + chunk_size - 1) // chunk_size  # número total de arquivos

for i in range(num_parts):
    chunk = data[i * chunk_size : (i + 1) * chunk_size]
    filename = f"database_part_{i+1}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(chunk, f, ensure_ascii=False, indent=2)
    print(f"Arquivo {filename} criado com {len(chunk)} registros.")