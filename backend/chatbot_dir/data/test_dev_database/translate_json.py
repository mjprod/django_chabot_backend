import json
from googletrans import Translator


def translate_json(input_file, output_file, src_lang="zh-cn", dest_lang="en"):
    # Initialize the translator
    translator = Translator()

    # Load the JSON data from the input file
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Function to recursively translate strings in JSON
    def translate_string(data):
        if isinstance(data, dict):
            return {k: translate_string(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [translate_string(item) for item in data]
        elif isinstance(data, str):
            # Translate string
            return translator.translate(data, src=src_lang, dest=dest_lang).text
        else:
            return data

    # Translate the entire JSON structure
    translated_data = translate_string(data)

    # Write the translated data to the output file
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(translated_data, f, ensure_ascii=False, indent=4)


# Example usage
translate_json(
    "json_translate.json", "translated_json.json", src_lang="zh-cn", dest_lang="en"
)
