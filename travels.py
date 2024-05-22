from aiohttp import web
from db import get_connection

async def create_travel(request):
    data = await request.json()
    print(data)
    travel_name = data.get('name')
    travel_description = data.get('description')
    travel_places = data.get('places')

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO travels (name, description) VALUES (%s, %s) RETURNING id;",
                (travel_name, travel_description)
            )
            travel_id = cursor.fetchone()[0]

            for place in travel_places:
                cursor.execute(
                    "INSERT INTO places (travel_id, address, name, type) VALUES (%s, %s, %s, %s);",
                    (travel_id, place['address'], place['name'], place['type'])
                )

            connection.commit()

        return web.json_response({'id': travel_id, 'name': travel_name, 'description': travel_description, 'places': travel_places}, status=201)

    except Exception as ex:
        return web.json_response({'error': str(ex)}, status=500)

    finally:
        if connection:
            connection.close()

async def get_all_travels(request):
    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM travels;")
            travels = cursor.fetchall()

            travel_list = []
            for travel in travels:
                cursor.execute("SELECT * FROM places WHERE travel_id = %s;", (travel[0],))
                places = cursor.fetchall()
                travel_list.append({
                    'id': travel[0],
                    'name': travel[1],
                    'description': travel[2],
                    'places': [{'id': place[0], 'address': place[2], 'name': place[3], 'type': place[4]} for place in places]
                })

        return web.json_response(travel_list, status=200)

    except Exception as ex:
        return web.json_response({'error': str(ex)}, status=500)

    finally:
        if connection:
            connection.close()

async def get_travel_by_id(request):
    travel_id = request.match_info['id']

    try:
        connection = get_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM travels WHERE id = %s;", (travel_id,))
            travel = cursor.fetchone()

            if not travel:
                return web.json_response({'message': 'Travel not found'}, status=404)

            cursor.execute("SELECT * FROM places WHERE travel_id = %s;", (travel[0],))
            places = cursor.fetchall()

            travel_data = {
                'id': travel[0],
                'name': travel[1],
                'description': travel[2],
                'places': [{'id': place[0], 'address': place[2], 'name': place[3], 'type': place[4]} for place in places]
            }

        return web.json_response(travel_data, status=200)

    except Exception as ex:
        return web.json_response({'error': str(ex)}, status=500)

    finally:
        if connection:
            connection.close()