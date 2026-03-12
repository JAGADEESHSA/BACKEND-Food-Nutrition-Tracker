from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessionLocal, engine
import models
import random
import smtplib
import schemas
from email.mime.text import MIMEText
from pydantic import BaseModel
from datetime import datetime
from datetime import date
from sqlalchemy.orm import Session
from fastapi import Depends
from datetime import date, timedelta
import os
import shutil
from fastapi import UploadFile, File
from schemas import GoalRequest, AIGoalRequest, ToggleGoalRequest
from ultralytics import YOLO
from PIL import Image
import io
from fastapi import UploadFile, File
from ai.food_nutrition import food_nutrition
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles

model = YOLO("ai/yolov8n.pt")




models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.mount("/profile_images", StaticFiles(directory="profile_images"), name="profile_images")

# ---------------- DATABASE DEPENDENCY ----------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ================= REQUEST MODELS =================

class SignupRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserDetailsRequest(BaseModel):
    user_id: int
    age: int
    height: float
    weight: float
    gender: str

class ForgotPasswordRequest(BaseModel):
    email: str

class SendOTPRequest(BaseModel):
    email: str

class ChangePasswordRequest(BaseModel):
    email: str
    current_password: str
    new_password: str
    confirm_password: str

class VerifyOTPRequest(BaseModel):
    email: str
    otp: str


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    confirm_password: str
    

class FoodLogRequest(BaseModel):
    user_id: int
    food_id: int
    grams: float

class GoalRequest(BaseModel):
    user_id: int
    calorie_goal: float
    protein_goal: float
    carbs_goal: float
    fat_goal: float
    goal_type: str

class AIGoalRequest(BaseModel):
    user_id: int
    goal_type: str


class GoalAIRequest(BaseModel):
    user_id: int
    goal_type: str   # weight_loss / maintain / muscle_gain


# ================= SIGNUP =================
@app.post("/signup")
def signup(user: SignupRequest, db: Session = Depends(get_db)):

    existing_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = models.User(
        full_name=user.full_name,
        email=user.email,
        password=user.password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "Account created", "user_id": new_user.id}


# ================= LOGIN =================
@app.post("/login")
def login(user: LoginRequest, db: Session = Depends(get_db)):

    db_user = db.query(models.User).filter(
        models.User.email == user.email
    ).first()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email")

    if db_user.password != user.password:
        raise HTTPException(status_code=400, detail="Invalid password")

    return {"message": "Login successful", "user_id": db_user.id}


# ================= USER DETAILS =================
@app.post("/user-details")
def save_user_details(details: UserDetailsRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        models.User.id == details.user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_details = models.UserDetails(
        user_id=details.user_id,
        age=details.age,
        height=details.height,
        weight=details.weight,
        gender=details.gender
    )

    db.add(new_details)
    db.commit()

    return {"message": "User details saved successfully"}


# ================= FORGOT PASSWORD (Screen 1) =================
@app.post("/forgot-password")
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    otp = f"{random.randint(0, 9999):04d}"
    print("Generated OTP:", otp)

    # 🔥 SAVE OTP TO DATABASE
    db.query(models.OTPCode).filter(
        models.OTPCode.email == request.email
    ).delete()

    new_otp = models.OTPCode(
        email=request.email,
        otp=otp
    )

    db.add(new_otp)
    db.commit()

    sender_email = "jagadeesh9121887794@gmail.com"
    sender_password = "tackfguvwgnxohow"

    message = MIMEText(f"Your OTP is: {otp}")
    message["Subject"] = "OTP Verification"
    message["From"] = sender_email
    message["To"] = request.email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(sender_email, sender_password)
    server.sendmail(sender_email, request.email, message.as_string())
    server.quit()

    return {"message": "OTP sent successfully"}

# ================= VERIFY OTP =================


@app.post("/verify-otp")
def verify_otp(request: VerifyOTPRequest, db: Session = Depends(get_db)):

    otp_record = db.query(models.OTPCode).filter(
        models.OTPCode.email == request.email,
        models.OTPCode.otp == request.otp
    ).first()

    if not otp_record:
        raise HTTPException(status_code=400, detail="Invalid OTP")

    return {"message": "OTP verified successfully"}


# ================= RESET PASSWORD =================
@app.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password = request.new_password
    db.commit()

    # Delete OTP after reset
    db.query(models.OTPCode).filter(
        models.OTPCode.email == request.email
    ).delete()
    db.commit()

    return {"message": "Password updated successfully"}

# ================= CHANGE PASSWORD =================
@app.post("/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # check current password
    if user.password != request.current_password:
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    # check new password match
    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user.password = request.new_password
    db.commit()

    return {"message": "Password changed successfully"}


@app.post("/save-food-log")
def save_food_log(request: FoodLogRequest, db: Session = Depends(get_db)):

    food = db.query(models.Food).filter(
        models.Food.food_id == request.food_id
    ).first()

    if not food:
        raise HTTPException(status_code=404, detail="Food not found")

    grams = request.grams

    calories = (food.calories_per_100g * grams) / 100
    protein = (food.protein_per_100g * grams) / 100
    carbs = (food.carbs_per_100g * grams) / 100
    fat = (food.fat_per_100g * grams) / 100
    fiber = (food.fiber_per_100g * grams) / 100

    now = datetime.now().strftime("%I:%M %p")

    new_log = models.FoodLog(
        user_id=request.user_id,
        food_id=food.food_id,
        food_name=food.food_name,
        grams=grams,
        calories=calories,
        protein=protein,
        carbs=carbs,
        fat=fat,
        fiber=fiber,
        log_date=now.date(),
        log_time = datetime.now().strftime("%I:%M %p")
()
    )

    db.add(new_log)
    db.commit()

    return {"message": "Food saved successfully"}


@app.get("/today-food-logs")
def get_today_food_logs(user_id: int, db: Session = Depends(get_db)):

    from datetime import date

    today = date.today()

    logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.log_date == today
    ).order_by(models.FoodLog.log_time.desc()).all()

    results = []

    for log in logs:
        results.append({
            "log_id": log.log_id,
            "food_name": log.food_name,
            "grams": log.grams,
            "calories": log.calories,
            "protein": log.protein,
            "carbs": log.carbs,
            "fat": log.fat,
            "fiber": log.fiber,
            "time": str(log.log_time)
        })

    return results

@app.get("/food-log/{log_id}")
def get_food_log_details(log_id: int, db: Session = Depends(get_db)):

    log = db.query(models.FoodLog).filter(
        models.FoodLog.log_id == log_id
    ).first()

    if not log:
        raise HTTPException(status_code=404, detail="Food log not found")

    return {
        "food_name": log.food_name,
        "grams": log.grams,
        "calories": log.calories,
        "protein": log.protein,
        "carbs": log.carbs,
        "fat": log.fat,
        "fiber": log.fiber
    }

@app.delete("/food-log/{log_id}")
def delete_food_log(log_id: int, db: Session = Depends(get_db)):

    log = db.query(models.FoodLog).filter(
        models.FoodLog.log_id == log_id
    ).first()

    if not log:
        raise HTTPException(status_code=404, detail="Food log not found")

    db.delete(log)
    db.commit()

    return {"message": "Food deleted successfully"}


from datetime import date, timedelta
from sqlalchemy import func

@app.get("/weekly-calories/{user_id}")
def get_weekly_calories(user_id: int, db: Session = Depends(get_db)):

    today = date.today()
    start_date = today - timedelta(days=6)

    results = db.query(
        models.FoodLog.log_date,
        func.sum(models.FoodLog.calories)
    ).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.log_date >= start_date
    ).group_by(
        models.FoodLog.log_date
    ).all()

    # convert DB result to dictionary
    db_data = {r[0]: float(r[1]) for r in results}

    response = []

    # ensure all 7 days exist
    for i in range(7):

        day_date = start_date + timedelta(days=i)

        response.append({
            "day": day_date.strftime("%a"),
            "date": day_date.strftime("%Y-%m-%d"),
            "calories": db_data.get(day_date, 0)
        })

    return response

from datetime import date

@app.get("/today-total-calories/{user_id}")
def get_today_total_calories(user_id: int, db: Session = Depends(get_db)):

    today = date.today()

    logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.log_date == today
    ).all()

    total_calories = sum(log.calories for log in logs)

    return {
        "date": str(today),
        "total_calories": total_calories
    }

from datetime import date

from datetime import date

@app.get("/today-nutrition/{user_id}")
def get_today_nutrition(user_id: int, db: Session = Depends(get_db)):

    today = date.today()

    logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.log_date == today
    ).all()

    total_calories = sum(log.calories for log in logs)
    total_protein = sum(log.protein for log in logs)
    total_carbs = sum(log.carbs for log in logs)
    total_fat = sum(log.fat for log in logs)
    total_fiber = sum(log.fiber for log in logs)

    return {
        "date": str(today),
        "calories": round(total_calories, 2),
        "protein": round(total_protein, 2),
        "carbs": round(total_carbs, 2),
        "fat": round(total_fat, 2),
        "fiber": round(total_fiber, 2)
    }


@app.post("/save-goals")
def save_goals(data: GoalRequest, db: Session = Depends(get_db)):

    goal = db.query(models.UserGoal)\
        .filter(models.UserGoal.user_id == data.user_id)\
        .first()

    if goal:
        goal.calorie_goal = data.calorie_goal
        goal.protein_goal = data.protein_goal
        goal.carbs_goal = data.carbs_goal
        goal.fat_goal = data.fat_goal
        goal.goal_type = data.goal_type

    else:
        goal = models.UserGoal(
            user_id=data.user_id,
            calorie_goal=data.calorie_goal,
            protein_goal=data.protein_goal,
            carbs_goal=data.carbs_goal,
            fat_goal=data.fat_goal,
            goal_type=data.goal_type
        )
        db.add(goal)

    db.commit()

    return {"message": "Goal saved successfully"}



@app.get("/get-goal/{user_id}")
def get_goal(user_id: int, db: Session = Depends(get_db)):

    goal = db.query(models.UserGoal)\
        .filter(models.UserGoal.user_id == user_id)\
        .first()

    if not goal:
        return {"message": "Goal not set"}

    return {
        "calorie_goal": goal.calorie_goal,
        "protein_goal": goal.protein_goal,
        "carbs_goal": goal.carbs_goal,
        "fat_goal": goal.fat_goal,
        "goal_type": goal.goal_type
    }

@app.get("/goal-progress/{user_id}")
def goal_progress(user_id: int, db: Session = Depends(get_db)):

    today = date.today()

    goal = db.query(models.UserGoal)\
        .filter(models.UserGoal.user_id == user_id)\
        .first()

    if not goal:
        return {"message": "Goal not set"}

    logs = db.query(models.FoodLog)\
        .filter(
            models.FoodLog.user_id == user_id,
            models.FoodLog.log_date == today
        ).all()

    calories = sum(l.calories for l in logs)
    protein = sum(l.protein for l in logs)
    carbs = sum(l.carbs for l in logs)
    fat = sum(l.fat for l in logs)

    return {
        "goal_calories": goal.calorie_goal,
        "goal_protein": goal.protein_goal,
        "goal_carbs": goal.carbs_goal,
        "goal_fat": goal.fat_goal,

        "consumed_calories": calories,
        "consumed_protein": protein,
        "consumed_carbs": carbs,
        "consumed_fat": fat
    }



@app.post("/ai-calculate-goal")
def ai_calculate_goal(data: AIGoalRequest, db: Session = Depends(get_db)):

    user = db.query(models.UserDetails)\
        .filter(models.UserDetails.user_id == data.user_id)\
        .first()

    if not user:
        return {"message": "User details not found"}

    weight = user.weight
    height = user.height
    age = user.age

    # BMR formula
    bmr = 10 * weight + 6.25 * height - 5 * age + 5

    if data.goal_type == "weight_loss":
        calories = bmr - 300
    elif data.goal_type == "muscle_gain":
        calories = bmr + 300
    else:
        calories = bmr

    protein = weight * 1.8
    fat = calories * 0.25 / 9
    carbs = (calories - (protein * 4 + fat * 9)) / 4

    return {
        "calorie_goal": round(calories),
        "protein_goal": round(protein),
        "carbs_goal": round(carbs),
        "fat_goal": round(fat)
    }



@app.get("/ai-food-suggestions/{user_id}")
def ai_food_suggestions(user_id: int, db: Session = Depends(get_db)):

    today = date.today()

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        return {"error": "User not found"}

    logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.log_date == today
    ).all()

    consumed_calories = sum(log.calories for log in logs)
    consumed_protein = sum(log.protein for log in logs)
    consumed_carbs = sum(log.carbs for log in logs)
    consumed_fat = sum(log.fat for log in logs)

    remaining_calories = max(user.calorie_goal - consumed_calories, 1)
    remaining_protein = max(user.protein_goal - consumed_protein, 1)
    remaining_carbs = max(user.carbs_goal - consumed_carbs, 1)
    remaining_fat = max(user.fat_goal - consumed_fat, 1)

    foods = db.query(models.Food).limit(500).all()

    suggestions = []

    for food in foods:

        calorie_score = max(0, 1 - abs(food.calories_per_100g - remaining_calories) / remaining_calories)
        protein_score = max(0, 1 - abs(food.protein_per_100g - remaining_protein) / remaining_protein)
        carb_score = max(0, 1 - abs(food.carbs_per_100g - remaining_carbs) / remaining_carbs)
        fat_score = max(0, 1 - abs(food.fat_per_100g - remaining_fat) / remaining_fat)

        score = (
            calorie_score * 40 +
            protein_score * 30 +
            carb_score * 20 +
            fat_score * 10
        )

        suggestions.append({
            "food_id": food.food_id,
            "food_name": food.food_name,
            "match": round(score)
        })

    suggestions.sort(key=lambda x: x["match"], reverse=True)

    return suggestions[:5]

class GoalModeRequest(BaseModel):
    user_id: int
    goal_mode: bool


@app.post("/toggle-goal-mode")
def toggle_goal(data: ToggleGoalRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(models.User.id == data.user_id).first()

    user.goal_mode = data.enabled

    db.commit()

    return {"goal_mode": user.goal_mode}


class EditProfileRequest(BaseModel):
    user_id: int
    full_name: str
    age: int
    height: float
    weight: float

@app.post("/edit-profile")
def edit_profile(request: EditProfileRequest, db: Session = Depends(get_db)):

    user = db.query(models.User).filter(
        models.User.id == request.user_id
    ).first()

    details = db.query(models.UserDetails).filter(
        models.UserDetails.user_id == request.user_id
    ).first()

    if not user or not details:
        raise HTTPException(status_code=404, detail="User not found")

    user.full_name = request.full_name
    details.age = request.age
    details.height = request.height
    details.weight = request.weight

    db.commit()

    return {"message": "Profile updated successfully"}

@app.post("/upload-profile-photo/{user_id}")
async def upload_profile_photo(
    user_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):

    file_location = f"profile_images/{user_id}_{file.filename}"

    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    user = db.query(models.User).filter(models.User.id == user_id).first()

    user.profile_photo = file_location

    db.commit()

    return {
        "message": "Profile photo uploaded",
        "image_url": file_location
    }





@app.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
   
    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    details = db.query(models.UserDetails).filter(
        models.UserDetails.user_id == user_id
    ).first()

    return {
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "age": details.age if details else None,
        "height": details.height if details else None,
        "weight": details.weight if details else None,
        "goal_mode": user.goal_mode,
        "name": user.full_name,
        "image": user.profile_photo
    }

@app.get("/search-food")
def search_food(query: str, db: Session = Depends(get_db)):

    foods = db.query(models.Food)\
        .filter(models.Food.food_name.ilike(f"%{query}%"))\
        .group_by(models.Food.food_name)\
        .limit(20)\
        .all()

    results = []

    for food in foods:

        results.append({
            "food_id": food.food_id,
            "food_name": food.food_name,
            "unit_type": food.unit_type,
            "avg_weight": food.avg_weight
        })

    return results

from datetime import datetime

@app.get("/daily-food-logs/{user_id}/{date}")
def get_daily_food_logs(user_id: int, date: str, db: Session = Depends(get_db)):

    selected_date = datetime.strptime(date, "%Y-%m-%d").date()

    logs = db.query(models.FoodLog).filter(
        models.FoodLog.user_id == user_id,
        models.FoodLog.log_date == selected_date
    ).order_by(models.FoodLog.log_time).all()

    results = []

    for log in logs:
        results.append({
            "log_id": log.log_id,
            "food_name": log.food_name,
            "grams": log.grams,
            "calories": log.calories,
            "protein": log.protein,
            "carbs": log.carbs,
            "fat": log.fat,
            "fiber": log.fiber,
            "time": log.log_time.strftime("%H:%M")
        })

    return results
class OwnFoodRequest(BaseModel):
    user_id: int
    food_name: str
    grams: float
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float

@app.post("/save-own-food")
def save_own_food(data: OwnFoodRequest, db: Session = Depends(get_db)):

    new_log = models.FoodLog(
        user_id=data.user_id,
        food_name=data.food_name,
        grams=data.grams,
        calories=data.calories,
        protein=data.protein,
        carbs=data.carbs,
        fat=data.fat,
        fiber=data.fiber,
        log_time = datetime.now().strftime("%I:%M %p")
    )

    db.add(new_log)
    db.commit()

    return {"message": "Food saved successfully"}

@app.post("/detect-food")
async def detect_food(file: UploadFile = File(...)):

    contents = await file.read()

    image = Image.open(io.BytesIO(contents))

    results = model(image)

    detected_food = None
    confidence = 0

    for r in results:
        for box in r.boxes:

            cls = int(box.cls[0])
            detected_food = model.names[cls]
            confidence = float(box.conf[0])

            break

    if detected_food is None:
        return {
            "message": "No food detected"
        }

    detected_food = detected_food.lower()

    nutrition = food_nutrition.get(detected_food)

    if nutrition:

        return {

            "food": detected_food,
            "confidence": confidence,

            "calories": nutrition["calories"],
            "protein": nutrition["protein"],
            "carbs": nutrition["carbs"],
            "fat": nutrition["fat"],
            "fiber": nutrition["fiber"]

        }

    else:

        return {

            "food": detected_food,
            "confidence": confidence,
            "message": "Nutrition not found"

        }

@app.post("/save-search")
def save_search(user_id: int, query: str, db: Session = Depends(get_db)):
    search = models.SearchHistory(
        user_id=user_id,
        search_text=query
    )

    db.add(search)
    db.commit()

    return {"message": "saved"}

@app.get("/recent-searches/{user_id}")
def recent_searches(user_id: int, db: Session = Depends(get_db)):

    results = db.query(models.SearchHistory)\
        .filter(models.SearchHistory.user_id == user_id)\
        .order_by(models.SearchHistory.created_at.desc())\
        .limit(3).all()

    return results