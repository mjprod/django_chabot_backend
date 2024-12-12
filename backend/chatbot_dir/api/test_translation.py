import os
import sys

from dotenv import load_dotenv

from api.chatbot import translate_en_to_ms

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Load environment variables
load_dotenv()


def test_translation():
    # Test text
    test_text = "Hello, how are you?"
    print(f"\nTesting translation for: {test_text}")

    # Test the translation function
    try:
        result = translate_en_to_ms(test_text)
        print("\nTranslation Result:")
        print(f"Original text: {test_text}")
        print(f"Translation response: {result}")
    except Exception as e:
        print(f"Error during translation: {str(e)}")


if __name__ == "__main__":
    test_translation()
