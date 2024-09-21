import os
import streamlit as st
import requests
import google.generativeai as genai
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from dotenv import load_dotenv

# Accessing the secrets stored in TOML format
gemini_api_key = st.secrets["GEMINI"]["GEMINI_API_KEY"]
usda_api_key = st.secrets["USDA"]["USDA_API_KEY"]

# Configure Google Generative AI with the Gemini API
genai.configure(api_key=gemini_api_key)

# Set Streamlit page configuration
st.set_page_config(page_title="NutriMentor", page_icon=":robot:")
st.header("NutriMentor")

# Configure Google Generative AI with the Gemini API
api_key = os.getenv("GEMINI_API_KEY") # Load API key from .env file
usda_api_key = os.getenv("USDA_API_KEY") # Load USDA API key from .env file
if not api_key:
 st.error("Gemini API key not found. Please set it in the .env file.")
 st.stop()

if not usda_api_key:
 st.error("USDA API key not found. Please set it in the .env file.")
 st.stop()

genai.configure(api_key=api_key)

# Function to query USDA API for nutritional data
def get_nutritional_data(food_name):
 search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={food_name}&api_key={usda_api_key}"
 response = requests.get(search_url)
 data = response.json()

 if 'foods' in data and len(data['foods']) > 0:
  food_data = data['foods'][0] # Take the first result from the search
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
def init_model():
 # Load the PDF document
 loader = PyPDFLoader("Dietary_Guidelines_for_Americans-2020-2025.pdf")
 documents = loader.load()

 # Split the documents into chunks
 text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
 texts = text_splitter.split_documents(documents)

 # Generate embeddings
 embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

 # Specify a directory for ChromaDB to store data
 persist_directory = './chroma_db'

 # Create the vectorstore using Chroma
 db = Chroma.from_documents(
  documents=texts,
  embedding=embeddings,
  persist_directory=persist_directory
 )

 # Create a retriever interface
 retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 2})

 # Create a function to query the Gemini LLM
 def query_gemini(prompt):
  model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
  response = model.generate_content(prompt)
  return response.candidates[0].content.parts[0].text if response.candidates else "No response"

 # Return both retriever and the query function for LLM
 return retriever, query_gemini

# Initialize the QA model and store it in session state
if 'qa_model' not in st.session_state:
 st.session_state['retriever'], st.session_state['query_gemini'] = init_model()

# Collect user information
st.subheader("Please enter your personal information or use default values for testing:")

# Use default values for testing
default_age = 30
default_gender = "Male"
default_height = 175.0
default_weight = 75.0
default_activity_level = "Moderately active"
default_calories_burned = 3500 # Weekly average calories burned
default_steps_walked = 70000 # Weekly average steps
default_sleep_hours = 7.0
default_health_goals = "Lose 5 kg in 3 months"
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

 # Combine inputs into a prompt
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
 Nutritional Data for Foods Consumed Regularly:
 {nutritional_data}
 """

 # Display user information and nutritional data
 st.subheader("Your Information:")
 st.text(user_info)

 st.subheader("Nutritional Data for Foods:")
 st.write("\n\n".join(nutritional_data))

 # Combine user information and additional instructions into the query
 detailed_prompt = f"""
 Based on the following user information and USDA nutritional data, create a personalized meal plan that aligns with the Dietary Guidelines for Americans:

 User Information:
 {user_info}

 Please consider the user's age, gender, height, weight, activity level, weekly average calories burned, weekly average steps walked, sleep hours, health goals, dietary preferences, health conditions, and the list of foods they regularly consume.

 If the user consumes alcohol regularly and wants to include it in the meal plan, provide appropriate suggestions for low-calorie alcohol options (beer, wine) within the 15% calorie rule.
 
 Otherwise, suggest an alcohol-free meal plan focused on weight loss and liver health.

 Provide the meal plan in a structured format, including breakfast, lunch, dinner, and snacks for each day. Include portion sizes and nutritional information (calories, protein, fat, carbs) for each food item.

 Provide a summary at the end that lists the total calories, protein, fat, and carbs consumed per day. Also, list each food item with its respective nutritional information and portion size.
 """

 # Perform similarity search with the retriever (optional)
 results = st.session_state['retriever'].get_relevant_documents(detailed_prompt)

 # Use the Gemini API to generate a response based on the detailed prompt
 gemini_response = st.session_state['query_gemini'](detailed_prompt)

 # Display the assistant's response
 st.subheader("Personalized Meal Plan with Nutritional Information:")
 st.write(gemini_response)

 # Optionally, display related documents from the retriever
 st.write("Related Documents:", results)