import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
import joblib
from datetime import datetime, timedelta

# Load the ARIMA model
model = joblib.load('energy_consumption_arima_model.joblib')

# Load and preprocess data
def load_data():
    data = pd.read_excel('final.xlsx')
    non_renewable_data = data[data['Type Of Station'].isin(['Gas', 'Nuclear', 'Thermal'])].copy()
    non_renewable_data['Date'] = pd.to_datetime(non_renewable_data['Date'])
    non_renewable_data = non_renewable_data.set_index('Date')

    # Ensure no duplicate dates per station
    non_renewable_data = non_renewable_data.groupby(['Station', 'Date']).sum()

    # Handle missing values
    def fill_missing_values(group):
        if group.index.name != 'Date':
            group = group.reset_index().set_index('Date')
        group = group.asfreq('D').fillna(0)
        if group['Declared Capability (MWh)'].eq(0).all():
            group['Declared Capability (MWh)'].fillna(0, inplace=True)
        else:
            group['Declared Capability (MWh)'] = group['Declared Capability (MWh)'].fillna(
                group['Declared Capability (MWh)'].rolling(window=7, min_periods=1).mean()
            )
        return group

    non_renewable_data = non_renewable_data.groupby('Station').apply(fill_missing_values)
    non_renewable_data.dropna(subset=['Declared Capability (MWh)'], inplace=True)

    # Aggregate data at the daily level
    daily_data = non_renewable_data.groupby('Date')['Declared Capability (MWh)'].sum()
    return daily_data


data = load_data()

def forecast_consumption(start_date, forecast_days):
    # Filter data up to the start_date
    filtered_data = data[:start_date]
    
    # Train ARIMA model
    model = ARIMA(filtered_data, order=(5, 1, 0))
    model_fit = model.fit()
    
    # Forecast for the next 'forecast_days' days
    forecast = model_fit.forecast(steps=forecast_days)
    forecast_dates = pd.date_range(start=start_date + timedelta(days=1), periods=forecast_days)
    
    forecast_series = pd.Series(forecast, index=forecast_dates)
    return forecast_series

st.title('Energy Consumption Forecast')

# User input as a single text field
user_input = st.text_input("Enter a date (YYYY-MM-DD), a month (YYYY-MM), or a year (YYYY):")

def process_input(input_text):
    try:
        # Try to parse as full date (YYYY-MM-DD)
        date_input = datetime.strptime(input_text, "%Y-%m-%d")
        return date_input, 'date'
    except ValueError:
        try:
            # Try to parse as year and month (YYYY-MM)
            month_input = datetime.strptime(input_text, "%Y-%m")
            return month_input, 'month'
        except ValueError:
            try:
                # Try to parse as year (YYYY)
                year_input = datetime.strptime(input_text, "%Y")
                return year_input, 'year'
            except ValueError:
                st.error("Invalid format! Please enter a valid date, month, or year (YYYY-MM-DD, YYYY-MM, or YYYY).")
                return None, None

if user_input:
    date_input, input_type = process_input(user_input)

    if date_input:
        if input_type == 'date':
            # For a specific date, forecast for the next week
            forecast_series = forecast_consumption(date_input, 7)

            st.write(f'Predicted Energy Consumption from {date_input.date()} to {(date_input + timedelta(days=7)).date()}:')
            st.write(forecast_series)

            # Plot the forecast
            plt.figure(figsize=(12, 6))
            plt.plot(forecast_series.index, forecast_series, color='red', linestyle='--', label='Forecasted Consumption')
            plt.xlabel('Date')
            plt.ylabel('Energy Consumption (MWh)')
            plt.title(f'Energy Consumption Forecast (Week after {date_input.date()})')
            plt.legend()
            st.pyplot()

        elif input_type == 'month':
            # For a month, show the trend for the entire month
            start_date = date_input.replace(day=1)
            end_date = datetime(date_input.year, date_input.month, pd.Timestamp(date_input.year, date_input.month, 1).days_in_month)

            # Display historical data and forecast for the selected month
            daily_data = data[start_date:end_date]
            forecast_series = forecast_consumption(end_date, 7)

            st.write(f'Energy Consumption Trend for {date_input.strftime("%B %Y")}:')
            st.write(daily_data)

            # Plot Historical and Forecast data
            plt.figure(figsize=(12, 6))
            plt.plot(daily_data.index, daily_data, label='Historical Consumption')
            plt.plot(forecast_series.index, forecast_series, color='red', linestyle='--', label='Next Week Forecast')
            plt.xlabel('Date')
            plt.ylabel('Energy Consumption (MWh)')
            plt.title(f'Energy Consumption Trend for {date_input.strftime("%B %Y")}')
            plt.legend()
            st.pyplot()

            # Show increase or decrease in consumption
            consumption_change = daily_data.diff().sum()
            if consumption_change > 0:
                st.write("Overall consumption increased during the month.")
            else:
                st.write("Overall consumption decreased during the month.")

        elif input_type == 'year':
            # For a year, show the trend for the entire year
            start_date = date_input.replace(month=1, day=1)
            end_date = date_input.replace(month=12, day=31)

            # Display historical data and forecast for the selected year
            yearly_data = data[start_date:end_date]
            forecast_series = forecast_consumption(end_date, 7)

            st.write(f'Energy Consumption Trend for {date_input.year}:')
            st.write(yearly_data)

            # Plot Historical and Forecast data
            plt.figure(figsize=(12, 6))
            plt.plot(yearly_data.index, yearly_data, label='Historical Consumption')
            plt.plot(forecast_series.index, forecast_series, color='red', linestyle='--', label='Next Week Forecast')
            plt.xlabel('Date')
            plt.ylabel('Energy Consumption (MWh)')
            plt.title(f'Energy Consumption Trend for {date_input.year}')
            plt.legend()
            st.pyplot()

            # Show increase or decrease in consumption
            consumption_change = yearly_data.diff().sum()
            if consumption_change > 0:
                st.write("Overall consumption increased during the year.")
            else:
                st.write("Overall consumption decreased during the year.")
