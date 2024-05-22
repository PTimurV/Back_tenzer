from aiohttp import web
from authHandlers import register, login
from travels import create_travel, get_all_travels, get_travel_by_id

app = web.Application()
app.router.add_post('/register', register)
app.router.add_post('/login', login)
app.router.add_post('/travels', create_travel)
app.router.add_get('/travels', get_all_travels)
app.router.add_get('/travels/{id}', get_travel_by_id)

if __name__ == '__main__':
    web.run_app(app, port=8080)