from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, Travel, Place,UsersTravel, PlaceInfo,PlacesTravel,TravelInfoDisplay,PhotoDisplay,AddMemberRequest,UsersTravelMember,User,UsersTravelDisplay2,PhotoDisplay2
from jwtAuth import JWTAuth
from pydantic import ValidationError  # Добавляем импорт
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import joinedload
import json
import base64
class TravelHandler:
    async def create_user_travel(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        user_payload = JWTAuth.decode_access_token(token)
        owner_user_id = user_payload.get('user_id')

        if not owner_user_id:
            return web.json_response({'error': 'Unauthorized access'}, status=401)

        reader = await request.multipart()
        title = None
        description = None
        img = None

        # Чтение данных из формы
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.name == 'title':
                title = await part.text()
            elif part.name == 'description':
                description = await part.text()
            elif part.name == 'img':
                img = await part.read()  # Читаем бинарные данные изображения

        if not title or not description:
            return web.json_response({'error': 'Missing title or description'}, status=400)

        try:
            # Создаем новый объект UsersTravel
            new_users_travel = UsersTravel(
                owner_user_id=owner_user_id,
                title=title,
                description=description,
                img=img,
                status='creating'  # Статус по умолчанию
            )
            db_session.add(new_users_travel)
            db_session.commit()

            # Кодируем изображение в base64 для ответа, если оно есть
            img_base64 = f"data:image/png;base64,{base64.b64encode(img).decode('utf-8')}" if img else None

            return web.json_response({
                'id': new_users_travel.id,
                'title': title,
                'description': description,
                'status': new_users_travel.status,
                'img': img_base64
            }, status=201)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)

    async def get_user_travels(self,request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            travel_status = request.query.get('status')
            if travel_status not in ['creating', 'passed']:
                return web.json_response({'error': 'Invalid status provided'}, status=400)

            travels = db_session.query(UsersTravel).filter(
                UsersTravel.owner_user_id == user_id,
                UsersTravel.status == travel_status
            ).options(joinedload(UsersTravel.places).joinedload(PlacesTravel.place).joinedload(Place.photos)).all()

            response_data = [TravelInfoDisplay(
                id=travel.id,
                title=travel.title,
                description=travel.description,
                img=base64.b64encode(travel.img).decode('utf-8') if travel.img else None,
                status=travel.status,
                places=[PlaceInfo(
                    id=place.place.id,
                    title=place.place.title,
                    description=place.place.description,
                    address=place.place.address,
                    type=place.place.type,
                    coordinates=place.place.coordinates,
                    travel_comment=place.description,
                    travel_date=place.date,
                    order=place.order,
                    photos=[
            PhotoDisplay.from_orm(photo) for photo in place.place.photos if photo.file is not None
        ],
                ) for place in travel.places]
            ).dict() for travel in travels]

            response_data = json.dumps(response_data, default=str)
            return web.json_response(text=response_data, status=200) 


        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        



    async def get_user_travel_details(self, request):
        travel_id = int(request.match_info['id'])
        token = request.headers.get('Authorization', '').split(' ')[-1]

        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            user_travel = db_session.query(UsersTravel).filter(UsersTravel.id == travel_id).options(
                joinedload(UsersTravel.places).joinedload(PlacesTravel.place).subqueryload(Place.photos),
                joinedload(UsersTravel.members).joinedload(UsersTravelMember.user)
            ).one_or_none()

            if not user_travel:
                return web.json_response({'message': 'Travel not found'}, status=404)

            # Serialize places
            places = [
                {
                    'id': place_travel.place.id,
                    'title': place_travel.place.title,
                    'description': place_travel.place.description,
                    'address': place_travel.place.address,
                    'type': place_travel.place.type,
                    'coordinates': place_travel.place.coordinates,
                    'status': place_travel.place.status,
                    'mean_score': place_travel.place.mean_score,
                    'photos': [PhotoDisplay2.from_orm(photo).dict() for photo in place_travel.place.photos if photo.file is not None]
                } for place_travel in user_travel.places
            ]

            # Serialize members
            members = [
                {
                    'user_id': member.user_id,
                    'username': member.user.username,
                    'img': base64.b64encode(member.user.img).decode('utf-8') if member.user.img else None
                } for member in user_travel.members
            ]

            # Prepare the complete response data
            response_data = {
                'id': user_travel.id,
                'owner_user_id': user_travel.owner_user_id,
                'title': user_travel.title,
                'description': user_travel.description,
                'score': user_travel.score,
                'img': base64.b64encode(user_travel.img).decode('utf-8') if user_travel.img else None,
                'status': user_travel.status,
                'places': places,
                'members': members
            }
            return web.json_response(response_data, status=200)

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)

    async def add_travel_member(self,request):
        travel_id = int(request.match_info['id'])  # ID путешествия из URL
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            # Декодируем токен для проверки авторизации и получения ID пользователя
            payload = JWTAuth.decode_access_token(token)
            authorized_user_id = payload.get("user_id")
            if not authorized_user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            # Парсим данные запроса
            request_data = await request.json()
            data = AddMemberRequest(**request_data)
            new_member = UsersTravelMember(
                users_travel_id=travel_id,
                user_id=data.user_id
            )

            # Проверяем, существует ли такой пользователь
            if not db_session.query(User).filter(User.id == data.user_id).scalar():
                return web.json_response({'message': 'User not found'}, status=404)

            # Добавляем запись в базу данных
            db_session.add(new_member)
            db_session.commit()

            return web.json_response({'message': 'Member added successfully'}, status=201)

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        
    async def update_travel_status_and_score(self, request):
        travel_id = int(request.match_info['id'])
        token = request.headers.get('Authorization', '').split(' ')[-1]

        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            # Получаем данные из запроса
            data = await request.json()
            new_score = data.get("score")

            # Получаем UsersTravel по ID
            users_travel = db_session.query(UsersTravel).filter(UsersTravel.id == travel_id, UsersTravel.owner_user_id == user_id).one_or_none()
            if not users_travel:
                return web.json_response({'message': 'Travel not found or access denied'}, status=404)

            users_travel.status = 'passed'
            users_travel.score = new_score

            # Проверяем, существует ли связанный Travel
            if users_travel.travel_id:
                travel = db_session.query(Travel).filter(Travel.id == users_travel.travel_id).one()
                # Обновляем среднюю оценку и количество пользователей
                old_mean_score = travel.mean_score
                old_count_users = travel.count_users
                new_mean_score = ((old_mean_score * old_count_users) + new_score) / (old_count_users + 1)
                travel.mean_score = new_mean_score
                travel.count_users += 1
            else:
                # Создаем новую запись в Travel
                new_travel = Travel(
                    user_id=user_id,
                    user_travel_id=travel_id,
                    mean_score=new_score,
                    status='passed',
                    count_users=1
                )
                db_session.add(new_travel)
                db_session.flush()  # Получаем ID нового Travel
                users_travel.travel_id = new_travel.id

            db_session.commit()
            return web.json_response({'message': 'Travel updated successfully'}, status=200)

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
        
    async def get_travel_details(self, request):
        travel_id = int(request.match_info['id'])

        try:
            travel = db_session.query(Travel).filter(Travel.id == travel_id).options(
                joinedload(Travel.user_travel).joinedload(UsersTravel.places).joinedload(PlacesTravel.place).subqueryload(Place.photos),
                joinedload(Travel.user_travel).joinedload(UsersTravel.members).joinedload(UsersTravelMember.user)
            ).one_or_none()

            if not travel:
                return web.json_response({'message': 'Travel not found'}, status=404)

            # Serialize places with photo processing
            places = [
                {
                    'id': place_travel.place.id,
                    'title': place_travel.place.title,
                    'description': place_travel.place.description,
                    'address': place_travel.place.address,
                    'type': place_travel.place.type,
                    'coordinates': place_travel.place.coordinates,
                    'status': place_travel.place.status,
                    'mean_score': place_travel.place.mean_score,
                    'photos': [
                        PhotoDisplay2.from_orm(photo).dict() for photo in place_travel.place.photos if photo.file is not None
                    ]
                } for place_travel in travel.user_travel.places
            ]

            # Serialize members
            members = [
                {
                    'user_id': member.user_id,
                    'username': member.user.username,
                    'img': base64.b64encode(member.user.img).decode('utf-8') if member.user.img else None
                } for member in travel.user_travel.members
            ]

            # Prepare the complete response data
            response_data = {
                'id': travel.id,
                'mean_score': travel.mean_score,
                'count_users': travel.count_users,
                'user_travel': {
                    'id': travel.user_travel.id,
                    'owner_user_id': travel.user_travel.owner_user_id,
                    'title': travel.user_travel.title,
                    'description': travel.user_travel.description,
                    'score': travel.user_travel.score,
                    'img': base64.b64encode(travel.user_travel.img).decode('utf-8') if travel.user_travel.img else None,
                    'status': travel.user_travel.status,
                    'places': places,
                    'members': members
                }
            }

            return web.json_response(response_data, status=200)

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        

    async def copy_travel(self, request):
        travel_id = int(request.match_info['id'])
        token = request.headers.get('Authorization', '').split(' ')[-1]

        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            # Получаем travel, чтобы найти связанный user_travel_id
            travel = db_session.query(Travel).filter(Travel.id == travel_id).one_or_none()
            if not travel:
                return web.json_response({'message': 'Travel not found'}, status=404)

            user_travel_id = travel.user_travel_id

            # Загружаем связанный UsersTravel
            original_travel = db_session.query(UsersTravel).filter(
                UsersTravel.id == user_travel_id
            ).options(
                joinedload(UsersTravel.places)
            ).one_or_none()

            if not original_travel:
                return web.json_response({'message': 'User Travel not found'}, status=404)

            # Создаем новый маршрут путешествия для пользователя
            new_travel = UsersTravel(
                owner_user_id=user_id,
                title=original_travel.title,
                description=original_travel.description,
                score=0,  # Начальный балл
                img=original_travel.img,
                status='creating',  # Статус на стадии создания
                travel_id=travel_id  # Ссылка на исходный тревел
            )
            db_session.add(new_travel)
            db_session.flush()

            # Копируем места из исходного путешествия
            for place in original_travel.places:
                new_place_travel = PlacesTravel(
                    users_travel_id=new_travel.id,
                    place_id=place.place_id,
                    date=place.date,
                    description=place.description,
                    order=place.order
                )
                db_session.add(new_place_travel)

            db_session.commit()

            return web.json_response({'message': 'Travel copied successfully'}, status=201)

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