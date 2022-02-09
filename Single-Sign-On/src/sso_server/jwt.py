from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.utils import datetime_from_epoch
from services.models import Service
from rest_framework_simplejwt.tokens import Token
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import get_user_model
from django.conf import settings
from sso_server.utils import CustomRefreshUser

User = get_user_model()


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return CustomRefreshUser.for_user(user)
        # token = super().get_token(user)
        #
        # token['aud'] = []
        # user_services = Service.for_user(user)
        # for service in user_services:
        #     token['aud'].append(service.identifier)
        #
        # return token

# A JWT access-token example
#
# {
#     'token_type': 'access',
#     'exp': 1599980514,
#     'jti': 'a3c77262a57d4df5a657fe12860c8492',
#     'user_id': '9a7b69e2-df4d-4c98-bc04-941c66cff1a0',
#     'aud': ['Docs', 'Sheets']
# }
#


class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
