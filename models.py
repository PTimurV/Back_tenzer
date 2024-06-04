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
import imghdr

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
    __tablename__ = 'users1'
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
    user_id = Column(Integer, ForeignKey('users1.id'), primary_key=True)
    interest_id = Column(Integer, ForeignKey('interests.id'), primary_key=True)
    user = relationship("User", back_populates="user_interests")
    interest = relationship("Interest", back_populates="user_interests")

class UserFriend(Base):
    __tablename__ = 'user_friends'
    user_id = Column(Integer, ForeignKey('users1.id'), primary_key=True)
    friend_id = Column(Integer, ForeignKey('users1.id'), primary_key=True)
    status = Column(Integer, default=0)  
    __table_args__ = (Index('idx_status', 'status'),)
    user = relationship("User", foreign_keys=[user_id], back_populates="friends")
    friend = relationship("User", foreign_keys=[friend_id], back_populates="friend_of")

# Travels and related structures
class Travel(Base):
    __tablename__ = 'travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users1.id'))
    user_travel_id = Column(Integer, ForeignKey('users_travels.id'))
    mean_score = Column(Float)
    status = Column(String)
    count_users = Column(Integer)
    user_travel = relationship("UsersTravel", back_populates="travel", foreign_keys=[user_travel_id],
                               primaryjoin="Travel.user_travel_id==remote(UsersTravel.id)")



class UsersTravel(Base):
    __tablename__ = 'users_travels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_user_id = Column(Integer, ForeignKey('users1.id'))
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
    user_id = Column(Integer, ForeignKey('users1.id'), primary_key=True)
    travel = relationship("UsersTravel", back_populates="members")  # Убедитесь, что это добавлено
    user = relationship("User", back_populates="travel_memberships")

# Places and related structures
class Place(Base):
    __tablename__ = 'places'
    id = Column(Integer, primary_key=True, autoincrement=True)
    creator_user_id = Column(Integer, ForeignKey('users1.id'))
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
    user_id = Column(Integer, ForeignKey('users1.id'))
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
    user_id = Column(Integer, ForeignKey('users1.id'))  # ID пользователя, оставившего отзыв
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

class BestTravel(Base):
    __tablename__ = 'best_travels'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    travel_id = Column(Integer, ForeignKey('travels.id'), nullable=False)
    
    travel = relationship("Travel")



# Pydantic models for User

class AuthResponse(BaseModel):
    id: int
    username: str
    access_token: str
    img: Optional[str] = None  # Изменение типа на str

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)  # Определяем тип изображения
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v
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

class UserInterestDisplay(BaseModel):
    interest_id: int
    name: str

class UserProfileDisplay(BaseModel):
    username: str
    name: str
    surname: str
    img: Optional[bytes]
    owner: int
    interests: List[UserInterestDisplay]
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat() if x else None
        }
    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)  # Определяем тип изображения
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v
class FriendInfo(BaseModel):
    friend_id: int
    name: str
    surname: str
    img: Optional[str]
    username: str
    status: int

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v

class FriendsResponse(BaseModel):
    pending_sent: List[FriendInfo]
    pending_received: List[FriendInfo]
    friends: List[FriendInfo]

class UserInfo(BaseModel):
    id: int
    img: Optional[str]
    name: Optional[str]
    surname: Optional[str]
    username: str

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v

class UsersResponse(BaseModel):
    users: List[UserInfo]

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
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)  # Определяем тип изображения
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v



# Pydantic models for Travel

class AddMemberRequest(BaseModel):
    user_id: int  # ID пользователя, которого добавляем


class PhotoDisplay(BaseModel):
    id: int
    file: str

    class Config:
        from_attributes = True

    @validator('file', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v

class PlaceInfo(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    address: Optional[str] = None
    type: Optional[str] = None
    coordinates: Optional[str] = None
    travel_comment: Optional[str] = None
    travel_date: Optional[date] = None
    order: Optional[int] = None
    photos: List[PhotoDisplay]

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat() if x else None
        }

class MemberInfo(BaseModel):
    user_id: int
    username: str
    img: Optional[str]

    class Config:
        from_attributes = True

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v

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

    class Config:
        from_attributes = True

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v

class TravelDetailDisplay(BaseModel):
    id: int
    owner_user_id: int
    title: Optional[str]
    description: Optional[str]
    score: Optional[float]
    img: Optional[str]
    status: Optional[str]
    places: Optional[List[PlaceInfo]]
    members: Optional[List[MemberInfo]]

    class Config:
        from_attributes = True

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v
    

class UserTravelInfo(BaseModel):
    id: int
    owner_user_id: int
    title: Optional[str]
    description: Optional[str]
    score: Optional[float]
    img: Optional[str]
    status: Optional[str]
    places: Optional[List[PlaceInfo]]
    members: Optional[List[MemberInfo]]

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }

    @validator('img', pre=True, allow_reuse=True)
    def convert_bytes_to_base64(cls, v):
        if v is None:
            return None
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v

class TravelDetailDisplayExtended(BaseModel):
    id: int
    mean_score: Optional[float]
    count_users: Optional[int]
    user_travel: Optional[UserTravelInfo]

    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda v: v.isoformat() if v else None
        }

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
            image_type = imghdr.what(None, h=v)  # Определяем тип изображения
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
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
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)  # Определяем тип изображения
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
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

# Additional models for many-to-many relationships

class PlaceTravelBase(BaseModel):
    date: Optional[date]
    description: Optional[str]
    order: Optional[int]
    class Config:
        from_attributes = True
        json_encoders = {
            date: lambda x: x.isoformat()
        }

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
        if v is None:
            return None  # Возвращаем None, если нет файла
        if isinstance(v, bytes):
            image_type = imghdr.what(None, h=v)  # Определяем тип изображения
            if image_type in ['jpeg', 'png']:
                return f"data:image/{image_type};base64,{base64.b64encode(v).decode('utf-8')}"
            else:
                raise ValueError('Unsupported image type')
        return v