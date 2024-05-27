from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, Travel, Place,UsersTravel, PlaceInfo,PlacesTravel,TravelInfoDisplay,PhotoDisplay
from jwtAuth import JWTAuth
from pydantic import ValidationError  # Добавляем импорт
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from sqlalchemy.orm import joinedload
import json
class TravelHandler:
    async def create_user_travel(self, request):
        # Получение токена из заголовков и декодирование для извлечения user_id
        token = request.headers.get('Authorization', '').split(' ')[-1]
        user_payload = JWTAuth.decode_access_token(token)
        owner_user_id = user_payload.get('user_id')

        if not owner_user_id:
            return web.json_response({'error': 'Unauthorized access'}, status=401)

        data = await request.json()
        title = data.get('title')
        description = data.get('description')
        img = data.get('img', '')  # Добавляем значение по умолчанию для img

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

            return web.json_response({
                'id': new_users_travel.id,
                'title': title,
                'description': description,
                'status': new_users_travel.status,
                'img': img
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
                img=travel.img,
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
                    photos=[PhotoDisplay.from_orm(photo) for photo in place.place.photos],
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
        



    async def get_travel_by_id(self, request):
        travel_id = int(request.match_info['id'])

        try:
            travel = db_session.query(Travel).filter(Travel.id == travel_id).first()
            if not travel:
                return web.json_response({'message': 'Travel not found'}, status=404)

            travel_data = {
                'id': travel.id,
                'name': travel.name,
                'description': travel.description,
                'places': [{
                    'id': place.id,
                    'address': place.address,
                    'name': place.name,
                    'type': place.type
                } for place in travel.places]
            }

            return web.json_response(travel_data, status=200)

        except SQLAlchemyError as e:
            return web.json_response({'error': str(e)}, status=500)