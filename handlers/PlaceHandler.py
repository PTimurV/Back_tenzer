from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, Place,PlacePhoto
from models import PlaceCreate, PlaceDisplay,PlacesTravel,PlaceTravelDisplay,PlaceFeedback,PlaceDisplayId2,FeedbackDisplayId,PlaceDisplayId,PhotoDisplayId
from jwtAuth import JWTAuth
from pydantic import ValidationError  # Добавляем импорт
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import joinedload

class PlaceHandler:
    async def create_place(self, request):
        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            reader = await request.multipart()
            data = {}
            photos = []

            # Чтение данных из формы
            while True:
                part = await reader.next()
                if part is None:
                    break
                if part.name in ['title', 'description', 'address', 'type', 'coordinates']:
                    data[part.name] = await part.text()
                elif part.name == 'file':
                    photo_data = {
                        'file': await part.read() # Используйте filename или другой метод для получения имени файла
                    }
                    photos.append(photo_data)

            place_data = PlaceCreate(**data, creator_user_id=user_id)
            new_place = Place(
                creator_user_id=user_id,
                title=place_data.title,
                description=place_data.description,
                address=place_data.address,
                type=place_data.type,
                coordinates=place_data.coordinates,
                status='0'
            )
            db_session.add(new_place)
            db_session.flush()  # Получаем ID для связанных записей

            # Сохранение фотографий
            for photo_data in photos:
                new_photo = PlacePhoto(
                    place_id=new_place.id,
                    file=photo_data['file']  # Бинарные данные фотографи
                )
                db_session.add(new_photo)

            db_session.commit()

            # Воспользуемся relationship для загрузки данных фотографий
            db_session.refresh(new_place)

            # Создаем ответ, используя Pydantic модели для формирования JSON
            response_data = PlaceDisplay.from_orm(new_place)
            return web.json_response(response_data.dict(), status=201)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
        

    async def add_place_to_travel(self, request):
        users_travel_id = int(request.match_info.get('id'))  # Получение ID из URL
        if not users_travel_id:
            return web.json_response({'error': 'Missing users_travel_id'}, status=400)

        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            json_data = await request.json()
            places = json_data.get('places', [])

            # Удаление всех существующих мест для данного путешествия
            db_session.query(PlacesTravel).filter(PlacesTravel.users_travel_id == users_travel_id).delete()
            db_session.commit()  # Применяем изменения после удаления

            new_ids = []
            # Создание и добавление новых мест
            for place_data in places:
                new_place_travel = PlacesTravel(
                    users_travel_id=users_travel_id,
                    place_id=place_data['place_id'],
                    date=place_data['date'],
                    description=place_data['description'],
                    order=place_data['order']
                )
                db_session.add(new_place_travel)
                db_session.flush()  # Получаем ID новых записей
                new_ids.append(new_place_travel.id)

            db_session.commit()  # Сохраняем все изменения

            # Получение только что добавленных мест
            all_new_places = db_session.query(PlacesTravel).filter(PlacesTravel.id.in_(new_ids)).all()

            # Подготовка данных о местах для ответа
            response_data = [PlaceTravelDisplay.from_orm(place).json() for place in all_new_places]

            return web.Response(text='[' + ','.join(response_data) + ']', content_type='application/json', status=201)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
            
    async def get_place_details(self, request):
        place_id = int(request.match_info['id'])
        token = request.headers.get('Authorization', '').split(' ')[-1]

        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            place = db_session.query(Place).filter(Place.id == place_id).options(
                joinedload(Place.photos),
                joinedload(Place.feedbacks).joinedload(PlaceFeedback.user)
            ).first()

            if not place:
                return web.json_response({'message': 'Place not found'}, status=404)

            place_data = PlaceDisplayId(
                id=place.id,
                creator_user_id=place.creator_user_id,
                title=place.title,
                description=place.description,
                address=place.address,
                type=place.type,
                coordinates=place.coordinates,
                status=place.status,
                mean_score=place.mean_score,
                photos=[PhotoDisplayId(file=photo.file) for photo in place.photos if photo.file is not None],  # Проверка, что файл существует
                feedbacks=[
                    FeedbackDisplayId(
                        user_id=feedback.user_id,
                        username=feedback.user.username,
                        score=feedback.score,
                        description=feedback.description
                    ) for feedback in place.feedbacks
                ]
            )

            return web.json_response(place_data.dict(), status=200)

        except ValidationError as e:
            return web.json_response({'error': str(e)}, status=400)
        except ExpiredSignatureError:
            return web.json_response({'error': 'Token has expired'}, status=401)
        except InvalidTokenError:
            return web.json_response({'error': 'Invalid token'}, status=401)
        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)


    async def get_all_places(self,request):
        token = request.headers.get('Authorization', '').split(' ')[-1]

        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            city = request.query.get('city')
            type_param = request.query.get('type')

            if not city or not type_param:
                return web.json_response({'error': 'City and type must be provided'}, status=400)

            query = db_session.query(Place)
            query = query.filter(Place.address.contains(f", {city},"))
            if type_param.lower() != "все":
                query = query.filter(Place.type == type_param)

            places = query.all()

            places_data = [PlaceDisplayId2(
                id=place.id,
                creator_user_id=place.creator_user_id,
                title=place.title,
                description=place.description,
                address=place.address,
                type=place.type,
                coordinates=place.coordinates,
                mean_score=place.mean_score,
                photos=[PhotoDisplayId(file=place.photos[0].file)] if place.photos and place.photos[0].file else [],
            ).dict() for place in places]

            return web.json_response(places_data, status=200)

        except web.HTTPUnauthorized as e:
            return web.json_response({'error': str(e.reason)}, status=401)
        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)
