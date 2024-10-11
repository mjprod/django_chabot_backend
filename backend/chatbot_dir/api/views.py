# chatbot_project/api/views.py

import json
import os

from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import capture_interaction, generate_answer, submit_feedback
from .serializers import (ChatRatingSerializer, CorrectAnswerSerializer,
                          CorrectBoolSerializer)


class ChatbotView(APIView):
    def post(self, request):
        serializer = CorrectAnswerSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            generation, binary_score = generate_answer(prompt)
            response_data = {"generation": generation, "binary_score": binary_score}
            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CorrectAnswerView(APIView):
    def post(self, request):
        serializer = CorrectAnswerSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data["answer"]
            self.save_to_json("responses.json", {"answer": answer})
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_to_json(self, filename, data):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, "a") as f:
            json.dump(data, f)
            f.write("\n")


class CorrectBoolView(APIView):
    def post(self, request):
        serializer = CorrectBoolSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.validated_data["is_correct"]
            self.save_to_json("feedback.json", {"is_correct": is_correct})
            return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_to_json(self, filename, data):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, "a") as f:
            json.dump(data, f)
            f.write("\n")


class ChatRatingView(APIView):
    def post(self, request):
        serializer = ChatRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating = serializer.validated_data["rating"]
            self.save_to_json("ratings.json", {"rating": rating})
            return Response({"rating": rating}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def save_to_json(self, filename, data):
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, "a") as f:
            json.dump(data, f)
            f.write("\n")


class SubmitFeedbackView(APIView):
    def post(self, request):
        data = request.data
        prompt = data.get("prompt")
        response = data.get("response")
        question_correct = data.get("question_correct")
        correct_rating = data.get("correct_rating")
        correct_answer = data.get("correct_answer")
        metadata = data.get("metadata", {})

        if not all(
            [
                prompt,
                response,
                question_correct is not None,
                correct_rating,
                correct_answer,
            ]
        ):
            return Response(
                {"error": "Missing required fields"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            question_correct = bool(question_correct)
            correct_rating = int(correct_rating)
            if not 1 <= correct_rating <= 6:
                raise ValueError("Correct_rating must be between 1 and 6")
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        result = capture_interaction(
            prompt, response, question_correct, correct_rating, correct_answer, metadata
        )
        return Response(result, status=status.HTTP_200_OK)


class CaptureInteractionView(APIView):
    def post(self, request):
        serializer = CorrectAnswerSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            response = serializer.validated_data["answer"]
            result = capture_interaction(prompt, response)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

