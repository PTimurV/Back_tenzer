from sqlalchemy import Column, Integer, String, ForeignKey, create_engine , Date, Float
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr, constr, validator
from typing import List, Optional
from config import host, user, password, db_name
from datetime import date
import os

Base = declarative_base()

# Настройка движка базы данных
#DATABASE_URL = f"postgresql+psycopg://{user}:{password}@{host}/{db_name}"
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Обертка для использования сессий в потоках
db_session = scoped_session(SessionLocal)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    img = Column(String)
    name = Column(String)
    surname = Column(String)
    role = Column(String)
    gender = Column(String)
    birthday = Column(Date)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    city = Column(String)
    password = Column(String)

class Interest(Base):
    __tablename__ = 'interests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)

class UserInterest(Base):
    __tablename__ = 'user_interests'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    interest_id = Column(Integer, ForeignKey('interests.id'), primary_key=True)

class UserFriend(Base):
    __tablename__ = 'user_friends'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

# Travels and related structures
class Travel(Base):
    __tablename__ = 'travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(String)
    mean_score = Column(Float)
    img = Column(String)
    status = Column(String)
    count_users = Column(Integer)

class UsersTravel(Base):
    __tablename__ = 'users_travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(String)
    score = Column(Float)
    img = Column(String)
    status = Column(String)
    travel_id = Column(Integer, ForeignKey('travels.id'))

class UsersTravelMember(Base):
    __tablename__ = 'user_travels_members'
    users_travel_id = Column(Integer, ForeignKey('users_travels.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)

# Places and related structures
class Place(Base):
    __tablename__ = 'places'
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(String)
    address = Column(String)
    type = Column(String)
    coordinates = Column(String)
    status = Column(String)

class PlaceTravelComment(Base):
    __tablename__ = 'place_travel_comments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_travel_id = Column(Integer, ForeignKey('places.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date)
    comment = Column(String)

class PlacePhoto(Base):
    __tablename__ = 'places_photo'
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey('places.id'))
    file = Column(String)
    name = Column(String)

class PlaceFeedback(Base):
    __tablename__ = 'places_feedback'
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey('places.id'))
    score = Column(Float)
    description = Column(String)


# Pydantic models for User
class UserBase(BaseModel):
    email: EmailStr
    username: str
    name: Optional[str]
    surname: Optional[str]

class UserCreate(UserBase):
    password: str

class UserDisplay(UserBase):
    id: int
    city: Optional[str]
    birthday: Optional[date]

# Pydantic models for Interest
class InterestBase(BaseModel):
    name: str

class InterestDisplay(InterestBase):
    id: int

# Pydantic models for Travel
class TravelBase(BaseModel):
    title: str
    description: Optional[str]

class TravelCreate(TravelBase):
    user_id: int

class TravelDisplay(TravelBase):
    id: int
    mean_score: Optional[float]
    img: Optional[str]
    status: str
    count_users: Optional[int]

# Pydantic models for Place
class PlaceBase(BaseModel):
    title: str
    description: Optional[str]
    address: str
    type: str
    coordinates: str

class PlaceCreate(PlaceBase):
    creator_user_id: int

class PlaceDisplay(PlaceBase):
    id: int
    status: str

# Pydantic models for Feedback and Comments
class PlaceFeedbackBase(BaseModel):
    score: float
    description: Optional[str]

class PlaceFeedbackDisplay(PlaceFeedbackBase):
    id: int
    place_id: int

class PlaceCommentBase(BaseModel):
    comment: str
    date: date

class PlaceCommentDisplay(PlaceCommentBase):
    id: int
    user_id: int
    place_travel_id: int

class PhotoBase(BaseModel):
    file: str
    name: Optional[str]

class PhotoDisplay(PhotoBase):
    id: int
    place_id: int

# Additional models for many-to-many relationships
class UserInterestDisplay(BaseModel):
    user_id: int
    interest_id: int

class UserFriendDisplay(BaseModel):
    user_id: int
    friend_id: int

class UsersTravelMemberDisplay(BaseModel):
    users_travel_id: int
    user_id: int