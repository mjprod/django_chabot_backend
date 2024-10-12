# chatbot_project/api/views.py

import json
import os

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import capture_interaction, generate_answer, submit_feedback
from .serializers import (AIResponseSerializer, CaptureSummarySerializer,
                          ChatRatingSerializer, CorrectBoolSerializer,
                          IncorrectAnswerResponseSerializer,
                          UserInputSerializer, ViewSummarySerializer)


class UserInputView(APIView):
    def post(self, request):
        serializer = UserInputSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            generation = generate_answer(prompt)
            response_data = {"generation": generation}
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIResponseView(APIView):
    def post(self, request):
        serializer = AIResponseSerializer(data=request.data)
        if serializer.is_valid():
            generation = serializer.validated_data["answer"]
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CorrectBoolView(APIView):
    def post(self, request):
        serializer = CorrectBoolSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.validated_data["is_correct"]
            return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatRatingView(APIView):
    def post(self, request):
        serializer = ChatRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating = serializer.validated_data["rating"]
            return Response({"rating": rating}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class IncorrectAnswerResponseView(APIView):
    def post(self, request):
        serializer = IncorrectAnswerResponseSerializer(data=request.data)
        if serializer.is_valid():
            incorrect_answer = serializer.validated_data["incorrect_answer"]
            # Here you might want to save this to your JSON or process it further
            return Response({"message": "Incorrect answer received"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CaptureSummaryView(APIView):
    def post(self, request):
        serializer = CaptureSummarySerializer(data=request.data)
        if serializer.is_valid():
            result = capture_interaction(
            prompt = serializer.validated_data["user_input"]
            generation = serializer.validated_data["ai_response"]
            is_correct = serializer.validated_data["correct_bool"]
            rating = serializer.validated_data["chat_rating"]
            incorrect_answer = serializer.validated_data.get("incorrect_answer_response", ""),
            metadata=serializer.validated_data.get("metadata", {})
            )
        
            
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ViewSummaryView(APIView):
    def get(self, request):
        # Path to the interactions.json file
        file_path = settings.BASE_DIR / 'data' / 'interactions.json'
        
        try:
            with open(file_path, 'r') as f:
                interactions = json.load(f)
        except FileNotFoundError:
            return Response({"error": "No interactions found"}, status=status.HTTP_404_NOT_FOUND)
        except json.JSONDecodeError:
            return Response({"error": "Invalid JSON data"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Pagination
        paginator = PageNumberPagination()
        paginator.page_size = 10  # Set the number of items per page
        result_page = paginator.paginate_queryset(interactions, request)
        
        serializer = ViewSummarySerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
