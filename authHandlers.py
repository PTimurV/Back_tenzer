from aiohttp import web
from db import get_connection
from jwtAuth import create_refresh_token,create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES,REFRESH_TOKEN_EXPIRE_DAYS,JWT_SECRET,JWT_ALGORITHM
import jwt
import datetime
from config import jwt_secret, jwt_algorithm

async def register(request):
    data = await request.json()
    userEmail = data.get('email')
    userLogin = data.get('login')
    userPassword = data.get('password')

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users1 (email, login, password) VALUES (%s, %s, %s);",
                (userEmail, userLogin, userPassword)
            )
            connection.commit()

        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = create_access_token(data={"sub": userLogin}, expires_delta=access_token_expires)
        refresh_token = create_refresh_token(data={"sub": userLogin}, expires_delta=refresh_token_expires)

        return web.json_response({
            'message': 'User registered successfully',
            'access_token': access_token,
            'refresh_token': refresh_token
        }, status=201)

    except Exception as ex:
        return web.json_response({'error': str(ex)}, status=500)

    finally:
        if connection:
            connection.close()



async def login(request):
    data = await request.json()
    userLogin = data.get('login')
    userPassword = data.get('password')

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users1 WHERE login = %s AND password = %s;",
                (userLogin, userPassword)
            )
            user_data = cursor.fetchone()

        if user_data:
            access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = datetime.timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
            
            access_token = create_access_token(data={"sub": userLogin}, expires_delta=access_token_expires)
            refresh_token = create_refresh_token(data={"sub": userLogin}, expires_delta=refresh_token_expires)

            return web.json_response({
                'message': 'Login successful',
                'access_token': access_token,
                'refresh_token': refresh_token
            }, status=200)
        else:
            return web.json_response({'message': 'Invalid credentials'}, status=401)

    except Exception as ex:
        return web.json_response({'error': str(ex)}, status=500)

    finally:
        if connection:
            connection.close()


async def refresh_token(request):
    data = await request.json()
    refresh_token = data.get('refresh_token')

    try:
        payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        userLogin = payload.get("sub")

        if userLogin is None:
            raise web.HTTPUnauthorized(reason="Invalid refresh token")

        access_token_expires = datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(data={"sub": userLogin}, expires_delta=access_token_expires)

        return web.json_response({
            'access_token': new_access_token
        }, status=200)

    except jwt.ExpiredSignatureError:
        return web.json_response({'message': 'Refresh token expired'}, status=401)
    except jwt.InvalidTokenError:
        return web.json_response({'message': 'Invalid refresh token'}, status=401)