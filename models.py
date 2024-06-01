from sqlalchemy import Column, Integer, String, ForeignKey, create_engine , Date, Float,Index
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel, EmailStr, constr, validator,Field
from typing import List, Optional
from config import host, user, password, db_name
from datetime import date
import os
from sqlalchemy import LargeBinary
import base64

Base = declarative_base()

# Настройка движка базы данных
DATABASE_URL = f"postgresql+psycopg://{user}:{password}@{host}/{db_name}"
#DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

# Создание фабрики сессий
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Обертка для использования сессий в потоках
db_session = scoped_session(SessionLocal)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    img = Column(LargeBinary)
    name = Column(String)
    surname = Column(String)
    role = Column(String)
    gender = Column(String)
    birthday = Column(Date)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    city = Column(String)
    password = Column(String)
    user_interests = relationship("UserInterest", back_populates="user")
    friends = relationship("UserFriend", foreign_keys="[UserFriend.user_id]", back_populates="user")
    friend_of = relationship("UserFriend", foreign_keys="[UserFriend.friend_id]", back_populates="friend")
    feedbacks = relationship("PlaceFeedback", back_populates="user")
    travel_memberships = relationship("UsersTravelMember", back_populates="user")

class Interest(Base):
    __tablename__ = 'interests'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    user_interests = relationship("UserInterest", back_populates="interest")

class UserInterest(Base):
    __tablename__ = 'user_interests'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    interest_id = Column(Integer, ForeignKey('interests.id'), primary_key=True)
    user = relationship("User", back_populates="user_interests")
    interest = relationship("Interest", back_populates="user_interests")

class UserFriend(Base):
    __tablename__ = 'user_friends'
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    status = Column(Integer, default=0)  
    __table_args__ = (Index('idx_status', 'status'),)
    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_of")

# Travels and related structures
class Travel(Base):
    __tablename__ = 'travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    user_travel_id = Column(Integer, ForeignKey('users_travels.id'))
    mean_score = Column(Float)
    status = Column(String)
    count_users = Column(Integer)
    user_travel = relationship("UsersTravel", back_populates="travel", foreign_keys=[user_travel_id],
                               primaryjoin="Travel.user_travel_id==remote(UsersTravel.id)")



class UsersTravel(Base):
    __tablename__ = 'users_travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(String)
    score = Column(Float)
    img = Column(LargeBinary)
    status = Column(String)
    start_date = Column(Date)  # Добавлено поле для даты начала путешествия
    end_date = Column(Date)    # Добавлено поле для даты окончания путешествия
    travel_id = Column(Integer, ForeignKey('travels.id'))
    places = relationship("PlacesTravel", back_populates="travel")
    members = relationship("UsersTravelMember", back_populates="travel")
    travel = relationship("Travel", back_populates="user_travel", foreign_keys=[travel_id],
                          primaryjoin="UsersTravel.travel_id==foreign(Travel.id)")

class UsersTravelMember(Base):
    __tablename__ = 'user_travels_members'
    users_travel_id = Column(Integer, ForeignKey('users_travels.id'), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    travel = relationship("UsersTravel", back_populates="members")  # Убедитесь, что это добавлено
    user = relationship("User", back_populates="travel_memberships")

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
    photos = relationship("PlacePhoto", back_populates="place", cascade="all, delete-orphan")
    feedbacks = relationship("PlaceFeedback", back_populates="place")
    travels = relationship("PlacesTravel", back_populates="place")
    mean_score = Column(Float, default=0.0)

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
    file = Column(LargeBinary)
    place = relationship("Place", back_populates="photos")

class PlaceFeedback(Base):
    __tablename__ = 'places_feedback'
    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(Integer, ForeignKey('places.id'))
    user_id = Column(Integer, ForeignKey('users.id'))  # ID пользователя, оставившего отзыв
    score = Column(Float)
    description = Column(String)
    place = relationship("Place", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")

class PlacesTravel(Base):
    __tablename__ = 'places_travel'
    id = Column(Integer, primary_key=True, autoincrement=True)
    users_travel_id = Column(Integer, ForeignKey('users_travels.id'))
    place_id = Column(Integer, ForeignKey('places.id'))
    date = Column(Date)
    description = Column(String)
    order = Column(Integer)

    # Relationships
    travel = relationship("UsersTravel", back_populates="places")
    place = relationship("Place", back_populates="travels")





# Pydantic models for User

class FriendDisplay(BaseModel):
    friend_id: int
    username: str
    name: Optional[str]
    surname: Optional[str]
    img: Optional[str]
    status: int

class UserBase(BaseModel):
    email: EmailStr
    username: str
    name: Optional[str]
    surname: Optional[str]

class UserUpdate(BaseModel):
    name: Optional[str]
    surname: Optional[str]
    role: Optional[str]
    gender: Optional[str]
    birthday: Optional[str]
    city: Optional[str]
    interests: List[int] = []
    img: Optional[bytes] = Field(None, description="Binary image data") 

    class Config:
        from_attributes = True

class UserCreate(UserBase):
    password: str

class UserDisplay(UserBase):
    id: int
    city: Optional[str]
    birthday: Optional[date]

class UserInterestDisplay(BaseModel):
    interest_id: int
    name: str

class UserSettingsDisplay(UserBase):
    id: int
    img: Optional[bytes]
    name: Optional[str]
    surname: Optional[str]
    role: Optional[str]
    gender: Optional[str]
    birthday: Optional[date]
    city: Optional[str]
    interests: List[UserInterestDisplay] = []
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat() if x else None
        }
    @validator('img', pre=True, allow_reuse=True)
    def convert_img_to_base64(cls, value):
        if value is not None:
            return f"data:image/png;base64,{base64.b64encode(value).decode('utf-8')}"
        return value
# Pydantic models for Interest
class InterestBase(BaseModel):
    name: str

class InterestDisplay(InterestBase):
    id: int






# Pydantic models for Travel
class TravelBase(BaseModel):
    title: str
    description: Optional[str]

class AddMemberRequest(BaseModel):
    user_id: int  # ID пользователя, которого добавляем

class TravelCreate(TravelBase):
    user_id: int

class TravelDisplay(TravelBase):
    id: int
    mean_score: Optional[float]
    img: Optional[str]
    status: str
    count_users: Optional[int]

class PhotoDisplay(BaseModel):
    id: int
    file: str
    class Config:
        from_attributes = True
    @validator('file', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            return f"data:image/jpeg;base64,{base64.b64encode(v).decode('utf-8')}"
        return v

class PlaceInfo(BaseModel):
    id: int
    title: str
    description: str
    address: str
    type: str
    coordinates: str
    travel_comment: Optional[str] = None
    travel_date: Optional[date] = None
    order: Optional[int] = None
    photos: List[PhotoDisplay]
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat() if x else None
        }

class TravelInfoDisplay(BaseModel):
    id: int
    owner_user_id: int
    title: Optional[str]
    description: Optional[str]
    img: Optional[str]
    status: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    places: Optional[List[PlaceInfo]]



# Pydantic models for Place
class PlaceBase(BaseModel):
    title: str
    description: Optional[str]
    address: str    
    type: str
    coordinates: str



class PhotoDisplayId(BaseModel):
    file: str
    @validator('file', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            return f"data:image/jpeg;base64,{base64.b64encode(v).decode('utf-8')}"
        return v

class FeedbackDisplayId(BaseModel):
    user_id: int
    username: str
    score: float
    description: Optional[str]

class PlaceDisplayId(BaseModel):
    id: int
    creator_user_id: int
    title: str
    description: str
    address: str
    type: str
    coordinates: str
    status: str
    mean_score: float
    photos: List[PhotoDisplayId]
    feedbacks: List[FeedbackDisplayId]

class PlaceDisplayId2(BaseModel):
    id: int
    creator_user_id: int
    title: str
    description: str
    address: str
    type: str
    coordinates: str
    mean_score: Optional[float]
    photos: Optional[List[PhotoDisplayId]]


class PlaceCreate(PlaceBase):
    creator_user_id: int

class PhotoBase(BaseModel):
    file: str

class PhotoDisplay(PhotoBase):
    id: int
    place_id: int
    class Config:
        from_attributes = True
    @validator('file', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if isinstance(v, bytes):
            return f"data:image/jpeg;base64,{base64.b64encode(v).decode('utf-8')}"
        return v

class PlaceDisplay(PlaceBase):
    id: int
    status: str
    photos: List[PhotoDisplay]
    class Config:
        from_attributes = True

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



# Additional models for many-to-many relationships

class UserFriendDisplay(BaseModel):
    user_id: int
    friend_id: int

class UsersTravelMemberDisplay(BaseModel):
    users_travel_id: int
    user_id: int

class PlaceTravelBase(BaseModel):
    date: Optional[date]
    description: Optional[str]
    order: Optional[int]
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat()
        }

class PlaceTravelCreate(PlaceTravelBase):
    users_travel_id: int
    place_id: int

class PlaceTravelDisplay(PlaceTravelBase):
    id: int
    users_travel_id: int
    place_id: int
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat()
        }





#Для эндпоинта просмотра детальной инфы о маршурте через id
class PhotoDisplay2(BaseModel):
    id: int
    file: str
    class Config:
        from_attributes = True
    @validator('file', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if isinstance(v, bytes):
            return f"data:image/jpeg;base64,{base64.b64encode(v).decode('utf-8')}"
        return v

class PlaceDisplay2(BaseModel):
    id: int
    title: str
    description: str
    address: str
    type: str
    coordinates: str
    status: str
    mean_score: float
    photos: List[PhotoDisplay2]= []
    class Config:
        from_attributes = True

class PlaceTravelDisplay2(BaseModel):
    date: date
    description: str
    order: int
    place: PlaceDisplay2
    class Config:
        from_attributes = True

class TravelMemberDisplay2(BaseModel):
    user_id: int
    username: Optional[str]
    img: Optional[str]
    class Config:
        from_attributes = True

class UsersTravelDisplay2(BaseModel):
    id: int
    owner_user_id: int
    title: str
    description: str
    score: Optional[float]
    img: Optional[str]
    status: str
    places: List[PlaceTravelDisplay2] = []
    members: List[TravelMemberDisplay2] = []
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat()
        }
