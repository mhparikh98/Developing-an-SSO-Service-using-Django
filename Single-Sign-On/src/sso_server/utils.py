from django.conf import settings
from rest_framework_simplejwt.tokens import Token, BlacklistMixin, AccessToken
from services.models import Service
from cryptography.fernet import Fernet

f_key = settings.FERNET_KEY
fernet = Fernet(f_key)


class CustomToken(Token):

    def __init__(self, token=None, verify=True, *args, **kwargs):
        Token.__init__(self, token=token, verify=verify)
        user = kwargs.get("user")
        if user:
            user_services = Service.for_user(user)
            self.payload['aud'] = []
            self.payload.update({"aud": [fernet.encrypt("DOC".encode()).decode()]})
            for service in user_services:
                self.payload['aud'].extend(fernet.encrypt(service.identifier.encode()).decode())

    def __setitem__(self, key, value):
        self.payload[key] = fernet.encrypt(value.encode()).decode()

    @classmethod
    def for_user(cls, user):
        """
        Returns an authorization token for the given user that will be provided
        after authenticating the user's credentials.
        """
        user_id = getattr(user, settings.SIMPLE_JWT.get("USER_ID_FIELD"))
        if not isinstance(user_id, int):
            user_id = str(user_id)
        token = cls(user=user)
        token[settings.SIMPLE_JWT.get("USER_ID_CLAIM")] = user_id

        return token


class CustomRefreshUser(BlacklistMixin, CustomToken):
    token_type = 'refresh'
    lifetime = settings.SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME")
    no_copy_claims = (
        settings.SIMPLE_JWT.get("TOKEN_TYPE_CLAIM"),
        'exp',

        # Both of these claims are included even though they may be the same.
        # It seems possible that a third party token might have a custom or
        # namespaced JTI claim as well as a default "jti" claim.  In that case,
        # we wouldn't want to copy either one.
        settings.SIMPLE_JWT.get("JTI_CLAIM"),
        'jti',
    )

    @property
    def access_token(self):
        """
        Returns an access token created from this refresh token.  Copies all
        claims present in this refresh token to the new access token except
        those claims listed in the `no_copy_claims` attribute.
        """
        access = AccessToken()

        # Use instantiation time of refresh token as relative timestamp for
        # access token "exp" claim.  This ensures that both a refresh and
        # access token expire relative to the same time if they are created as
        # a pair.
        access.set_exp(from_time=self.current_time)

        no_copy = self.no_copy_claims
        for claim, value in self.payload.items():
            if claim in no_copy:
                continue
            access[claim] = value

        return access
