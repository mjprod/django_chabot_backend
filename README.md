Chatbot Backend

Key Components

1. Chatbot Engine (chatbot.py)
Implements the core logic for document retrieval and answer generation.
Uses Cohere embeddings and Chroma vector store for efficient document retrieval.
Integrates with the Groq API for language model inference.
Handles translation between English and Bahasa Malay.

2. API Views (views.py)
Provides several API endpoints for different functionalities:
UserInputView: Handles user queries and generates responses.
AIResponseView: Processes AI-generated responses.
CorrectBoolView: Captures feedback on response correctness.
ChatRatingView: Allows users to rate chat interactions.
IncorrectAnswerResponseView: Handles submission of correct answers for incorrect responses.
CaptureSummaryView: Summarizes and saves complete interactions.
ViewSummaryView: Retrieves summaries of past interactions.

3. Serializers (serializers.py)
Defines data serialization for API requests and responses, ensuring proper data formatting and validation.
API Endpoints
POST /api/user_input/: Submit user queries and receive chatbot responses.
POST /api/ai_response/: Process AI-generated responses.
POST /api/correct_bool/: Submit feedback on response correctness.
POST /api/chat_rating/: Submit ratings for chat interactions.
POST /api/incorrect_answer_response/: Submit correct answers for incorrect responses.
POST /api/capture_summary/: Save complete interaction summaries.
GET /api/view_summary/: Retrieve summaries of past interactions.

Setup and Configuration

Ensure all required environment variables are set, including API keys for OpenAI and Mesolitica.
Install all dependencies listed in requirements.txt.
Run migrations to set up the database.
Use python manage.py runserver to start the development server.
SSL config:
go to a file called create_nginx_config.py under chatbot_project/SSL

Run this file with "sudo python3 create_nginx_config_1.py"

once this is run, test with "sudo nginx -t"

if successful then run "sudo systemctl reload nginx"



Important Notes
All API endpoints expect and return JSON data.
The UserInputView handles both English and Bahasa Malay inputs and provides translations.
Implement error handling for potential API failures or unexpected responses.
Use the ViewSummaryView to retrieve past interactions for display or analysis.
Ensure proper handling of user feedback and ratings through the respective endpoints.

Future Improvements
Implement user authentication for personalized experiences.
Expand language support beyond English and Bahasa Malay.
Enhance the RAG system with more advanced retrieval techniques.
Implement a feedback loop to continuously improve the chatbot's responses.
For any questions or issues, please contact me.
