from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import scoped_session
from models import db_session, UserUpdate, User,UserInterest,UserInterestDisplay,UserSettingsDisplay
from pydantic import ValidationError 
from jwtAuth import JWTAuth
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import json

class UserHandler:
    async def update_user(self,request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        user_payload = JWTAuth.decode_access_token(token)
        user_id = user_payload.get('user_id')
        json_data = await request.json()
        try:
            update_data = UserUpdate(**json_data)
            
            # Находим пользователя в базе данных
            user = db_session.query(User).filter(User.id == user_id).one_or_none()
            if not user:
                return web.json_response({'error': 'User not found'}, status=404)

            # Обновляем поля пользователя
            for field, value in update_data.dict(exclude={'interests'}).items():
                setattr(user, field, value) if value is not None else None

            # Синхронизация интересов пользователя
            current_interest_ids = {ui.interest_id for ui in user.user_interests}
            new_interest_ids = set(update_data.interests)

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
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
            
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
                response_data = {
                    'username': user.username,
                    'name': user.name,
                    'surname': user.surname,
                    'img': user.img,
                    'owner': owner
                }

            response_data = json.dumps(response_data, default=str)
            return web.json_response(text=response_data, status=200)  # Используем .dict() для корректной сериализации

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)


# Регистрация маршрута
