from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, Travel, Place,UsersTravel, PlaceInfo,PlacesTravel,TravelInfoDisplay,PhotoDisplay,AddMemberRequest,UsersTravelMember,User,PhotoDisplay2,BestTravel,UserFriend,TravelDetailDisplay,MemberInfo,UserTravelInfo,TravelDetailDisplayExtended,PlaceTravelDisplay
from jwtAuth import JWTAuth
from pydantic import ValidationError  # Добавляем импорт
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import joinedload
import json
import base64
from datetime import datetime
class TravelHandler:
    async def create_user_travel(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
    
    # Декодируем токен для получения payload
        user_payload = JWTAuth.decode_access_token(token)
        owner_user_id = user_payload.get('user_id')

        if not owner_user_id:
            return web.json_response({'error': 'Unauthorized access'}, status=401)

        try:
            # Создаем новый объект UsersTravel с базовыми значениями
            new_users_travel = UsersTravel(
                owner_user_id=owner_user_id,
                title="Новый маршрут",
                description="",  # Пустое описание
                img=None,  # Без изображения
                status='creating'  # Статус по умолчанию
            )
            db_session.add(new_users_travel)
            db_session.commit()

            return web.json_response({
                'id': new_users_travel.id,
            }, status=201)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)


    async def update_user_travel(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        user_payload = JWTAuth.decode_access_token(token)
        owner_user_id = user_payload.get('user_id')

        if not owner_user_id:
            return web.json_response({'error': 'Unauthorized access'}, status=401)

        try:
            travel_id = int(request.match_info['travel_id'])  # ID путешествия из URL
            json_data = await request.json()

            travel = db_session.query(UsersTravel).filter(UsersTravel.id == travel_id).first()
            if not travel:
                return web.json_response({'error': 'Travel not found'}, status=404)

            # Логи для диагностики
            print("Received JSON data:", json_data)

            # Обновление данных о путешествии
            travel.title = json_data.get('title', travel.title)
            travel.description = json_data.get('description', travel.description)
            travel.start_date = json_data.get('start_date', travel.start_date)
            travel.end_date = json_data.get('end_date', travel.end_date)
            travel.status = json_data.get('status', travel.status)
            
            # Обработка изображения
            img_data = json_data.get('img')
            if img_data:
                header, encoded = img_data.split(',', 1)
                travel.img = base64.b64decode(encoded)

            # Обновление участников
            member_data = json_data.get('members', [])
            if member_data:
                # Удаляем существующих участников
                db_session.query(UsersTravelMember).filter(UsersTravelMember.users_travel_id == travel_id).delete()
                # Добавляем новых участников
                for member in member_data:
                    member_id = member.get('user_id')
                    if db_session.query(User).filter(User.id == member_id).scalar():
                        new_member = UsersTravelMember(
                            users_travel_id=travel.id,
                            user_id=member_id
                        )
                        db_session.add(new_member)

            # Обновление мест
            places = json_data.get('places', [])
            if places:
                # Удаление всех существующих мест для данного путешествия
                db_session.query(PlacesTravel).filter(PlacesTravel.users_travel_id == travel_id).delete()
                db_session.commit()  # Применяем изменения после удаления

                new_ids = []
                # Создание и добавление новых мест
                for place_data in places:
                    new_place_travel = PlacesTravel(
                        users_travel_id=travel_id,
                        place_id=place_data['place_id'],
                        date=place_data.get('date'),
                        description=place_data.get('description'),
                        order=place_data.get('order')
                    )
                    db_session.add(new_place_travel)
                    db_session.flush()  # Получаем ID новых записей
                    new_ids.append(new_place_travel.id)

                # Получение только что добавленных мест
                all_new_places = db_session.query(PlacesTravel).filter(PlacesTravel.id.in_(new_ids)).all()
                # Подготовка данных о местах для ответа
                response_places = [PlaceTravelDisplay.from_orm(place).dict() for place in all_new_places]

            # Коммит изменений
            db_session.commit()

            response_data = {
                'id': travel.id,
                'message': 'Travel updated successfully',
                'places': response_places if places else []
            }

            return web.json_response(response_data, status=200)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=500)



    async def get_user_travels(self,request):
        try:
            user_id = int(request.match_info['user_id'])  # ID путешествия из URL
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing user_id")

            travel_status = request.query.get('status')
            if travel_status not in ['creating', 'passed', 'now']:
                return web.json_response({'error': 'Invalid status provided'}, status=400)

            travels = db_session.query(UsersTravel).filter(
                UsersTravel.owner_user_id == user_id,
                UsersTravel.status == travel_status
            ).options(joinedload(UsersTravel.places).joinedload(PlacesTravel.place).joinedload(Place.photos)).all()

            response_data = [TravelInfoDisplay(
                id=travel.id,
                owner_user_id = travel.owner_user_id,
                title=travel.title,
                description=travel.description,
                img=travel.img,
                status=travel.status,
                start_date=travel.start_date,
                end_date=travel.end_date,
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

            places = [
                PlaceInfo(
                    place_id=place_travel.place.id,
                    title=place_travel.place.title,
                    description=place_travel.place.description,
                    address=place_travel.place.address,
                    type=place_travel.place.type,
                    coordinates=place_travel.place.coordinates,
                    travel_comment=place_travel.description,
                    travel_date=place_travel.date.isoformat() if place_travel.date else None,
                    order=place_travel.order,
                    photos=[PhotoDisplay.from_orm(photo) for photo in place_travel.place.photos if photo.file is not None]
                ) for place_travel in user_travel.places
            ]

            members = [
                MemberInfo(
                    user_id=member.user_id,
                    username=member.user.username,
                    img=member.user.img
                ) for member in user_travel.members
            ]

            response_data = TravelDetailDisplay(
                places=places,
                id=user_travel.id,
                owner_user_id=user_travel.owner_user_id,
                title=user_travel.title,
                description=user_travel.description,
                score=user_travel.score,
                img=user_travel.img,
                status=user_travel.status,
                
                members=members
            ).dict()

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
            travel_id_response = 0

            # Проверяем, существует ли связанный Travel
            if users_travel.travel_id:
                travel = db_session.query(Travel).filter(Travel.id == users_travel.travel_id).one()
                # Обновляем среднюю оценку и количество пользователей
                old_mean_score = travel.mean_score
                old_count_users = travel.count_users
                new_mean_score = ((old_mean_score * old_count_users) + new_score) / (old_count_users + 1)
                travel.mean_score = new_mean_score
                travel.count_users += 1
                travel_id_response = travel.id
            else:
                # Создаем новую запись в Travel
                new_travel = Travel(
                    user_id=user_id,
                    user_travel_id=travel_id,
                    mean_score=new_score,
                    status=0,
                    count_users=1
                )
                db_session.add(new_travel)
                db_session.flush()  # Получаем ID нового Travel
                users_travel.travel_id = new_travel.id
                travel_id_response = travel.id

            db_session.commit()
            return web.json_response({'id':travel_id_response,'message': 'Travel updated successfully'}, status=200)

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

            places = [
                PlaceInfo(
                    id=place_travel.place.id,
                    title=place_travel.place.title,
                    description=place_travel.place.description,
                    address=place_travel.place.address,
                    type=place_travel.place.type,
                    coordinates=place_travel.place.coordinates,
                    travel_comment=place_travel.description,
                    travel_date=None,
                    order=place_travel.order,
                    photos=[PhotoDisplay.from_orm(photo) for photo in place_travel.place.photos if photo.file is not None]
                ).dict() for place_travel in travel.user_travel.places
            ]

            members = [
                MemberInfo(
                    user_id=member.user_id,
                    username=member.user.username,
                    img=member.user.img
                ).dict() for member in travel.user_travel.members
            ]

            user_travel_info = UserTravelInfo(
                id=travel.user_travel.id,
                owner_user_id=travel.user_travel.owner_user_id,
                title=travel.user_travel.title,
                description=travel.user_travel.description,
                score=travel.user_travel.score,
                img=travel.user_travel.img,
                status=travel.user_travel.status,
                places=places,
                members=members
            )

            response_data = TravelDetailDisplayExtended(
                id=travel.id,
                mean_score=travel.mean_score,
                count_users=travel.count_users,
                user_travel=user_travel_info
            ).dict()

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


            response_data = {
                'users_travel_id': new_travel.id
            }

            return web.json_response(response_data, status=201)

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
        

    async def hint_card(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            best_travels = db_session.query(BestTravel).options(
                joinedload(BestTravel.travel).joinedload(Travel.user_travel)
            ).all()

            response_data = [
                {
                    'id': best_travel.travel.id,
                    'title': best_travel.travel.user_travel.title,
                    'description': best_travel.travel.user_travel.description,
                    'mean_score': best_travel.travel.mean_score,
                    'img': base64.b64encode(best_travel.travel.user_travel.img).decode('utf-8') if best_travel.travel.user_travel.img else None,
                    'count_users': best_travel.travel.count_users
                } for best_travel in best_travels
            ]

            # Запрос для получения ближайших маршрутов пользователя
            upcoming_travels = db_session.query(UsersTravel).filter(
                UsersTravel.owner_user_id == user_id,
                UsersTravel.status == 'creating',
            ).order_by(
                UsersTravel.start_date.asc()
            ).limit(5).all()

            upcoming_data = [
                {
                    'id': travel.id,
                    'title': travel.title,
                    'description': travel.description,
                    'mean_score': travel.score,
                    'img': base64.b64encode(travel.img).decode('utf-8') if travel.img else None,
                    'start_date': travel.start_date.isoformat() if travel.start_date else None,
                    'end_date': travel.end_date.isoformat() if travel.end_date else None
                } for travel in upcoming_travels
            ]

            # Получение списка друзей пользователя
            friends = db_session.query(UserFriend).filter(
                (UserFriend.user_id == user_id) | (UserFriend.friend_id == user_id),
                UserFriend.status == 1
            ).all()

            friend_ids = {f.friend_id if f.user_id == user_id else f.user_id for f in friends}

            # Получение маршрутов, где друзья являются создателями
            friends_travels_owner = db_session.query(UsersTravel, User).select_from(UsersTravel).join(User, UsersTravel.owner_user_id == User.id).filter(
                UsersTravel.owner_user_id.in_(friend_ids),
                UsersTravel.start_date >= datetime.today()
            ).all()

            # Получение маршрутов, где друзья являются участниками
            friends_travels_member = db_session.query(UsersTravel, User).select_from(UsersTravel).join(UsersTravelMember, UsersTravel.id == UsersTravelMember.users_travel_id).join(User, UsersTravelMember.user_id == User.id).filter(
                UsersTravelMember.user_id.in_(friend_ids),
                UsersTravel.start_date >= datetime.today()
            ).all()

            # Объединение и сортировка маршрутов друзей
            all_friends_travels = friends_travels_owner + friends_travels_member
            all_friends_travels = sorted(all_friends_travels, key=lambda x: x[0].start_date)[:5]

            friends_travel_data = [
                {
                    'id': travel.id,
                    'title': travel.title,
                    'description': travel.description,
                    'mean_score': travel.score,
                    'img': base64.b64encode(travel.img).decode('utf-8') if travel.img else None,
                    'start_date': travel.start_date.isoformat() if travel.start_date else None,
                    'end_date': travel.end_date.isoformat() if travel.end_date else None,
                    'friend_id': user.id,
                    'friend_username': user.username
                } for travel, user in all_friends_travels
            ]

            return web.json_response({'best_travels': response_data, 'upcoming_travels': upcoming_data, 'friends_travels': friends_travel_data}, status=200)
        
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        except Exception as e:
            return web.json_response({'error': str(e)}, status=400)