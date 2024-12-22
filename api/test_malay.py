import os

import requests
from dotenv import load_dotenv


def test_translate_en_to_ms():
    # Load environment variables
    load_dotenv()

    # Test input
    test_text = "Hello, how are you today?"

    # Translation endpoint
    url = "https://api.mesolitica.com/translation"

    # Request payload
    payload = {
        "input": test_text,
        "to_lang": "ms",
        "model": "base",
        "top_k": 1,
        "top_p": 1,
        "repetition_penalty": 1.1,
        "temperature": 0,
    }

    # Headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('MESOLITICA_API_KEY')}",
    }

    try:
        print(f"Testing translation for: {test_text}")
        response = requests.post(url, json=payload, headers=headers)

        print(f"Response status code: {response.status_code}")
        print(f"Response content: {response.text}")

        if response.status_code == 200:
            translation_data = response.json()
            print(f"Translated text: {translation_data.get('result', '')}")
            print(f"Usage stats: {translation_data.get('usage', {})}")
            return True
        else:
            print("Translation failed")
            return False

    except Exception as e:
        print(f"Error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    test_translate_en_to_ms()
