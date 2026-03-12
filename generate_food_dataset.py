import pandas as pd
import random

foods = [
"Apple","Banana","Egg","Chicken Breast","Rice","Paneer","Milk","Curd","Butter",
"Bread","Chapati","Paratha","Idli","Dosa","Sambar","Upma","Poha","Biryani",
"Chicken Curry","Paneer Butter Masala","Dal Tadka","Rajma","Chole","Vegetable Curry",
"Oats","Cornflakes","Mango","Orange","Papaya","Pineapple","Watermelon","Grapes",
"Almonds","Cashews","Peanuts","Walnuts","Greek Yogurt","Protein Shake","Salad",
"Tomato","Potato","Onion","Carrot","Broccoli","Spinach","Cabbage","Cauliflower"
]

dataset = []

for i in range(5000):
    food = random.choice(foods)

    calories = round(random.uniform(40,400),2)
    protein = round(random.uniform(0,30),2)
    carbs = round(random.uniform(0,60),2)
    fat = round(random.uniform(0,30),2)
    fiber = round(random.uniform(0,10),2)

    if food in ["Egg","Apple","Banana","Idli","Chapati","Paratha"]:
        unit_type = "piece"
        avg_weight = random.randint(30,120)
    else:
        unit_type = "gram"
        avg_weight = 100

    dataset.append([
        food,calories,protein,carbs,fat,fiber,unit_type,avg_weight
    ])

df = pd.DataFrame(dataset,columns=[
"food_name",
"calories_per_100g",
"protein_per_100g",
"carbs_per_100g",
"fat_per_100g",
"fiber_per_100g",
"unit_type",
"avg_weight"
])

df.to_csv("foods_dataset.csv",index=False)

print("Dataset created successfully!")