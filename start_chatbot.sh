#!/bin/bash

# Navigate to the backend directory
cd ~/chatbot

# Activate the virtual environment
#source venv/bin/activate

python3.10 -m venv venv
source venv/bin/activate

cd ~/django_chabot_backend

#cd ~/chatbot/django_chabot_backend/backend/chatbot_dir

# Run the parameter_store_loader python file to update the .env with correct details
#python3 parameter_store_loader.py


# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Run Django development server
# python3 manage.py runserver 0.0.0.0:8000
python3 manage.py runserver 0.0.0.0:8000 --settings=settings.local
# python3 manage.py runserver 0.0.0.0:8000 --settings=settings.staging
# python3 manage.py runserver 0.0.0.0:8000 --settings=settings.production
