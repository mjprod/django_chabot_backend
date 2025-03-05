import os
import logging
import time
import asyncio


from openai import OpenAI
from datetime import datetime
from langchain.vectorstores import Chroma
from langchain.embeddings import CohereEmbeddings

from ai_config.ai_constants import (
    OPENAI_MODEL,
    OPENAI_TIMEOUT,
    MAX_TOKENS,
    MAX_TEMPERATURE,
    LANGUAGE_DEFAULT,
)

from ai_config.ai_constants import (
    OPENAI_MODEL,
    OPENAI_TIMEOUT,
    MAX_TOKENS,
    MAX_TEMPERATURE,
    LANGUAGE_DEFAULT,
)

from ai_config.ai_prompts import (
    FIRST_MESSAGE_PROMPT,
)

from api.chatbot import (
    confidence_grader,
    format_docs,
    store,
    retriever,
    retrieval_grader,
    rag_chain,
)

from api.translation import (
  generate_translations,
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
    
def prompt_conversation(self, user_prompt, store ,language_code=LANGUAGE_DEFAULT):
    start_time = time.time()
    logger.info(f"Starting prompt_conversation request - Language: {language_code}")
    db = None

    try:
        # Database connection with timeout
        db = self.get_db()
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
            docs_retrieve = store.similarity_search(
                user_prompt, k=3  # Limit to top 3 results for performance
            )
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
    finally:
        if db is not None:
            self.close_db()



def i_need_this_knowledge(db,conversation_id, user_prompt,ai_response, confidence_score):
    document = {
        "conversation_id": conversation_id,
        "user_prompt": user_prompt,
        "generation": ai_response,
        "confidence_score": confidence_score,
    }
    try:
        db.low_confidence_responses.update_one(
            {"session_id": conversation_id},
            {"$set": document},
            upsert=True
        )
    except Exception as me:
        logger.warning(f"MongoDB error: {str(me)}")
        raise  

def prompt_conversation_admin(
    self,
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
        # Database connection with timeout
        db = self.get_db()
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
            #TODO: I tried to send as prop but it didn't work
           # COHERE_MODEL = "embed-multilingual-v3.0"
           # embedding_model = CohereEmbeddings(model=COHERE_MODEL, user_agent="glaucomp")

           # store = Chroma(
            #    persist_directory="./chroma_db",
            #    embedding_function=embedding_model,
            #    collection_name="RAG"
          #  )

            # Exception handling for user prompt
            if user_prompt.lower().strip() == "ok":
                docs_retrieve = store.similarity_search(user_prompt, k=1)
            else:
                docs_retrieve = store.similarity_search(user_prompt, k=3)
            
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
            #logging.info(messages_history)
            ai_response = response.choices[0].message.content
            logger.debug(
                f"AI response generated in {time.time() - generation_start:.2f}s"
            )
        except Exception as oe:
            logger.error(f"OpenAI error: {str(oe)}")
            raise

        is_last_message = is_finalizing_phrase(ai_response)

        try:
            confidence_result = confidence_grader.invoke({
                "documents": format_docs(docs_retrieve),
                "generation": ai_response,
            })
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

        if confidence_result and confidence_result.confidence_score < 0.65:
            i_need_this_knowledge(db,conversation_id,user_prompt, ai_response, confidence_result.confidence_score)

        total_time = time.time() - start_time
        logger.info(f"Request completed in {total_time:.2f}s")

        return {
            "generation": ai_response,
            "conversation_id": conversation_id,
            "language": language_code,
            "is_last_message": is_last_message,
            "confidence_score": confidence_result.confidence_score if confidence_result else None,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation_admin: {str(e)}", exc_info=True)
        raise
    finally:
        if db is not None:
            self.close_db()

'''
def generate_user_input(cleaned_prompt):
    # Get relevant documents
    docs_retrieve = retriever.get_relevant_documents(cleaned_prompt)
    logger.error(f"Retrieved {len(docs_retrieve)} documents")

    docs_to_use = []

    # Filter documents
    for doc in docs_retrieve:
        relevance_score = retrieval_grader.invoke(
            {"prompt": cleaned_prompt, "document": doc.page_content}
        )
        if relevance_score.confidence_score >= 0.7:
            docs_to_use.append(doc)

    # Generate response
    generation = rag_chain.invoke(
        {
            "context": format_docs(docs_to_use),
            "prompt": cleaned_prompt,
        }
    )

    # Generate translations asynchronously
    translations = asyncio.run(generate_translations(generation))

    return {
        "generation": generation,
        "translations": translations,
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }



def generate_prompt_conversation(
    user_prompt, conversation_id, admin_id, bot_id, user_id
):
    logger.info("Starting prompt_conversation request")

    try:
        # this is a check for the conversation to remove Dear player
        db = get_mongodb_client()
        existing_conversation = db.conversations.find_one(
            {"session_id": conversation_id}
        )
        is_first_message = not existing_conversation

        # Initialize conversation
        conversation = ConversationMetaData(
            session_id=conversation_id,
            admin_id=admin_id,
            bot_id=bot_id,
            user_id=user_id,
        )
        conversation.is_first_message = is_first_message

        rag_prompt = get_rag_prompt_template(is_first_message)

        # Process prompt and add message
        logger.info("Processing user prompt")
        cleaned_prompt = translate_and_clean(user_prompt)
        conversation.add_message("user", user_prompt)

        # Get and filter relevant documents
        logger.info("Retrieving relevant documents")
        docs_start = time.time()
        docs_retrieve = retriever.invoke(cleaned_prompt)[:3]  # Limit initial retrieval
        docs_to_use = []

        for doc in docs_retrieve:
            relevance_score = retrieval_grader.invoke(
                {"prompt": cleaned_prompt, "document": doc.page_content}
            )
            if relevance_score.confidence_score >= 0.7:
                docs_to_use.append(doc)
        logger.info(f"Document retrieval completed in {time.time() - docs_start:.2f}s")

        # Generate  inital response
        logger.info("Generating AI response")
        dynamic_chain = (
            {
                "context": lambda x: format_docs(docs_to_use),
                "prompt": RunnablePassthrough(),
            }
            | rag_prompt
            | rag_llm
            | StrOutputParser()
        )

        # generation_start = time.time()
        generation = dynamic_chain.invoke(
            {
                "context": format_docs(docs_to_use),
                "prompt": cleaned_prompt,
                "history": conversation.get_conversation_history(),
            }
        )
        # logger.info(f"AI Generation completed in {time.time() - generation_start:.2f}s")

        # this is where the self learning comes in, Its rough but will be worked on over time
        # logger.info("Starting self-learning comparison")

        """
        db = get_mongodb_client()
        relevant_feedbacks = get_relevant_feedback_data(cleaned_prompt, db)

        comparison_result = {
            "better_answer": None,
            "confidence_diff": 0.0,
            "generated_score": 0.0,
            "feedback_score": 0.0,
            "best_feedback": None,
        }

        if relevant_feedbacks:
            logger.info(f"Found {len(relevant_feedbacks)} relevant feedback answers")
            comparison_result = compare_answers(
               generation, relevant_feedbacks, docs_to_use
           )

        if comparison_result and comparison_result["better_answer"] == "feedback":
            logger.info("Using feedback answer with higher confidence")
            generation = comparison_result["best_feedback"]["correct_answer"]
            update_database_confidence(comparison_result, docs_to_use)
        else:
            logger.info("Generated answer maintained, updating confidence")
            update_local_confidence(
                 generation, comparison_result["confidence_diff"]
            )
        """

        # Calculate confidence
        confidence_result = confidence_grader.invoke(
            {"documents": format_docs(docs_to_use), "generation": generation}
        )

        # Generate translations asynchronously
        translation_start = time.time()
        translations = asyncio.run(generate_translations(generation))
        logger.info(f"Translations completed in {time.time() - translation_start:.2f}s")

        return {
            "generation": generation,
            "conversation": conversation.to_dict(),
            "confidence_score": confidence_result.confidence_score,
            "translations": translations,
        }

    except Exception as e:
        logger.error(f"Error in prompt_conversation: {str(e)}")
        raise
    finally:
        # compare_memory(memory_snapshot)
        gc.collect()


'''








            