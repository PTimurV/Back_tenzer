from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, User
from jwtAuth import JWTAuth
import datetime
import jwt

class AuthHandler:
    async def register(self, request):
        data = await request.json()
        userEmail = data.get('email')
        userLogin = data.get('login')
        userPassword = data.get('password')

        try:
            # Создание нового пользователя
            new_user = User(email=userEmail, login=userLogin, password=userPassword)
            db_session.add(new_user)
            db_session.commit()

            # Создание токенов доступа и обновления
            access_token_expires = datetime.timedelta(minutes=JWTAuth.ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = datetime.timedelta(days=JWTAuth.REFRESH_TOKEN_EXPIRE_DAYS)
            
            access_token = JWTAuth.create_access_token(data={"sub": userLogin}, expires_delta=access_token_expires)
            refresh_token = JWTAuth.create_refresh_token(data={"sub": userLogin}, expires_delta=refresh_token_expires)

            return web.json_response({
                'message': 'User registered successfully',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, status=201)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)

    async def login(self, request):
        data = await request.json()
        userLogin = data.get('login')
        userPassword = data.get('password')

        try:
            user = db_session.query(User).filter(User.login == userLogin, User.password == userPassword).first()
            if user:
                access_token_expires = datetime.timedelta(minutes=JWTAuth.ACCESS_TOKEN_EXPIRE_MINUTES)
                refresh_token_expires = datetime.timedelta(days=JWTAuth.REFRESH_TOKEN_EXPIRE_DAYS)
                
                access_token = JWTAuth.create_access_token(data={"sub": userLogin}, expires_delta=access_token_expires)
                refresh_token = JWTAuth.create_refresh_token(data={"sub": userLogin}, expires_delta=refresh_token_expires)

                return web.json_response({
                    'message': 'Login successful',
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }, status=200)
            else:
                return web.json_response({'message': 'Invalid credentials'}, status=401)

        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)

    async def refresh_token(self, request):
        data = await request.json()
        refresh_token = data.get('refresh_token')

        try:
            payload = JWTAuth.decode_refresh_token(refresh_token)
            userLogin = payload.get("sub")

            if userLogin is None:
                raise web.HTTPUnauthorized(reason="Invalid refresh token")

            access_token_expires = datetime.timedelta(minutes=JWTAuth.ACCESS_TOKEN_EXPIRE_MINUTES)
            new_access_token = JWTAuth.create_access_token(data={"sub": userLogin}, expires_delta=access_token_expires)

            return web.json_response({
                'access_token': new_access_token
            }, status=200)

        except jwt.ExpiredSignatureError:
            return web.json_response({'message': 'Refresh token expired'}, status=401)
        except jwt.InvalidTokenError:
            return web.json_response({'message': 'Invalid refresh token'}, status=401)