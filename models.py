from sqlalchemy import Column, Integer, String, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List, Optional
from config import host, user, password, db_name

Base = declarative_base()

# Настройка движка базы данных
DATABASE_URL = f"postgresql+psycopg://{user}:{password}@{host}/{db_name}"
engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Обертка для использования сессий в потоках
db_session = scoped_session(SessionLocal)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, index=True)
    login = Column(String, unique=True, index=True)
    password = Column(String)

class Travel(Base):
    __tablename__ = 'travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    places = relationship('Place', back_populates='travel')

class Place(Base):
    __tablename__ = 'places'
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String)
    name = Column(String)
    type = Column(String)
    travel_id = Column(Integer, ForeignKey('travels.id'))
    travel = relationship('Travel', back_populates='places')

# Pydantic models for data validation
class UserBase(BaseModel):
    email: str
    login: str

class UserCreate(UserBase):
    password: str

class UserDisplay(UserBase):
    id: int

class TravelBase(BaseModel):
    name: str
    description: Optional[str] = None

class TravelDisplay(TravelBase):
    id: int
    places: List[int] = []

class PlaceBase(BaseModel):
    address: str
    name: str
    type: str
    travel_id: int