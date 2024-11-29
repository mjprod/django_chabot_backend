import json

#import both of our json files for editing
with open("interaction_outcome.json", "r", encodings="utf-8") as f:
    interaction_data = json.load(f)

with open("database_part_1.json", "r", encodings="utf-8") as ff:
    database = json.load(ff)

#find and replace function that takes the correct_answer from interaction_outcome and replace the "detailed answer in chinese
correct_answers = [item["correct_answer"] for itme in interaction_data if not item["correct_bool"]] 

for i, entry in enumerate(database):
    if i < len(correct_answers):
        entry["answer"]["detailed"]["cn"] = correct_answers[i]

with open("database_part_1.json", "w", encoding="utf-8") ad f:
    json.dump(database, f, ensure_ascii=False, indent=4)

