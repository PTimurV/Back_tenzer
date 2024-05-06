from aiohttp import web
import psycopg
from config import host, user, password, db_name

async def register(request):
    data = await request.json()
    userEmail = data.get('email')
    userLogin = data.get('login')
    userPassword = data.get('password')

    try:
        connection = psycopg.connect(
            host=host,
            user=user,
            password=password,
            dbname=db_name,
            port=5432
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO users1 (email, login, password) VALUES (%s, %s, %s);",
                (userEmail,userLogin, userPassword)
            )
            connection.commit()

        return web.json_response({'message': 'User registered successfully'}, status=201)

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
        connection = psycopg.connect(
            host=host,
            user=user,
            password=password,
            dbname=db_name,
            port=5432
        )

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM users1 WHERE login = %s AND password = %s;",
                (userLogin, userPassword)
            )
            user_data = cursor.fetchone()

        if user_data:
            return web.json_response({'message': 'Login successful'}, status=200)
        else:
            return web.json_response({'message': 'Invalid credentials'}, status=401)

    except Exception as ex:
        return web.json_response({'error': str(ex)}, status=500)

    finally:
        if connection:
            connection.close()

app = web.Application()
app.router.add_post('/register', register)
app.router.add_post('/login', login)

if __name__ == '__main__':
    web.run_app(app, port=8080)


