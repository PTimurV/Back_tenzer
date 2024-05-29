from aiohttp import web
from sqlalchemy.exc import SQLAlchemyError
from models import db_session, PlaceFeedback, User,PlaceFeedbackBase, Place
from jwtAuth import JWTAuth
from pydantic import BaseModel, ValidationError
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

class FeedbackHandler(BaseModel):

    async def add_feedback(self,request):
        place_id = int(request.match_info.get('place_id'))

        token = request.headers.get('Authorization', '').split(' ')[-1]
        try:
            payload = JWTAuth.decode_access_token(token)
            user_id = payload.get("user_id")
            if not user_id:
                raise web.HTTPUnauthorized(reason="Missing or invalid token")

            data = await request.json()
            feedback_data = PlaceFeedbackBase(**data)

            new_feedback = PlaceFeedback(
                place_id=place_id,
                user_id=user_id,
                score=feedback_data.score,
                description=feedback_data.description
            )
            db_session.add(new_feedback)
            db_session.flush()

            # Вычисляем новую среднюю оценку
            place = db_session.query(Place).filter(Place.id == place_id).first()
            all_feedbacks = db_session.query(PlaceFeedback.score).filter(PlaceFeedback.place_id == place_id).all()
            if all_feedbacks:
                new_mean_score = sum([fb.score for fb in all_feedbacks]) / len(all_feedbacks)
                place.mean_score = new_mean_score

            db_session.commit()

            # Обновляем и возвращаем данные
            db_session.refresh(new_feedback)
            db_session.refresh(place)
            response_data = {
                'id': new_feedback.id,
                'place_id': new_feedback.place_id,
                'user_id': new_feedback.user_id,
                'score': new_feedback.score,
                'description': new_feedback.description,
                'mean_score': place.mean_score
            }

            return web.json_response(response_data, status=201)

        except ValidationError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=400)
        except (ExpiredSignatureError, InvalidTokenError) as e:
            return web.json_response({'error': str(e)}, status=401)
        except SQLAlchemyError as e:
            db_session.rollback()
            return web.json_response({'error': str(e)}, status=500)
