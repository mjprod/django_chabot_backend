from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import threading
from datetime import datetime, timedelta


from api.services.conversation_streaming_manager import ConversationStreamingManager


import logging
logger = logging.getLogger("api")
   
class StreamConversationsAPIView(APIView):
    def post(self, request, *args, **kwargs):

        user_date = request.data.get("date")
        current_date = datetime.now()

        if user_date:
            try:
                formatted_date = datetime.strptime(user_date, "%Y-%m-%d").strftime('%Y-%m-%d')
            except ValueError:
                return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else: 
            return Response({"error": "'date' is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Asynchronously run the streaming process
        def run_streaming():
            manager = ConversationStreamingManager()
            manager.streaming_conversations_from_db(formatted_date)
            logger.info(f"Task executed at {datetime.now()} for streamed conversations on date: {formatted_date}")

        threading.Thread(target=run_streaming, daemon=True).start()
        
        return Response({"message": f"Streaming started for date: {formatted_date}"}, status=status.HTTP_202_ACCEPTED)