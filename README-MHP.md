# Django SSO

sso refers to Single Sign On where there will be multiple apps along with multiple portal 
but they will be having single or common authentication.

due to this one has to login single time and can switch to different apps without multiple time authentication.

SSO can be implemented using SAML, OpenID Connect and Oauth methodology.

so over here we have implementation using OpenID connect.

We have 2 django projects in implementation.
```diff
- A. Single-Sign-On
- B. StandAloneService
```

### A. Single-Sign-On:
This server is basically used to generate the jwt token where the token is generated using RS256 algorithm so for RS256 algorithm we have generated the public and private key if not present in the project within **sso_server/settings.py** so the file will be generated in the path **Single-Sign-on/config** and the snippet code to generate the public and private key is

```python
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

CONFIG_DIR = os.path.join(Path(BASE_DIR).parent, 'config')
JWT_PRIVATE_KEY_PATH = os.path.join(CONFIG_DIR, 'jwt_key')
JWT_PUBLIC_KEY_PATH = os.path.join(CONFIG_DIR, 'jwt_key.pub')

if (not os.path.exists(JWT_PRIVATE_KEY_PATH)) or (not os.path.exists(JWT_PUBLIC_KEY_PATH)):

    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=4096,
        backend=default_backend()
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )
    with open(JWT_PRIVATE_KEY_PATH, 'w') as pk:
        pk.write(pem.decode())

    public_key = private_key.public_key()
    pem_public = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(JWT_PUBLIC_KEY_PATH, 'w') as pk:
        pk.write(pem_public.decode())
    print('PUBLIC/PRIVATE keys Generated!')
```
Thus 2 files will be generated 
A. jwt_key (private key) 
B. jwt_key.pub (public key)

then we will add the public and private key in simple jwt configuration

```python
SIMPLE_JWT = {
    ...
    'ALGORITHM': 'RS256',  # 'alg' (Algorithm Used) specified in header

    'SIGNING_KEY': open(JWT_PRIVATE_KEY_PATH).read(),
    'VERIFYING_KEY': open(JWT_PUBLIC_KEY_PATH).read(),
    ....
}
```

thus over here we are using **asymmetric encryption algorithm** to generate the jwt token.

In order to store the outstanding token and blacklist token we need to do following changes in installed apps and then we need to apply migrations using migrate command **python manage.py migrate** this will create the OutstandingToken and BlacklistedToken table and will be also shown in the admin panel.

```python
INSTALLED_APPS = [
    ...
    "rest_framework_simplejwt.token_blacklist",
    ...
```

In this we will create users using signup api as follows:

```
URL: http://localhost:8000/signup/
Method: POST
Request Body: 
{
    "email": <email>,
    "first_name": <first_name>,
    "last_name": <last_name>,
    "password": <password>,
    "phone_number": "+919123456780"
}
```

Now to add the addititonal payload values in encryted form inside the jwt token we have overrided the inbuilt ***TokenObtainPairSerializer, TokenObtainPairView, Token class, and RefreshUser class*** of the restframework_simplejwt, we are also encrypting the payload over here

so we have following classes 

```python
** In Single-Sign-On/src/sso_server/jwt.py **


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from sso_server.utils import CustomRefreshUser


class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return CustomRefreshUser.for_user(user)
    
    
class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer
    
** In Single-Sign-On/src/sso_server/utils.py ** 

- please review the file for the same
```

Now using the login url we will get the access and refresh token in which the refresh token will be stored in the OutstandingToken Model

```
URL: http://localhost:8000/api/token/
Method: POST
Request Body:
{
    "email": <email>,
    "password": <password>
}
```

Thus the access token obtained over here will be used in other services or app.

### B. StandAloneService

The JWT token generated through sso server will be passed into the StandAloneService or the other
service which we will create thus that token will be used for authentication.

Now jwt token is signed using RSA algorithm provided with public and private key in the sso server so 
in order to verify the signature of the jwt token we will be using the public key provided in the sso server over here
so the configuration of simple_jwt in **StandAloneService/src/service_server/settings.py** will be 

```python

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

# Over here sso_jwt_key.pub file is same as jwt_key.pub generated for sso server, only name is changed
SSO_JWT_PUBLIC_KEY_PATH = os.path.join(Path(BASE_DIR).parent, 'config', 'sso_jwt_key.pub') 

with open(SSO_JWT_PUBLIC_KEY_PATH, "rb") as key_file:
    public_key = serialization.load_pem_public_key(key_file.read(), backend=default_backend())

SIMPLE_JWT = {
    ...
    'ALGORITHM': 'RS256',
    'SIGNING_KEY': None,
    'VERIFYING_KEY': public_key,
    ...
}
```

Now restframework_simplejwt library has 2 classes for authentication.
```diff
- A. JWTTokenUserAuthentication
- B. JWTAuthentication
```

so in service_provider we have used JWTTokenUserAuthentication instead of JWTAuthentication because
in the standaloneservice server database we are not storing the user and JWTAuthentication will
try to fetch the user from the database while JWTTokenUserAuthentication will not try to fetch the user object and 
on ***request.user*** code it will return us the object of JWTTokenUserAuthentication itself hence for us there will
be no need to store the user again in other database.

Thus the settings for it will be 

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTTokenUserAuthentication',
    ],
}
```

After obtaining the token from sso server for specific user we can pass the access token as bearer token
during the api call

we can obtain the necessary data from token in the views like

```python
user_id = request.user.token.get("user_id")
```

and the api call would look like this

```python
URL: localhost:8001/api/protected-resource/
Method: GET
Authorization: 
    - Type: Bearer Token
    - add token value
```

Reference Links:
- https://medium.com/vx-company/oauth-and-openid-explained-with-real-life-examples-bf40daa8049f#:~:text=Logging%20into%20Spotify%20with%20your,those%20details%20to%20identify%20you.
- https://medium.com/@Sendbird/implementing-single-sign-on-sso-for-a-product-dashboard-a20e90d5630e
- https://www.geeksforgeeks.org/how-to-encrypt-and-decrypt-strings-in-python/
- https://www.youtube.com/watch?v=4BN2Np7fUqY (In this project implemented like this)
- https://github.com/Vibhu-Agarwal/Developing-an-SSO-Service-using-Django (consider our implementation as fork of this)