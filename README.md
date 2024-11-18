Chatbot Backend


This Django-based backend serves as the core for a multilingual chatbot system with Retrieval-Augmented Generation (RAG) capabilities. It's designed to process user inputs, generate responses, and handle various interactions while supporting both English and Bahasa Malay languages.
Purpose


The main purposes of this backend are:
To provide a robust API for handling user queries and generating appropriate responses.
To implement a RAG system for more accurate and context-aware answers.
To support multilingual interactions, specifically English and Bahasa Malay.
To capture and store user interactions for future analysis and improvement.


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


Data Flow

User sends a query through the UserInputView.
The backend processes the query using the RAG system in chatbot.py.
A response is generated and translated if necessary.
The interaction is saved for future reference.
Additional endpoints allow for feedback, ratings, and corrections to be submitted and stored.


Setup and Configuration

Ensure all required environment variables are set, including API keys for OpenAI and Mesolitica.
Install all dependencies listed in requirements.txt.
Run migrations to set up the database.
Use python manage.py runserver to start the development server.


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
