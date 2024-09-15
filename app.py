import os
import streamlit as st
import requests
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set Streamlit page configuration
st.set_page_config(page_title="NutriMentor", page_icon=":robot:")
st.header("NutriMentor")

# Configure Google Generative AI with the Gemini API
api_key = os.getenv("GEMINI_API_KEY")  # Load API key from .env file
if not api_key:
    st.error("Gemini API key not found. Please set it in the .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Your USDA API Key
usda_api_key = os.getenv("USDA_API_KEY")  # Load USDA API key from .env file
if not usda_api_key:
    st.error("USDA API key not found. Please set it in the .env file.")
    st.stop()

# Function to query USDA API for nutritional data
def get_nutritional_data(food_name):
    search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={usda_api_key}"
    response = requests.get(search_url)
    data = response.json()

    if 'foods' in data and len(data['foods']) > 0:
        food_data = data['foods'][0]  # Take the first result from the search
        food_name = food_data.get("description", food_name)
        serving_size = food_data.get("servingSize", 100)
        serving_size_unit = food_data.get("servingSizeUnit", "g")
        food_nutrients = food_data.get("foodNutrients", [])

        nutrients = {}
        for nutrient in food_nutrients:
            nutrient_name = nutrient.get("nutrientName")
            unit_name = nutrient.get("unitName")
            value = nutrient.get("value")
            nutrients[nutrient_name] = f"{value} {unit_name}"

        return {
            "food_name": food_name,
            "serving_size": serving_size,
            "serving_size_unit": serving_size_unit,
            "nutrients": nutrients
        }
    else:
        return None

# Function to initialize the model
def query_gemini(prompt):
    model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
    response = model.generate_content(prompt)
    return response.candidates[0].content.parts[0].text if response.candidates else "No response"

# Collect user information
st.subheader("Please enter your personal information or use default values for testing:")

# Use default values for testing
default_age = 24
default_gender = "Male"
default_height = 173.0
default_weight = 127.0
default_activity_level = "Moderately active"
default_calories_burned = 3500  # Weekly average calories burned
default_steps_walked = 4000  # Weekly average steps
default_sleep_hours = 7.0
default_health_goals = "Lose 15 kg in 3 months"
default_dietary_preferences = "Non-vegetarian"
default_health_conditions = "None"
default_is_alcoholic = False

# User inputs (with default values)
age = st.number_input("Age", min_value=0, max_value=120, value=default_age, step=1)
gender = st.selectbox("Gender", ["Male", "Female", "Other"], index=0)
height = st.number_input("Height (cm)", min_value=0.0, value=default_height, step=0.1)
weight = st.number_input("Weight (kg)", min_value=0.0, value=default_weight, step=0.1)
activity_level = st.selectbox("Activity Level", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"], index=2)

# Simulate weekly averages for health data
calories_burned = st.number_input("Weekly Average Calories Burned (from Health App)", min_value=0, value=default_calories_burned, step=1)
steps_walked = st.number_input("Weekly Average Steps Walked (from Health App)", min_value=0, value=default_steps_walked, step=1)
sleep_hours = st.number_input("Average Daily Sleep Hours (from Health App)", min_value=0.0, value=default_sleep_hours, step=0.1)
health_goals = st.text_input("Health Goals", value=default_health_goals)
dietary_preferences = st.text_input("Dietary Preferences", value=default_dietary_preferences)
health_conditions = st.text_input("Health Conditions", value=default_health_conditions)
is_alcoholic = st.checkbox("Do you consume alcohol regularly?", value=default_is_alcoholic)

# Option for including alcohol in the meal plan
if is_alcoholic:
    st.warning("Drinking alcohol may impact your weight loss journey. Would you still like to include alcohol in your meal plan?")
    include_alcohol = st.radio("Include alcohol in the meal plan?", ["Yes", "No"], index=1)
else:
    include_alcohol = "No"

# User inputs their regular food preferences
user_food_list = st.text_area("Enter the list of foods you eat regularly (separated by commas)", "chicken, rice, eggs, fish")

if st.button("Generate Meal Plan"):
    # Get nutritional data for each food
    nutritional_data = []
    for food in user_food_list.split(","):
        food = food.strip().lower()
        data = get_nutritional_data(food)
        if data:
            nutrients = "\n".join([f"{nutrient}: {value}" for nutrient, value in data["nutrients"].items()])
            nutritional_data.append(f"**{data['food_name']}** ({data['serving_size']} {data['serving_size_unit']}):\n{nutrients}")
        else:
            nutritional_data.append(f"**{food.capitalize()}**: Nutritional information not found.")

    # Display user information and nutritional data
    st.subheader("Your Information:")
    user_info = f"""
    Age: {age}
    Gender: {gender}
    Height: {height} cm
    Weight: {weight} kg
    Activity Level: {activity_level}
    Weekly Average Calories Burned: {calories_burned} kcal
    Weekly Average Steps Walked: {steps_walked}
    Average Daily Sleep Hours: {sleep_hours}
    Health Goals: {health_goals}
    Dietary Preferences: {dietary_preferences}
    Health Conditions: {health_conditions}
    Alcoholic: {"Yes" if is_alcoholic else "No"}
    Include Alcohol: {include_alcohol}
    Regular Foods: {user_food_list}
    """
    st.text(user_info)

    st.subheader("Nutritional Data for Foods:")
    st.write("\n\n".join(nutritional_data))

    detailed_prompt = f"""
User Information:
{user_info}

Nutritional Data for Foods Consumed Regularly:
{nutritional_data}

Instructions for Generating a Consistent Meal Plan:
Based on the American Dietary Guidelines and the user's personal information, create a personalized meal plan with the following specifications:

Daily Calorie Intake:

Set a daily calorie target for weight loss, adjusted based on the user's activity level and health goals. Create a daily caloric deficit while ensuring the user's nutrient needs are met.
If alcohol is included, ensure it follows the American Dietary Guidelines by allocating no more than 15% of total daily calories to low-calorie alcohol options.
Nutrient Distribution (from American Dietary Guidelines):

Distribute daily calorie intake using the macronutrient ranges from the American Dietary Guidelines:
Protein: 10-35% of total calories
Fat: 20-35% of total calories
Carbohydrates: 45-65% of total calories
Provide the total calories, protein, fat, and carbohydrates consumed per day in the meal plan summary.
Meal Plan Structure:

Create a 7-day meal plan with breakfast, lunch, dinner, and snacks each day.
List exact portion sizes for each meal, and provide the following nutritional breakdown for each food item:
Calories
Protein (grams)
Fat (grams)
Carbohydrates (grams)
Food Choices:

Prioritize foods regularly consumed by the user, as provided in the nutritional data.
Ensure the meal plan adheres to the user's dietary preferences and health conditions. Avoid foods they cannot consume.

Edge Case Considerations:
1. Avoid high-calorie, low-nutrient foods (e.g., processed snacks, sugary drinks).
2. Limit foods high in simple carbohydrates or added sugars to avoid hindering weight loss.
3. Avoid or limit foods high in saturated fats or trans fats to improve heart health and manage weight.
4. For users with health conditions (e.g., diabetes, hypertension), limit high-sugar or high-sodium foods to avoid exacerbating their conditions.
5. Ensure appropriate portion sizes to support the user's weight loss and health goals.
6. Avoid extreme macronutrient imbalances (e.g., excessive protein or too many carbs) that may conflict with dietary needs.
7. Restrict foods with high glycemic index for users managing blood sugar levels (e.g., white bread, refined sugars).
8. Eliminate foods that conflict with any provided allergies or dietary restrictions.
9. If the user consumes alcohol, include low-calorie alcohol options within the 15% calorie rule or suggest alternatives that will not hinder weight loss.
10. Prioritize nutrient-dense whole foods over processed options.

Alcohol Consideration (if applicable):

If the user consumes alcohol, include low-calorie alcohol options that follow the 15% calorie rule from the American Dietary Guidelines.
For alcohol-free plans, focus on foods that promote liver health and support the user's weight loss goals.
Consistency and Guidelines:

Follow the American Dietary Guidelines to ensure that the meals are balanced, nutrient-dense, and consistent across similar user profiles.
Maintain the same structure and rules for the meal plan, even if the food items change based on the user's preferences.
Final Summary:

Provide a daily summary for each day, listing the total calories, protein, fat, and carbohydrates consumed across all meals.
Include a table of food items used in the plan, showing their portion size and corresponding nutritional information.
    """




    # Query the Gemini LLM
    gemini_response = query_gemini(detailed_prompt)

    # Display the meal plan generated by Gemini
    st.subheader("Personalized Meal Plan with Nutritional Information:")
    st.write(gemini_response)