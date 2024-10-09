# chatbot_project/api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
from .serializers import (
    CorrectAnswerSerializer,
    CorrectBoolSerializer,
    ChatRatingSerializer
)
from .chatbot import generate_answer, submit_feedback
import os
import json

class ChatbotView(APIView):
    def post(self, request):
        serializer = CorrectAnswerSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data['prompt']
            generation, binary_score = generate_answer(prompt)
            response_data = {
                'generation': generation,
                'binary_score': binary_score
            }
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CorrectAnswerView(APIView):
    def post(self, request):
        serializer = CorrectAnswerSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data['answer']
            self.save_to_json('responses.json', {'answer': answer})
            return Response({'answer': answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_to_json(self, filename, data):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, 'a') as f:
            json.dump(data, f)
            f.write('\n')

class CorrectBoolView(APIView):
    def post(self, request):
        serializer = CorrectBoolSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.validated_data['is_correct']
            self.save_to_json('feedback.json', {'is_correct': is_correct})
            return Response({'is_correct': is_correct}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_to_json(self, filename, data):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, 'a') as f:
            json.dump(data, f)
            f.write('\n')

class ChatRatingView(APIView):
    def post(self, request):
        serializer = ChatRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating = serializer.validated_data['rating']
            self.save_to_json('ratings.json', {'rating': rating})
            return Response({'rating': rating}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_to_json(self, filename, data):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, 'a') as f:
            json.dump(data, f)
            f.write('\n')

class SubmitFeedbackView(APIView):
    def post(self, request):
        return submit_feedback(request)