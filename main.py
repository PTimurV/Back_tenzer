from aiohttp import web
from authHandlers import AuthHandler
from travels import TravelHandler

app = web.Application()

auth_handler = AuthHandler()
travel_handler = TravelHandler()

app.router.add_post('/register', auth_handler.register)
app.router.add_post('/login', auth_handler.login)
app.router.add_post('/refresh_token', auth_handler.refresh_token)

app.router.add_post('/travels', travel_handler.create_travel)
app.router.add_get('/travels', travel_handler.get_all_travels)
app.router.add_get('/travels/{id}', travel_handler.get_travel_by_id)

if __name__ == '__main__':
    web.run_app(app, port=8080)