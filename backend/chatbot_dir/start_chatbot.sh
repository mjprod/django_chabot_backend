#!/bin/bash
# Navigate to the backend directory
cd ~/chatbot
# Activate the virtual environment
source venv/bin/activate
cd ~/chatbot/django_chabot_backend/backend/chatbot_dir
#run the parameter_store_loader python file to udpate the .env with correct details
python3 parameter_store_loader.py
# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)
# Run Django development server
python3 manage.py runserver 0.0.0.0:8000

