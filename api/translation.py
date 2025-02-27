import logging
import asyncio
import os
import gc
import requests
from openai import OpenAI

from concurrent.futures import ThreadPoolExecutor

from ai_config.ai_constants import (
    OPENAI_MODEL,
    OPENAI_MODEL_EN_TO_CN,
    OPENAI_TIMEOUT,
    MAX_TOKENS,
    URL_TRANSLATE_EN_TO_MS,
)

from ai_config.ai_prompts import (
    TRANSLATION_AND_CLEAN_PROMPT,
    TRANSLATION_EN_TO_CN_PROMPT,
)

logger = logging.getLogger(__name__)


async def generate_translations(generation):
    try:
        logger.info(f"Starting translations for: {generation}")

        with ThreadPoolExecutor() as executor:
            # Run translations
            malay_future = executor.submit(translate_en_to_ms, generation)
            chinese_future = executor.submit(translate_en_to_cn, generation)

            logger.info("Submitted translation tasks...")

            # Gather results
            translations = await asyncio.gather(
                asyncio.wrap_future(malay_future), asyncio.wrap_future(chinese_future)
            )

            logger.info(f"Translation results: {translations}")

            # Return structured translations
            output = [
                {"language": "en", "text": generation},
                {"language": "ms-MY", "text": translations[0].get("text", "")},
                {"language": "zh_CN", "text": translations[1].get("text", "")},
                {"language": "zh_TW", "text": translations[1].get("text", "")},
            ]

            logger.info(f"Final output: {output}")
            return output
    except Exception as e:
        logger.error(f"Error in generate_translations: {str(e)}", exc_info=True)
        raise

def translate_en_to_cn(input_text):
    logger.info("Translating text to Chinese...")

    try:
        api_key = os.getenv("OPENAI_API_KEY")
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model=OPENAI_MODEL_EN_TO_CN,
            messages=[
                {
                    "role": "system",
                    "content": TRANSLATION_EN_TO_CN_PROMPT,
                },
                {
                    "role": "user",
                    "content": f"Translate this text to Chinese: {input_text}",
                },
            ],
            temperature=0,
            timeout=OPENAI_TIMEOUT,
        )

        translation = response.choices[0].message.content.strip()

        return {
            "text": translation,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        }
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return {"text": "", "prompt_tokens": 0, "total_tokens": 0}

def translate_en_to_ms(input_text, to_lang="ms", model="base"):
    # this is the url we send the payload to for translation
    url = URL_TRANSLATE_EN_TO_MS

    # the payload struct
    payload = {
        "input": input_text,
        "to_lang": to_lang,
        "model": model,
        "top_k": 1,
        "top_p": 1,
        "repetition_penalty": 1.1,
        "temperature": 0,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('MESOLITICA_API_KEY')}",
    }

    try:
        print(f"Sending translation request for: {input_text}")  # Debug print
        response = requests.post(url, json=payload, headers=headers)

        if response.status_code == 200:
            translation_data = response.json()
            return {
                "text": translation_data.get("result", ""),
                "usage": translation_data.get("usage", {}),
            }
    except Exception as e:
        print(f"Translation error: {str(e)}")

    return {"text": "", "prompt_tokens": 0, "total_tokens": 0}


# this is the OPENAI translate function
def translate_and_clean(text):
    logger.error("translate_and_clean")
    # memory_snapshot = monitor_memory()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY environment variable.")
        return text

    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": TRANSLATION_AND_CLEAN_PROMPT,
                },
                {"role": "user", "content": f"Process this text: {text}"},
            ],
            max_tokens=MAX_TOKENS,
            timeout=OPENAI_TIMEOUT,
        )

        translated_text = response.choices[0].message.content.strip()
        translated_text = re.sub(r"^(Translated.*?:)", "", translated_text).strip()
        return translated_text

    except Exception as e:
        logger.error(f"Translation error: {str(e)}", exc_info=True)
        return text
    finally:
        # compare_memory(memory_snapshot)
        gc.collect()
