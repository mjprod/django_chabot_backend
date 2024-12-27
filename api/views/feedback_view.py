import logging
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..mixins.mongodb_mixin import MongoDBMixin
from ..serializers import CaptureFeedbackSerializer

logger = logging.getLogger(__name__)

class CaptureFeedbackView(MongoDBMixin, APIView):
    """
    View para capturar e salvar feedbacks.
    """

    def post(self, request):
        db = None
        try:
            logger.info("Recebendo feedback.")

            # Validar dados recebidos
            serializer = CaptureFeedbackSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Erro de validação: {serializer.errors}")
                return Response(
                    {"error": "Dados inválidos.", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Preparar documento para o MongoDB
            feedback_data = {
                **serializer.validated_data,
                "timestamp": datetime.utcnow().isoformat(),
            }

            db = self.get_db()
            db.feedback_data.insert_one(feedback_data)
            logger.info("Feedback salvo no MongoDB.")

            return Response(
                {"message": "Feedback salvo com sucesso."},
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            logger.error(f"Erro ao salvar feedback: {str(e)}", exc_info=True)
            return Response(
                {"error": "Erro ao salvar feedback."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        finally:
            if db:
                self.close_db()

    def get(self, request):
        db = None
        try:
            db = self.get_db()

            # Buscar feedbacks no banco
            feedbacks = db.feedback_data.find().sort("timestamp", -1)
            results = []
            for feedback in feedbacks:
                feedback["_id"] = str(feedback["_id"])  # Converter ObjectId
                results.append(feedback)

            return Response(results, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erro ao buscar feedbacks: {str(e)}", exc_info=True)
            return Response(
                {"error": "Erro ao buscar feedbacks."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        finally:
            if db:
                self.close_db()