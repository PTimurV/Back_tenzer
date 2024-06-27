Restfull api бэкенд для платформы планирования совместных путешествий.
Документация описана в Swagger.yaml.
Стэк: Python, AIOHTTP, SQLAlchemy, pydentic, alembic, bcrypt, psycorg, PyJWT.
Реализована полноценная реализация авторизации с JWT access и refresh токенами.
Реализованы CRUD операции для сущностей: User, Interest, UserInterest, UserFriend, Travel, UsersTravel, UsersTravelMember, Place, PlaceTravelComment, PlacePhoto, PlaceFeedback, PlacesTravel, BestTravel.
Реализована обработка ошибок и валидация полей.
Весь вывод информации реализован с помощью pydentic моделей.
Проект задеплоен. Начальный url: https://backtenzer-production.up.railway.app
