from django.conf import settings
from django.http import JsonResponse


class FixedTokenAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Obter o token do cabeçalho Authorization
        token = request.headers.get("Authorization", "")

        # Verificar se o token segue o formato esperado
        expected_token = f"Token {getattr(settings, 'FIXED_API_TOKEN', '')}"

        if not settings.FIXED_API_TOKEN:  # Se o token não estiver definido no settings
            return JsonResponse(
                {"error": "Internal Server Error - Token not configured"}, status=500
            )

        if token != expected_token:
            return JsonResponse({"error": "Invalid token"}, status=403)

        return self.get_response(request)
