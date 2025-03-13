import os
import logging
import time

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from datetime import datetime

from api.constants.ai_constants import (
    OPENAI_MODEL,
    OPENAI_TIMEOUT,
    MAX_TOKENS,
    MAX_TEMPERATURE,
    LANGUAGE_DEFAULT,
)

from api.constants.ai_prompts import (
    FIRST_MESSAGE_PROMPT,
    CONFIDENCE_GRADER_PROMPT,
)

from api.chatbot import (
     chatbot,
)
# store = None
from .mongo import MongoDB

from api.ai_services import (
    GradeConfidenceLevel,
)

logger = logging.getLogger(__name__)


def is_finalizing_phrase(phrase):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("Missing OPENAI_API_KEY environment variable.")
        return "false"

    client = OpenAI(api_key=api_key)
    """
    Analyzes whether a given phrase is likely to be a conversation-ender.
    """
    messages = [
        {
            "role": "system",
            "content": "You are an assistant that determines if a phrase ends a conversation.",
        },
        {
            "role": "user",
            "content": f"Does the following phrase indicate the end of a conversation? \
                \n\nPhrase: \"{phrase}\"\n\n \
                Respond with 'Yes' or 'No'.",
        },
    ]

    try:
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            temperature=0,
            timeout=OPENAI_TIMEOUT,
        )

        result = response.choices[0].message.content.strip()
        if result.lower() == "yes":
            return "true"
        else:
            return "false"

    except Exception as e:
        print(f"Error during OpenAI API call: {e}")
        return False


def prompt_conversation(user_prompt, language_code=LANGUAGE_DEFAULT):
    start_time = time.time()
    logger.info(f"Starting prompt_conversation request - Language: {language_code}")
    db = None

    try:
        db = MongoDB.get_db()
        logger.debug(
            f"MongoDB connection established in {time.time() - start_time:.2f}s"
        )

        # Conversation retrieval
        existing_conversation = db.conversations.find_one(
            {"session_id": ""},
            {"messages": 1, "_id": 0},
        )

        messages = (
            existing_conversation.get("messages", [])
            if existing_conversation
            else [{"role": "system", "content": FIRST_MESSAGE_PROMPT}]
        )

        # Add user message
        messages.append(
            {
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Vector store retrieval
        vector_start = time.time()
        try:
            
            docs_retrieve = chatbot.brain.query(user_prompt)
            
            #store.similarity_search(
                #user_prompt, k=3  # Limit to top 3 results for performance
            #)
            logger.debug(
                f"Vector store retrieval completed in {time.time() - vector_start:.2f}s"
            )
        except Exception as ve:
            logger.error(f"Vector store error: {str(ve)}")
            docs_retrieve = []
            print(docs_retrieve)

        # OpenAI response generation
        generation_start = time.time()
        try:
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT)

            # the history of messages is the context
            messages_history = messages.copy()
            if docs_retrieve:
                context_text = " ".join([doc.page_content for doc in docs_retrieve])
                messages_history.append(
                    {"role": "system", "content": f"Relevant context: {context_text}"}
                )

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages_history,
                temperature=MAX_TEMPERATURE,
                max_tokens=MAX_TOKENS,
                timeout=OPENAI_TIMEOUT,
            )
            ai_response = response.choices[0].message.content
            logger.debug(
                f"AI response generated in {time.time() - generation_start:.2f}s"
            )
        except Exception as oe:
            logger.error(f"OpenAI error: {str(oe)}")
            raise

        return {
            "generation": ai_response,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation: {str(e)}", exc_info=True)
        raise


# Define Formatting Function
def format_docs(docs):
    return "\n".join(doc.page_content for doc in docs)


def prompt_conversation_admin(
    user_prompt,
    conversation_id,
    admin_id,
    bot_id,
    user_id,
    language_code=LANGUAGE_DEFAULT,
):

    start_time = time.time()
    logger.info(
        f"Starting prompt_conversation_admin request - Language: {language_code}"
    )
    db = None

    try:
        db = MongoDB.get_db()
        logger.debug(
            f"MongoDB connection established in {time.time() - start_time:.2f}s"
        )

        # Conversation retrieval
        existing_conversation = db.conversations.find_one(
            {"session_id": conversation_id},
            {"messages": 1, "_id": 0},
        )

        messages = (
            existing_conversation.get("messages", [])
            if existing_conversation
            else [{"role": "system", "content": FIRST_MESSAGE_PROMPT}]
        )

        # Add user message
        messages.append(
            {
                "role": "user",
                "content": user_prompt,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Vector store retrieval
        vector_start = time.time()
        docs_retrieve = []
        try:

            # Exception handling for user prompt
            if user_prompt.lower().strip() == "ok":
                docs_retrieve =chatbot.brain.query(user_prompt, k=1)
            else:
                docs_retrieve = chatbot.brain.query(user_prompt)

            for i, doc in enumerate(docs_retrieve, start=1):
                print(f"📌 Result {i}:")
                print(f"Content: {doc.page_content}\n")
                print(f"Metadata: {doc.metadata}\n")
                print("=" * 50)

            logger.debug(
                f"Vector store retrieval completed in {time.time() - vector_start:.2f}s"
            )
        except Exception as ve:
            logger.error(f"Vector store error: {str(ve)}")
            docs_retrieve = []
            print(docs_retrieve)

        # OpenAI response generation
        generation_start = time.time()
        try:

            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=OPENAI_TIMEOUT)

            # the history of messages is the context
            messages_history = messages.copy()
            if docs_retrieve:
                context_text = " ".join([doc.page_content for doc in docs_retrieve])
                messages_history.append(
                    {"role": "system", "content": f"Relevant context: {context_text}"}
                )

            response = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages_history,
                temperature=MAX_TEMPERATURE,
                max_tokens=MAX_TOKENS,
                timeout=OPENAI_TIMEOUT,
            )
            # logging.info(messages_history)
            ai_response = response.choices[0].message.content
            logger.debug(
                f"AI response generated in {time.time() - generation_start:.2f}s"
            )
        except Exception as oe:
            logger.error(f"OpenAI error: {str(oe)}")
            raise

        is_last_message = is_finalizing_phrase(ai_response)

        try:
            # Initialize LLM for Hallucination Grading
            llm_confidence = ChatOpenAI(model=OPENAI_MODEL, temperature=MAX_TEMPERATURE)
            structured_confidence_grader = llm_confidence.with_structured_output(
                GradeConfidenceLevel
            )

            # System Message for confidence Grader
            confidence_system_message = CONFIDENCE_GRADER_PROMPT
            # Create Confidence Grading Prompt
            confidence_prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", confidence_system_message),
                    (
                        "human",
                        "Source facts: \n\n {documents} \n\n AI response: {generation}",
                    ),
                ]
            )

            # Runnable Chain for Confidence Grader
            confidence_grader = confidence_prompt | structured_confidence_grader

            confidence_result = confidence_grader.invoke(
                {
                    "documents": format_docs(docs_retrieve),
                    "generation": ai_response,
                }
            )
        except Exception as ce:
            logger.error(f"Error obtaining confidence: {str(ce)}")
            confidence_result = None

        # Update conversation
        messages.append(
            {
                "role": "assistant",
                "content": ai_response,
                "timestamp": datetime.now().isoformat(),
            }
        )

        # Prepare and save conversation
        conversation = {
            "session_id": conversation_id,
            "admin_id": admin_id,
            "bot_id": bot_id,
            "user_id": user_id,
            "language": language_code,
            "messages": messages,
            "updated_at": datetime.now().isoformat(),
        }

        # Upsert with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                db.conversations.update_one(
                    {"session_id": conversation_id}, {"$set": conversation}, upsert=True
                )
                break
            except Exception as me:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"MongoDB retry {attempt + 1}/{max_retries}: {str(me)}")
                time.sleep(0.5)

        total_time = time.time() - start_time
        logger.info(f"Request completed in {total_time:.2f}s")

        return {
            "generation": ai_response,
            "conversation_id": conversation_id,
            "language": language_code,
            "is_last_message": is_last_message,
            "confidence_score": (
                confidence_result.confidence_score if confidence_result else None
            ),
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation_admin: {str(e)}", exc_info=True)
        raise
