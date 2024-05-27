from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, Place,PlacePhoto
from models import PlaceCreate, PlaceDisplay,PhotoBase,PhotoDisplay,PlaceTravelCreate,PlacesTravel,PlaceTravelDisplay
from jwtAuth import JWTAuth
from pydantic import ValidationError  # Добавляем импорт
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

class PlaceHandler:
    async def create_place(self, request):
        json_data = await request.json()

        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            place_data = PlaceCreate(**json_data, creator_user_id=user_id)
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

            for photo_data in json_data.get('photos', []):
                new_photo = PlacePhoto(
                    place_id=new_place.id,
                    file=photo_data['file'],
                    name=photo_data.get('name')
                )
                db_session.add(new_photo)

            db_session.commit()

            # Воспользуемся relationship для загрузки данных фотографий
            db_session.refresh(new_place)

            # Создаем ответ, используя Pydantic модели для формирования JSON
            response_data = PlaceDisplay.from_orm(new_place)
            return web.json_response(response_data.dict(), status=201)

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
        

    async def add_place_to_travel(self,request):
        json_data = await request.json()
        try:
            places = json_data.get('places', [])
            new_ids = []

            # Сначала создаем все места и добавляем их в базу
            for place_data in places:
                new_place_travel = PlacesTravel(
                    users_travel_id=place_data['users_travel_id'],
                    place_id=place_data['place_id'],
                    date=place_data['date'],
                    description=place_data['description'],
                    order=place_data['order']
                )
                db_session.add(new_place_travel)
                db_session.flush()  # Применяем изменения, чтобы получить ID
                new_ids.append(new_place_travel.id)  # Сохраняем ID

            db_session.commit()

            # Получение только что добавленных мест по сохраненным ID
            all_new_places = db_session.query(PlacesTravel).filter(PlacesTravel.id.in_(new_ids)).all()

            # Подготовка данных о местах для ответа
            response_data = [PlaceTravelDisplay.from_orm(place).json() for place in all_new_places]

            # Возвращаем ответ как JSON строку
            return web.Response(text='[' + ','.join(response_data) + ']', content_type='application/json', status=201)
        except ValidationError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=400)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)