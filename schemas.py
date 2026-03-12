from pydantic import BaseModel

class ToggleGoalRequest(BaseModel):
    user_id: int
    goal_mode: bool


from pydantic import BaseModel

class GoalRequest(BaseModel):
    user_id: int
    calories: float
    protein: float
    carbs: float
    fat: float
    goal_type: str

class AIGoalRequest(BaseModel):
    user_id: int
    age: int
    weight: float
    height: float
    gender: str
    activity_level: str



class OwnFoodRequest(BaseModel):
    user_id: int
    food_name: str
    grams: float
    calories: float
    protein: float
    carbs: float
    fat: float
    fiber: float