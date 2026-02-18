import os
import numpy as np
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import openmeteo_requests
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv
from rnn_weather import WeatherLSTM
from datetime import datetime, timedelta

def get_date_suffix(day):
    if 11 <= day <= 13:
        return 'th'
    else:
        return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

forecaster = WeatherLSTM(lookback_hours=24, feature_count=1)

def get_weather_data():
    endpoint = os.getenv('URL')
    parameters = {
        'latitude': 52.52,
        'longitude': 13.41,
        'hourly': 'temperature_2m',
    }
    responses = openmeteo.weather_api(endpoint, params=parameters)
    return responses[0]

@app.on_event("startup")
def train_model():
    response = get_weather_data()
    raw_data = forecaster.preprocess_json(response)
    X_train, y_train = forecaster.create_sequences(raw_data)
    forecaster.build_model()
    forecaster.train(X_train, y_train, epochs=5)
    print("Model ready!")

@app.get("/predict")
async def predict(view_type: str = Query("today")):
    response = get_weather_data()
    raw_data = forecaster.preprocess_json(response)
    
    predictions = []
    base_date = datetime(2027, 2, 15, 9, 0, 0) 
    
    if view_type == "today":
        current_window = raw_data[-24:]
        for i in range(12):
            next_val = forecaster.forecast_next_hour(current_window)
            
            pred_dt = base_date + timedelta(hours=i)
            suffix = get_date_suffix(pred_dt.day)
            formatted_time = pred_dt.strftime(f"%A %d{suffix} %Y, %H:%M:%S")
            
            predictions.append({
                "time": formatted_time,
                "temp": f"{next_val:.1f}°",
                "status": "Raining",
                "icon": "rain"
            })

            new_row = forecaster.scaler.transform([[next_val]])
            current_window = np.append(current_window[1:], new_row, axis=0)
            
    return predictions

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)