from aiohttp import web
from authHandlers import AuthHandler
from travels import TravelHandler
from handlers.PlaceHandler import PlaceHandler
from handlers.UserHandler import UserHandler

app = web.Application()

auth_handler = AuthHandler()
travel_handler = TravelHandler()
place_handler = PlaceHandler()
user_handler = UserHandler()

app.router.add_post('/register', auth_handler.register)
app.router.add_post('/login', auth_handler.login)
app.router.add_post('/refresh_token', auth_handler.refresh_token)
app.router.add_post('/logout', auth_handler.logout)


app.router.add_post('/travels', travel_handler.create_user_travel)
app.router.add_get('/user_travels', travel_handler.get_user_travels)


app.router.add_post('/places', place_handler.create_place)
app.router.add_post('/add_place_to_travel', place_handler.add_place_to_travel)

app.router.add_put('/profile/settings', user_handler.update_user)
app.router.add_get('/profile/settings', user_handler.get_user_settings)
app.router.add_get('/profile/{id}', user_handler.get_user_profile)




async def hello(request):
    return web.Response(text="Hello, world")
app.router.add_get('/', hello)

if __name__ == '__main__':
    web.run_app(app, port=8080)