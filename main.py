from aiohttp import web
import aiohttp_cors
from authHandlers import AuthHandler
from travels import TravelHandler
from handlers.PlaceHandler import PlaceHandler
from handlers.UserHandler import UserHandler
from handlers.FriendHandler import FriendHandler
from handlers.FeedbackHandler import FeedbackHandler

def create_app():
    app = web.Application()
    
    # Handlers initialization
    auth_handler = AuthHandler()
    travel_handler = TravelHandler()
    place_handler = PlaceHandler()
    user_handler = UserHandler()
    friend_handler = FriendHandler()
    feedback_handler = FeedbackHandler()

    # Routes
    app.router.add_post('/register', auth_handler.register)
    app.router.add_post('/login', auth_handler.login)
    app.router.add_post('/refresh_token', auth_handler.refresh_token)
    app.router.add_post('/logout', auth_handler.logout)

    app.router.add_post('/travels', travel_handler.create_user_travel)
    app.router.add_get('/user_travels', travel_handler.get_user_travels)
    app.router.add_post('/user_travels/{id}/add_member', travel_handler.add_travel_member)
    app.router.add_get('/user_travels/{id}', travel_handler.get_user_travel_details)
    app.router.add_get('/travels/{id}', travel_handler.get_travel_details)
    app.router.add_post('/user_travels/{id}/passed', travel_handler.update_travel_status_and_score)
    app.router.add_post('/travels/{id}/copy', travel_handler.copy_travel)

    app.router.add_post('/places', place_handler.create_place)
    app.router.add_post('/add_place_to_travel/{id}', place_handler.add_place_to_travel)
    app.router.add_get('/place/{id}', place_handler.get_place_details)

    app.router.add_put('/profile/settings', user_handler.update_user)
    app.router.add_get('/profile/settings', user_handler.get_user_settings)
    app.router.add_get('/profile/{id}', user_handler.get_user_profile)
    app.router.add_get('/friends', user_handler.get_friends)
    app.router.add_post('/friends/send/{friend_id}', friend_handler.send_friend_request)
    app.router.add_post('/friends/respond/{request_id}', friend_handler.respond_to_friend_request)
    app.router.add_post('/places/{place_id}/feedback', feedback_handler.add_feedback)

    app.router.add_get('/', lambda request: web.Response(text="Hello, world"))

    # Setup CORS
    cors = aiohttp_cors.setup(app)
    for route in list(app.router.routes()):
        cors.add(route, {
            "*": aiohttp_cors.ResourceOptions(
                allow_credentials=True, expose_headers="*", allow_headers="*", allow_methods="*")
        })

    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, port=8080)