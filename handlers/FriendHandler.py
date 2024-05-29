from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, UserFriend
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from jwtAuth import JWTAuth
from pydantic import ValidationError 
from models import db_session, User, UserFriend

class FriendHandler:
    async def send_friend_request(self,request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            current_user_id = payload.get("user_id")
            if not current_user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")
            
            friend_id = int(request.match_info['friend_id'])

            # Проверяем, что пользователь, которому отправляется запрос, существует
            if not db_session.query(User).filter(User.id == friend_id).first():
                return web.json_response({'message': 'Friend user not found'}, status=404)
            
            # Создаем запрос на добавление в друзья с начальным статусом 0 (ожидание подтверждения)
            new_friend_request = UserFriend(user_id=current_user_id, friend_id=friend_id, status=0)
            db_session.add(new_friend_request)
            db_session.commit()

            return web.json_response({'message': 'Friend request sent successfully'}, status=201)
        
        except ValidationError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)

    async def respond_to_friend_request(self,request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        json_data = await request.json()
        response = json_data.get('response')  # 'accept' или 'reject'
        friend_request_id = int(request.match_info['request_id'])

        try:
            payload = JWTAuth.decode_access_token(token)
            current_user_id = payload.get("user_id")
            if not current_user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")
            
            friend_request = db_session.query(UserFriend).filter(
                UserFriend.user_id == friend_request_id,
                UserFriend.friend_id == current_user_id
            ).first()
            
            if not friend_request:
                return web.json_response({'message': 'Friend request not found'}, status=404)
            
            if response == 'accept':
                friend_request.status = 1
            elif response == 'reject':
                db_session.delete(friend_request)

            db_session.commit()
            return web.json_response({'message': 'Response recorded'}, status=200)
        
        except ValidationError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)