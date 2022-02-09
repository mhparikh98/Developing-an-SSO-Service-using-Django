from cryptography.fernet import Fernet
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings


class HelloPythonistaAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        f_key = settings.FERNET_KEY
        fernet = Fernet(f_key)
        content = {'message': 'Hello, Pythonistas, from Stand-Alone-Service!', "user_id": fernet.decrypt(request.user.token.get("user_id").encode()).decode()}
        return Response(content)
