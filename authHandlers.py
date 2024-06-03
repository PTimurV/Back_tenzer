from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, User
from jwtAuth import JWTAuth
import datetime
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import bcrypt

class AuthHandler:
    async def register(self, request):
        data = await request.json()
        userEmail = data.get('email')
        userName = data.get('username')
        userPassword = data.get('password').encode('utf-8')
        hashed_password = bcrypt.hashpw(userPassword, bcrypt.gensalt()).decode('utf-8')

        try:
            # Создание нового пользователя
            new_user = User(email=userEmail, username=userName, password=hashed_password)
            db_session.add(new_user)
            db_session.commit()

            # Создание токенов доступа и обновления
            access_token_expires = datetime.timedelta(minutes=JWTAuth.ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = datetime.timedelta(days=JWTAuth.REFRESH_TOKEN_EXPIRE_DAYS)
            
            access_token = JWTAuth.create_access_token(data={"sub": userName, "user_id": new_user.id}, expires_delta=access_token_expires)
            refresh_token = JWTAuth.create_refresh_token(data={"sub": userName, "user_id": new_user.id}, expires_delta=refresh_token_expires)

            response =  web.json_response({
                "id": new_user.id,
                'message': 'User registered successfully',
                'access_token': access_token,
            }, status=201)

            response.set_cookie('refreshToken', refresh_token, httponly=True, secure=True, samesite='Strict', path='/refresh_token')

            return response

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)

    async def login(self, request):
        data = await request.json()
        userName = data.get('username')
        userPassword = data.get('password').encode('utf-8')

        try:
            user = db_session.query(User).filter(User.username == userName).first()
            if user and bcrypt.checkpw(userPassword, user.password.encode('utf-8')):  # Проверка хеша пароля
                access_token_expires = datetime.timedelta(minutes=JWTAuth.ACCESS_TOKEN_EXPIRE_MINUTES)
                refresh_token_expires = datetime.timedelta(days=JWTAuth.REFRESH_TOKEN_EXPIRE_DAYS)
                
                access_token = JWTAuth.create_access_token(data={"sub": userName, "user_id": user.id}, expires_delta=access_token_expires)
                refresh_token = JWTAuth.create_refresh_token(data={"sub": userName, "user_id": user.id}, expires_delta=refresh_token_expires)

                response = web.json_response({
                    "id": user.id,
                    'message': 'Login successful',
                    'access_token': access_token,
                }, status=200)
                response.set_cookie('refreshToken', refresh_token, httponly=True, secure=True, samesite='Strict', path='/refresh_token')
                return response
            else:
                return web.json_response({'message': 'Invalid credentials'}, status=401)

        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)

    async def refresh_token(self, request):
        refresh_token = request.cookies.get('refreshToken')

        if not refresh_token:
            raise web.HTTPUnauthorized(reason="Refresh token not found")

        try:
            payload = JWTAuth.decode_refresh_token(refresh_token)
            userName = payload.get("sub")
            userId = payload.get("user_id")

            if userName is None or userId is None:
                raise web.HTTPUnauthorized(reason="Invalid refresh token")

            access_token_expires = datetime.timedelta(minutes=JWTAuth.ACCESS_TOKEN_EXPIRE_MINUTES)
            new_access_token = JWTAuth.create_access_token(
                data={"sub": userName, "user_id": userId},
                expires_delta=access_token_expires
            )

            return web.json_response({
                "id": userId,                
                'access_token': new_access_token
            }, status=200)

        except ExpiredSignatureError:
            return web.json_response({'message': 'Refresh token expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'message': 'Invalid refresh token'}, status=401)
        
    async def logout(self, request):
        # Установить cookie с токеном обновления так, чтобы оно истекло
        response = web.Response(text="Logged out successfully.")
        response.del_cookie('refreshToken', path='/refresh_token')
        return response