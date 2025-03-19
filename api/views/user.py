from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser

class UserLoginView(APIView):
    permission_classes = [AllowAny]  # Allow anyone to access the login endpoint
    parser_classes = [JSONParser]  # Ensure JSON data is accepted

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(username=username, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            })
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)