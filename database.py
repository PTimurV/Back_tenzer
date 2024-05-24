from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import host, user, password, db_name

Base = declarative_base()

class Database:
    # Строка подключения, использующая данные из файла config
    DATABASE_URL = f"postgresql+psycopg://{user}:{password}@{host}/{db_name}"

    def __init__(self):
        # Создание движка SQLAlchemy
        self.engine = create_engine(self.DATABASE_URL, echo=True)
        # Создание фабрики сессий
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)

    def get_db(self):
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()