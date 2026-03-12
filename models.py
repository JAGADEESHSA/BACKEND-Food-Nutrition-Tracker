from sqlalchemy import Column, Integer, String, Float, ForeignKey, TIMESTAMP, DateTime
from sqlalchemy.sql import func
from database import Base
from datetime import datetime
from sqlalchemy import Date, Time
from sqlalchemy import Column, Integer, String, Float, Date, Time, Boolean


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100))
    email = Column(String(150), unique=True, index=True)
    password = Column(String(255))
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    calorie_goal = Column(Float)
    protein_goal = Column(Float)
    carbs_goal = Column(Float)
    fat_goal = Column(Float)

    goal_mode = Column(Boolean, default=False)
    profile_photo = Column(String(255), nullable=True)

class UserGoal(Base):
    __tablename__ = "user_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    calorie_goal = Column(Float)
    protein_goal = Column(Float)
    carbs_goal = Column(Float)
    fat_goal = Column(Float)
    goal_type = Column(String(50))


class UserDetails(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    age = Column(Integer)
    height = Column(Float)
    weight = Column(Float)
    gender = Column(String(20))


class OTPCode(Base):
    __tablename__ = "otp_codes"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(150))
    otp = Column(String(6))
    created_at = Column(DateTime, default=datetime.utcnow)

    
class Food(Base):
    __tablename__ = "foods"

    food_id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String(255))
    calories_per_100g = Column(Float)
    protein_per_100g = Column(Float)
    carbs_per_100g = Column(Float)
    fat_per_100g = Column(Float)
    fiber_per_100g = Column(Float)
    unit_type = Column(String(50))
    avg_weight = Column(Float)

    
from pydantic import BaseModel

class FoodLog(Base):
    __tablename__ = "food_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    
    food_id = Column(Integer)
    food_name = Column(String(255))
    grams = Column(Float)

    calories = Column(Float)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    fiber = Column(Float)

    log_date = Column(Date)
    log_time = Column(Time)

    