from sqlalchemy import func, delete, select, text
from models import Travel, BestTravel, db_session,UsersTravel  # Предполагается, что ваши модели и async_session настроены корректно
from datetime import date

async def update_best_travels():
     # Получаем максимальное значение count_users
    max_count_users_query = select(func.max(Travel.count_users)).scalar_subquery()
    result_max_count_users = db_session.execute(select(max_count_users_query))
    max_count_users = result_max_count_users.scalar_one()

    # Запрос для получения маршрутов с вычислением взвешенного значения
    weighted_score_expr = (0.6 * Travel.mean_score + 0.4 * (Travel.count_users / max_count_users_query)).label('weighted_score')
    query = select(
        Travel,
        weighted_score_expr
    ).order_by(
        text('weighted_score DESC')
    ).limit(5)  # Допустим, сохраняем топ-10 маршрутов
    result = db_session.execute(query)
    best_travels = result.scalars().all()

    # Очистка таблицы перед добавлением новых данных
    db_session.execute(delete(BestTravel))
    db_session.commit()

    # Добавляем новые лучшие маршруты
    for travel in best_travels:
        new_best_travel = BestTravel(travel_id=travel.id)
        db_session.add(new_best_travel)

    db_session.commit()


async def update_travel_status():
    today = date.today()
    # Запрос для получения записей, у которых статус должен быть изменен на 'now'
    query = select(UsersTravel).filter(
        UsersTravel.start_date <= today,
        UsersTravel.end_date >= today
    )
    result = db_session.execute(query)
    travels_to_update = result.scalars().all()


    # Обновление статуса у записей
    for travel in travels_to_update:
        travel.status = 'now'
    
    db_session.commit()