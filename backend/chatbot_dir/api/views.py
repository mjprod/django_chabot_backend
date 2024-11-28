import json
import os
from datetime import datetime

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .chatbot import (
    generate_answer,
    save_interaction,
    translate_and_clean,
    translate_en_to_ms,
)
from .serializers import (
    AIResponseSerializer,
    CaptureSummarySerializer,
    ChatRatingSerializer,
    CorrectBoolSerializer,
    IncorrectAnswerResponseSerializer,
    UserInputSerializer,
    ViewSummarySerializer,
)


class UserInputView(APIView):
    def post(self, request):
        serializer = UserInputSerializer(data=request.data)
        if serializer.is_valid():
            prompt = serializer.validated_data["prompt"]
            user_id = serializer.validated_data["user_id"]

            # added the translation here
            cleaned_prompt = translate_and_clean(prompt)

            generation = generate_answer(cleaned_prompt)

            response_data = {
                "user_id": user_id,
                "prompt": prompt,
                "cleaned_prompt": cleaned_prompt,
                "generation": generation["generation"],
                "translations": generation["translations"],
                "usage": {
                    "prompt_tokens": generation["usage"].get("prompt_tokens", 0),
                    "completion_tokens": generation["usage"].get(
                        "completion_tokens", 0
                    ),
                    "total_tokens": generation["usage"].get("total_tokens", 0),
                },
            }

            save_interaction(
                "user_input",
                {
                    "user_id": user_id,
                    "prompt": prompt,
                    "cleaned_prompt": cleaned_prompt,
                    "generation": generation["generation"],
                    "translations": generation["translations"],
                },
            )

            return Response(response_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIResponseView(APIView):
    def post(self, request):
        serializer = AIResponseSerializer(data=request.data)
        if serializer.is_valid():
            answer = serializer.validated_data["answer"]
            save_interaction("ai_response", {"answer": answer})
            return Response({"answer": answer}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CorrectBoolView(APIView):
    def post(self, request):
        serializer = CorrectBoolSerializer(data=request.data)
        if serializer.is_valid():
            is_correct = serializer.validated_data["is_correct"]
            save_interaction("correct_bool", {"is_correct": is_correct})
            return Response({"is_correct": is_correct}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChatRatingView(APIView):
    def post(self, request):
        serializer = ChatRatingSerializer(data=request.data)
        if serializer.is_valid():
            rating = serializer.validated_data["rating"]
            save_interaction("chat_rating", {"rating": rating})
            return Response({"rating": rating}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class IncorrectAnswerResponseView(APIView):
    def post(self, request):
        serializer = IncorrectAnswerResponseSerializer(data=request.data)
        if serializer.is_valid():
            incorrect_answer = serializer.validated_data["incorrect_answer"]
            save_interaction(
                "incorrect_answer_response", {"incorrect_answer": incorrect_answer}
            )
            return Response(
                {"message": "Correct answer received"}, status=status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CaptureSummaryView(APIView):
    def post(self, request):
        serializer = CaptureSummarySerializer(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            result = save_interaction("complete_interaction", data)
            return Response(result, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# changed the ViewSummary API to work for the new malay/english
class ViewSummaryView(APIView):
    def get(self, request):
        try:
            file_path = os.path.join(
                os.path.dirname(__file__), "../data/interactions.json"
            )

            if not os.path.exists(file_path):
                return Response(
                    {"error": "No data available"}, status=status.HTTP_404_NOT_FOUND
                )

            try:
                with open(file_path, "r") as f:
                    interactions = json.load(f)
                    if not isinstance(interactions, list):
                        return Response(
                            {"error": "Invalid data format"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        )

            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid JSON data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            summaries = []
            for interaction in interactions:
                try:
                    if interaction.get("Type") == "user_input":
                        data = interaction.get("Data", {})
                        summary = {
                            "user_id": data.get("user_id", 0),
                            "Date_time": interaction.get("Date_time"),
                            "Question": data.get("prompt", ""),
                            "Cleaned_Question": data.get("cleaned_prompt", ""),
                            "generation": data.get("generation", ""),
                            "translations": data.get("translations", []),
                            "Question_correct": False,
                            "Correct_rating": 0,
                            "Correct_Answer": "",
                            "Metadata": {},
                        }
                        summaries.append(summary)
                except AttributeError:
                    continue  # Skip malformed entries

            return Response(summaries, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def save_to_json(self, filename, data):
        file_path = os.path.join(settings.BASE_DIR, "data", filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "a") as f:
            json.dump(data, f)
            f.write("\n")
