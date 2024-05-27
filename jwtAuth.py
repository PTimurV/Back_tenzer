import jwt
import datetime
from config import jwt_secret, jwt_algorithm
from jwt import ExpiredSignatureError, InvalidTokenError

class JWTAuth:
    JWT_SECRET = jwt_secret
    JWT_ALGORITHM = jwt_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = 15
    REFRESH_TOKEN_EXPIRE_DAYS = 30

    @classmethod
    def create_access_token(cls, data, expires_delta=None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)
        return encoded_jwt

    @classmethod
    def create_refresh_token(cls, data, expires_delta=None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.datetime.utcnow() + expires_delta
        else:
            expire = datetime.datetime.utcnow() + datetime.timedelta(days=cls.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, cls.JWT_SECRET, algorithm=cls.JWT_ALGORITHM)
        return encoded_jwt
    
    @classmethod
    def decode_refresh_token(cls, token):
        try:
            # Попытка декодирования токена с проверкой на валидность
            decoded = jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])
            return decoded
        except ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Refresh token expired.")
        except InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid refresh token.")
        
    @classmethod
    def decode_access_token(cls, token):
        try:
            # Попытка декодирования токена с проверкой на валидность
            decoded = jwt.decode(token, cls.JWT_SECRET, algorithms=[cls.JWT_ALGORITHM])
            return decoded
        except ExpiredSignatureError:
            raise jwt.ExpiredSignatureError("Access token expired.")
        except InvalidTokenError:
            raise jwt.InvalidTokenError("Invalid access token.")