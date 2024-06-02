from sqlalchemy import func, delete, select, text
from models import Travel, BestTravel, db_session,UsersTravel  # Предполагается, что ваши модели и async_session настроены корректно
from datetime import date

async def update_best_travels():
     # Получаем максимальное значение count_users
    max_count_users_query = select(func.max(Travel.count_users)).scalar_subquery()
    result_max_count_users = db_session.execute(select(max_count_users_query))
    max_count_users = result_max_count_users.scalar_one()
    print(f"Max count users: {max_count_users}")

    # Запрос для получения маршрутов с вычислением взвешенного значения
    weighted_score_expr = (0.6 * Travel.mean_score + 0.4 * (Travel.count_users / max_count_users_query)).label('weighted_score')
    print(weighted_score_expr)
    query = select(
        Travel,
        weighted_score_expr
    ).order_by(
        text('weighted_score DESC')
    ).limit(5)  # Допустим, сохраняем топ-10 маршрутов
    print("query = ", query)
    result = db_session.execute(query)
    best_travels = result.scalars().all()
    print(f"Best travels: {best_travels}")

    # Очистка таблицы перед добавлением новых данных
    db_session.execute(delete(BestTravel))
    db_session.commit()

    # Добавляем новые лучшие маршруты
    for travel in best_travels:
        new_best_travel = BestTravel(travel_id=travel.id)
        db_session.add(new_best_travel)
        print(f"Added travel: {travel.id}")

    db_session.commit()


async def update_travel_status():
    print("Updating travel statuses...")
    today = date.today()
    # Запрос для получения записей, у которых статус должен быть изменен на 'now'
    query = select(UsersTravel).filter(
        UsersTravel.start_date <= today,
        UsersTravel.end_date >= today
    )
    result = db_session.execute(query)
    travels_to_update = result.scalars().all()

    print(f"Travels to update: {travels_to_update}")

    # Обновление статуса у записей
    for travel in travels_to_update:
        travel.status = 'now'
        print(f"Updated travel ID: {travel.id} to status 'now'")
    
    db_session.commit()

    print("Travel statuses updated.")