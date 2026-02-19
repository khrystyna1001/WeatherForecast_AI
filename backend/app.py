import os
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import openmeteo_requests
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv
from rnn_weather import WeatherLSTM
from datetime import date, timedelta, datetime

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
        'latitude': os.getenv('LATITUDE'),
        'longitude': os.getenv('LONGITUDE'),
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

@app.get("/predict/{base_date}")
async def predict(base_date: date, view_type: str = Query("today")):
    try:
        print(base_date, type(base_date))
        response = get_weather_data() 
        current_raw_data = forecaster.preprocess_json(response)
        
        hours_to_predict = 12 if view_type == "today" else 168
        current_dt = datetime.combine(base_date, datetime.min.time())
        current_window = current_raw_data[-24:].copy()
    
        predictions = []

        for i in range(hours_to_predict):
            prediction_input = current_window[np.newaxis, ...]
            pred_scaled = forecaster.model.predict(prediction_input, verbose=0)
            
            dummy = np.zeros((1, forecaster.feature_count))
            dummy[0, 0] = pred_scaled[0, 0]
            actual_temp = forecaster.scaler.inverse_transform(dummy)[0, 0]
            
            pred_dt = current_dt + timedelta(hours=i)
            
            should_append = True if view_type == "today" else (i % 3 == 0)
            
            if should_append:
                suffix = get_date_suffix(pred_dt.day)
                predictions.append({
                    "date": pred_dt.strftime("%Y-%m-%d"),
                    "time": pred_dt.strftime("%H:%M"),
                    "display_time": pred_dt.strftime(f"%A %d{suffix}, %H:%M"),
                    "temp": f"{actual_temp:.1f}°",
                    "status": "Partly Cloudy",
                    "icon": "cloud"
                })

            new_row = np.zeros((1, forecaster.feature_count))
            new_row[0, 0] = pred_scaled[0, 0]
            current_window = np.append(current_window[1:], new_row, axis=0)
            
        return predictions
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)