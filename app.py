import os
import requests
import pandas as pd
from dotenv import load_dotenv
from rnn_weather import WeatherLSTM

load_dotenv()

endpoint = 'https://frost.met.no/observations/v0.jsonld'
parameters = {
    'sources': 'SN18700,SN90450',
    'elements': 'mean(air_temperature P1D),sum(precipitation_amount P1D),mean(wind_speed P1D)',
    'referencetime': '2010-04-01/2010-04-03',
}

r = requests.get(endpoint, parameters, auth=(os.getenv("CLIENT_ID"),''))
json = r.json()

if r.status_code == 200:
    forecaster = WeatherLSTM(lookback_hours=1, feature_count=3)

    raw_data = forecaster.preprocess_json(json['data'])
    X_train, y_train = forecaster.create_sequences(raw_data)

    forecaster.build_model()
    forecaster.train(X_train, y_train, epochs=30)

    latest_history = raw_data[-24:] 
    next_temp = forecaster.forecast_next_hour(latest_history)

    print(f"Predicted temperature for next hour: {next_temp}°C")

else:
    print("Error! Returned status code %s" % r.status_code)
    print("Message: %s" % json['error']['message'])
    print("Reason: %s" % json['error']['reason'])