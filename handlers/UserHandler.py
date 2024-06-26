from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from models import db_session, UserUpdate, User,UserInterest,UserInterestDisplay,UserSettingsDisplay,UserFriend,UserProfileDisplay,UserInfo, FriendInfo,FriendsResponse,UsersResponse
from pydantic import ValidationError 
from jwtAuth import JWTAuth
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import joinedload
import json
import base64

class UserHandler:
    async def update_user(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        user_payload = JWTAuth.decode_access_token(token)
        user_id = user_payload.get('user_id')

        try:
            json_data = await request.json()
            update_data = {}

            # Обработка изображения
            img_data = json_data.get('file')
            if img_data:
                header, encoded = img_data.split(',', 1)
                file = base64.b64decode(encoded)
            else:
                file = None

            # Обработка интересов
            interests_str = json_data.get('interests', '[]')
            try:
                update_data['interests'] = json.loads(interests_str)
            except json.JSONDecodeError:
                update_data['interests'] = []

            # Заполняем update_data остальными полями
            update_data.update({
                'name': json_data.get('name'),
                'surname': json_data.get('surname'),
                'role': json_data.get('role'),
                'gender': json_data.get('gender'),
                'birthday': json_data.get('birthday'),
                'city': json_data.get('city')
            })

            try:
                user_update = UserUpdate(**update_data)  # Создаем Pydantic модель из полученных данных

                # Находим пользователя в базе данных
                user = db_session.query(User).filter(User.id == user_id).one_or_none()
                if not user:
                    return web.json_response({'error': 'User not found'}, status=404)

                # Обновляем поля пользователя
                for field, value in user_update.dict(exclude={'interests'}).items():
                    setattr(user, field, value) if value is not None else None

                # Если есть файл, сохраняем его в базе данных
                if file:
                    user.img = file  # Прямое сохранение двоичных данных

                # Синхронизация интересов пользователя
                if 'interests' in user_update.dict():
                    current_interest_ids = {ui.interest_id for ui in user.user_interests}
                    new_interest_ids = set(user_update.interests)

                    # Удаляем неактуальные интересы
                    for interest_id in current_interest_ids - new_interest_ids:
                        db_session.query(UserInterest).filter_by(user_id=user_id, interest_id=interest_id).delete()

                    # Добавляем новые интересы
                    for interest_id in new_interest_ids - current_interest_ids:
                        db_session.add(UserInterest(user_id=user_id, interest_id=interest_id))

                db_session.commit()
                return web.json_response({'message': 'User updated successfully'}, status=200)

            except ValidationError as e:
                db_session.rollback()
                return web.json_response({'error': str(e)}, status=400)
            except SQLAlchemyError as e:
                db_session.rollback()
                return web.json_response({'error': str(e)}, status=500)
        except json.JSONDecodeError as e:
            return web.json_response({'error': 'Invalid JSON'}, status=400)
        
    async def get_user_settings(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            user = db_session.query(User).filter(User.id == user_id).first()
            if not user:
                return web.json_response({'message': 'User not found'}, status=404)
            
            # Подготовка данных о интересах пользователя
            interests = [
                UserInterestDisplay(interest_id=ui.interest.id, name=ui.interest.name)
                for ui in user.user_interests
            ]

            # Подготовка и отправка основных данных пользователя
            user_data = UserSettingsDisplay.from_orm(user)
            user_data.interests = interests

            # Кодирование изображения в base64, если оно есть

            response_data = json.dumps(user_data.dict(), default=str)
            return web.json_response(text=response_data, status=200)  # Используем .dict() для корректной сериализации

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)
        

    async def get_user_profile(self, request):
        profile_id = int(request.match_info['id'])
        token = request.headers.get('Authorization', '').split(' ')[-1]

        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            user = db_session.query(User).filter(User.id == profile_id).first()
            if not user:
                return web.json_response({'message': 'User not found'}, status=404)

            # Fetch interests
            interests = [
                UserInterestDisplay(interest_id=ui.interest.id, name=ui.interest.name)
                for ui in user.user_interests
            ]

            # Determine if the profile belongs to the logged-in user
            owner = 1 if user_id == profile_id else 0

            # Prepare the response data based on ownership
            if owner:
                user_data = UserSettingsDisplay.from_orm(user)
                user_data.interests = interests
                response_data = user_data.dict()
                response_data['owner'] = owner
            else:
                response_data = UserProfileDisplay(
                    username=user.username,
                    name=user.name,
                    surname=user.surname,
                    img=user.img,
                    owner=owner,
                    interests=interests
                ).dict()

            response_data = json.dumps(response_data, default=str)
            return web.json_response(text=response_data, status=200)

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)

    async def get_friends(self, request):
        try:
            user_id = int(request.match_info['user_id'])
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            from sqlalchemy import or_

            friends = db_session.query(UserFriend).filter(
                or_(
                    UserFriend.user_id == user_id,
                    UserFriend.friend_id == user_id
                )
            ).options(
                joinedload(UserFriend.user),
                joinedload(UserFriend.friend)
            ).all()

            response_data = {'pending_sent': [], 'pending_received': [], 'friends':[]}
            for friendship in friends:
                if friendship.status == 0:
                    if friendship.user_id == user_id:
                        # Текущий пользователь является инициатором
                        friend_data = FriendInfo(
                            friend_id=friendship.friend_id,
                            name=friendship.friend.name,
                            surname=friendship.friend.surname,
                            img=friendship.friend.img,
                            username=friendship.friend.username,
                            status=friendship.status
                        )
                        response_data['pending_sent'].append(friend_data)
                    else:
                        # Текущий пользователь является получателем
                        friend_data = FriendInfo(
                            friend_id=friendship.user_id,
                            name=friendship.user.name,
                            surname=friendship.user.surname,
                            img=friendship.user.img,
                            username=friendship.user.username,
                            status=friendship.status
                        )
                        response_data['pending_received'].append(friend_data)
                else: 
                    if friendship.user_id == user_id:
                        # Текущий пользователь является инициатором
                        friend_data = FriendInfo(
                            friend_id=friendship.friend_id,
                            name=friendship.friend.name,
                            surname=friendship.friend.surname,
                            img=friendship.friend.img,
                            username=friendship.friend.username,
                            status=friendship.status
                        )
                        response_data['friends'].append(friend_data)
                    else:
                        # Текущий пользователь является получателем
                        friend_data = FriendInfo(
                            friend_id=friendship.user_id,
                            name=friendship.user.name,
                            surname=friendship.user.surname,
                            img=friendship.user.img,
                            username=friendship.user.username,
                            status=friendship.status
                        )
                        response_data['friends'].append(friend_data)

            # Преобразуем словарь в модель Pydantic для валидации и сериализации
            response_model = FriendsResponse(**response_data)
            return web.json_response(response_model.dict(), status=200)

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)

        
    async def get_all_users(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            # Получение списка друзей и заявок
            friends_query = db_session.query(UserFriend).filter(
                (UserFriend.user_id == user_id) | (UserFriend.friend_id == user_id)
            ).all()

            # Извлечение идентификаторов друзей и заявок
            friend_ids = {f.friend_id if f.user_id == user_id else f.user_id for f in friends_query}

            # Добавление своего ID в список исключений
            friend_ids.add(user_id)

            # Запрос для получения всех пользователей, кроме себя и друзей
            users = db_session.query(User).filter(~User.id.in_(friend_ids)).all()

            # Формирование ответа
            response_data = [
                UserInfo(
                    id=user.id,
                    img=user.img,
                    name=user.name,
                    surname=user.surname,
                    username=user.username
                ) for user in users
            ]

            # Преобразуем список моделей Pydantic в словарь
            response_model = UsersResponse(users=response_data)
            return web.json_response(response_model.dict(), status=200)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)
        


    

# Регистрация маршрута
