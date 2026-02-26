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
from datetime import date, timedelta, datetime, time

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
    forecaster.train(X_train, y_train, epochs=25)
    print("Model ready!")

@app.get("/predict/{base_date}")
async def predict(base_date: date, view_type: str = Query("today")):
    if base_date < date.today():
        raise HTTPException(status_code=400, detail="Cannot predict a past date")
    try:
        response = get_weather_data() 
        current_raw_data = forecaster.preprocess_json(response)
        predictions = []

        if view_type == "today":
            for i in range(1, 13):
                actual_temp = forecaster.forecast_next_hour(current_raw_data)
                pred_dt = datetime.combine(base_date, datetime.now().time()) + timedelta(hours=i)
                
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
                new_row[0, 0] = forecaster.scaler.transform([[actual_temp]])[0, 0]
                current_raw_data = np.append(current_raw_data, new_row, axis=0)

        else:
            for i in range(1, 8):
                target_dt = datetime.combine(base_date + timedelta(days=i), time(12, 0))
                
                actual_temp = forecaster.forecast_date(current_raw_data, target_dt)
                
                new_row = np.zeros((1, forecaster.feature_count))
                new_row[0, 0] = forecaster.scaler.transform([[actual_temp]])[0, 0]
                current_raw_data = np.append(current_raw_data, new_row, axis=0)

                suffix = get_date_suffix(target_dt.day)
                predictions.append({
                    "date": target_dt.strftime("%Y-%m-%d"),
                    "time": f"{actual_temp:.1f}",
                    "display_time": target_dt.strftime(f"%A %d{suffix}"),
                    "temp": f"{actual_temp:.1f}°",
                    "status": "Sunny",
                    "icon": "sun"
                })

        return predictions
    except Exception as e:
        print(f"Internal Server Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)