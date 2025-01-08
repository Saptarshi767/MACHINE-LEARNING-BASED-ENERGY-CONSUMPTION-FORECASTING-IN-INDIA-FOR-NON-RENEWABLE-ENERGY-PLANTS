import streamlit as st
import pandas as pd
import joblib
import numpy as np
from datetime import datetime

# Load the trained model and state encoder
model = joblib.load('random_forest_model.pkl')
state_encoder = joblib.load('state_encoder.pkl')

# Function to predict usage based on input state and date
def predict_usage(state, date_input):
    # Extract day, month, year, and other features from the date_input
    try:
        if date_input.lower() == 'day':
            date_str = st.date_input("Enter Date", value=datetime.today()).strftime("%d/%m/%Y")
            day, month, year = [int(x) for x in date_str.split('/')]

        elif date_input.lower() == 'month':
            month = st.selectbox("Select Month", [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
            year = st.number_input("Enter Year", min_value=2000, max_value=2100, value=datetime.today().year)
            day = 1  # Placeholder day value

        elif date_input.lower() == 'year':
            year = st.number_input("Enter Year", min_value=2000, max_value=2100, value=datetime.today().year)
            month = 1  # Placeholder month value
            day = 1  # Placeholder day value

        else:
            st.error("Invalid date input. Please select Day, Month, or Year")
            return

        # Calculate the quarter based on the month
        quarter = (month - 1) // 3 + 1

        # Encode state using LabelEncoder
        state_encoded = state_encoder.transform([state])[0]

        # Prepare input features as a dictionary
        features_dict = {
            'Day': day,
            'Month': month,
            'Year': year,
            'StateEncoded': state_encoded,
            'Weekday': datetime(year, month, day).weekday(),
            'IsWeekend': 1 if (datetime(year, month, day).weekday() >= 5) else 0,
            'Quarter': quarter,
            'latitude': 0,  # Placeholder, add real latitude if available
            'longitude': 0  # Placeholder, add real longitude if available
        }

        # Convert the dictionary into a DataFrame
        features_df = pd.DataFrame([features_dict])

        # Make prediction
        predicted_usage = model.predict(features_df)[0]
        return predicted_usage, month, year

    except Exception as e:
        st.error(f"Error: {e}")
        return None, None, None

# Title of the app
st.title("Energy Consumption Prediction")

# Create a dropdown for state selection
state_list = [
    "Punjab", "Haryana", "Rajasthan", "Delhi", "UP", "Uttarakhand", "HP", "J&K", 
    "Chandigarh", "Chhattisgarh", "Gujarat", "MP", "Maharashtra", "Goa", "DNH", 
    "Andhra Pradesh", "Telangana", "Karnataka", "Kerala", "Tamil Nadu", "Pondy"
]

# User selects a state from dropdown
selected_state = st.selectbox("Select a state", state_list)

if selected_state:
    st.write(f"State selected: {selected_state}")

    # Allow the user to select a date input type
    date_input = st.radio("Select input type", ['Day', 'Month', 'Year'])

    # Display predicted result when the user inputs data
    predicted_value, month, year = predict_usage(selected_state, date_input)

    if predicted_value is not None:
        st.write(f"Predicted Usage: {predicted_value-100:.2f} kWh")
