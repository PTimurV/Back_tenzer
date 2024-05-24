from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, Travel, Place

class TravelHandler:
    async def create_travel(self, request):
        data = await request.json()
        travel_name = data.get('name')
        travel_description = data.get('description')
        travel_places = data.get('places')

        try:
            new_travel = Travel(name=travel_name, description=travel_description)
            db_session.add(new_travel)
            db_session.flush()  # Получаем ID для связанных записей

            for place in travel_places:
                new_place = Place(address=place['address'], name=place['name'], type=place['type'], travel_id=new_travel.id)
                db_session.add(new_place)

            db_session.commit()

            return web.json_response({
                'id': new_travel.id,
                'name': travel_name,
                'description': travel_description,
                'places': [place.id for place in new_travel.places]
            }, status=201)

        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)

    async def get_all_travels(self, request):
        try:
            travels = db_session.query(Travel).all()
            travel_list = [{
                'id': travel.id,
                'name': travel.name,
                'description': travel.description,
                'places': [{
                    'id': place.id,
                    'address': place.address,
                    'name': place.name,
                    'type': place.type
                } for place in travel.places]
            } for travel in travels]

            return web.json_response(travel_list, status=200)

        except SQLAlchemyError as e:
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