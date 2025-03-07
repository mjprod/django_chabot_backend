from time import sleep
from openai import OpenAI
from pymongo import MongoClient
import json

# MongoDB Configuration
MONGODB_USERNAME = "dev"
MONGODB_PASSWORD = "Yrr0szjwTuE1BU7Y"
MONGODB_CLUSTER = "chatbotdb-dev.0bcs2.mongodb.net"
# MONGODB_CLUSTER = "chatbotdb-staging.0bcs2.mongodb.net"
MONGODB_DATABASE = "chatbotdb"


# Connect to MongoDB
try:
    client = MongoClient(
        f"mongodb+srv://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@"
        f"{MONGODB_CLUSTER}/{MONGODB_DATABASE}?"
        f"retryWrites=true&w=majority&tlsAllowInvalidCertificates=true"
    )
    db = client[MONGODB_DATABASE]
    print("Connected to MongoDB successfully.")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    exit()
COLLECTION_NAME = "old_conversation"


def get_data_from_mongo():
    """Fetch conversations from MongoDB."""
    collection = db[COLLECTION_NAME]

    # Fetch all documents with conversation history
    documents = collection.find({}, {"historyMsgs": 1})
    return list(documents)

def extract_main_question_and_solution(conversation):
    """Extracts the main question (user's message) and the best support response."""

    # Ensure 'historyMsgs' exists and is a list
    history_msgs = conversation.get("historyMsgs", [])

    if not isinstance(history_msgs, list):
        return {"flagged_as_irrelevant": True}

    # Separate user and support messages
    user_messages = [msg["Msg"] for msg in history_msgs if not msg.get("IsService", False)]
    support_messages = [msg["Msg"] for msg in history_msgs if msg.get("IsService", False)]

    # Validate that there is a user message
    if not user_messages:
        return {"flagged_as_irrelevant": True}

    # Define the main problem as the first real user message
    main_problem = user_messages[0] if user_messages else None

    # Define the main solution as the first valid support response
    main_solution = support_messages[0] if support_messages else None

    # If we have no valid problem or solution, flag as irrelevant
    if not main_problem or not main_solution:
        return {"flagged_as_irrelevant": True}

    return {"main_problem": main_problem, "main_solution": main_solution}

    return formatted_conversation

def send_to_openai(conversation_text):
    """Sends the conversation to OpenAI to determine the main question and the correct response."""
    prompt = f"""
Here is a conversation between a user and support.

{conversation_text}

Your task:
1. Identify the **main question** asked by the user. 
2. Identify the **best response** given by the support that provides a **clear solution**.
3. **DO NOT** modify any words. Keep everything exactly as said.
4. If the user's question is not clear, or there is no valid solution from support, return: `"flagged_as_irrelevant": true`
5. Use the following rules:
   - `"IsService": true` → This message is from **support**.
   - `"IsService": false` → This message is from **the user**.
   - **main_problem** = The user's main question.
   - **main_solution** = The support's response that provides a clear solution.

Respond in **JSON format**:
{{
  "main_problem": "<user's question>",
  "main_solution": "<support's response>"
}}
"""
    print(prompt)
    # sleep(100)
    try:
            
            client = OpenAI(api_key="")


            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )
            #logging.info(messages_history)
            ai_response = response.choices[0].message.content
            print(ai_response)
            return ai_response
          
    except Exception as e:
          print(f"OpenAI API error: {e}")
          return None

      
      

def process_documents():
    """Processes MongoDB conversations, extracts key messages, and updates the database."""
    collection = db[COLLECTION_NAME]

    data = get_data_from_mongo()
    print(f"Processing {len(data)} documents...")

    for doc in data:
        doc_id = doc["_id"]
        
        # Ensure the doc contains 'historyMsgs' before processing
        if "historyMsgs" not in doc or not isinstance(doc["historyMsgs"], list):
            print(f"⚠️ Skipping document {doc_id}, missing or invalid 'historyMsgs'.")
            continue

        # Pass the full document, not just the messages list
        conversation_text = extract_main_question_and_solution(doc)

        # Send to OpenAI
        openai_response = send_to_openai(conversation_text)

        if openai_response:
            try:
                # Parse OpenAI response as JSON
                response_data = json.loads(openai_response)

                # Extract fields safely
                main_problem = response_data.get("main_problem")
                main_solution = response_data.get("main_solution")

                if main_problem and main_solution:
                    # Update MongoDB with valid extracted problem and solution
                    collection.update_one(
                        {"_id": doc_id},
                        {"$set": {
                            "main_problem": main_problem,
                            "main_solution": main_solution,
                            "validated_response": openai_response
                        }}
                    )
                    print(f"✅ Updated document {doc_id} with extracted problem and solution.")
                else:
                    # If OpenAI couldn't extract a valid issue, flag as irrelevant
                    collection.update_one(
                        {"_id": doc_id},
                        {"$set": {"flagged_as_irrelevant": True}}
                    )
                    print(f"⚠️ Document {doc_id} flagged as irrelevant.")

            except json.JSONDecodeError:
                # Handle cases where OpenAI doesn't return valid JSON
                collection.update_one(
                    {"_id": doc_id},
                    {"$set": {"flagged_as_irrelevant": True}}
                )
                print(f"⚠️ OpenAI response could not be parsed. Document {doc_id} flagged as irrelevant.")
        
        else:
            # If OpenAI response is empty or None, flag as irrelevant
            collection.update_one(
                {"_id": doc_id},
                {"$set": {"flagged_as_irrelevant": True}}
            )
            print(f"⚠️ OpenAI returned no response. Document {doc_id} flagged as irrelevant.")

        # Prevent OpenAI rate-limiting issues by waiting
        sleep(60)
    

if __name__ == "__main__":
    process_documents()