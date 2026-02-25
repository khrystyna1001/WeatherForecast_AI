import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.preprocessing import MinMaxScaler
import joblib

class WeatherLSTM:
    def __init__(self, lookback_hours=24, feature_count=5):
        self.lookback = lookback_hours
        self.feature_count = feature_count
        self.scaler = MinMaxScaler()
        self.model = None

    def preprocess_json(self, response, training=False):
        hourly = response.Hourly()
        temp_2m = hourly.Variables(0).ValuesAsNumpy()

        df = pd.DataFrame({
            'temperature_2m': temp_2m
        })

        df_final = df.interpolate(method='linear').bfill().ffill()
        
        if training or not hasattr(self.scaler, "n_features_in_"):
            scaled_data = self.scaler.fit_transform(df_final)
        else:
            scaled_data = self.scaler.transform(df_final)
        return scaled_data
    
    def save_scaler(self, filename="scaler.pkg"):
        joblib.dump(self.scaler, filename)

    def load_scaler(self, filename="scaler.pkg"):
        self.scaler = joblib.load(filename)
    
    def create_sequences(self, data):
        X, y = [], []
        for i in range(len(data) - self.lookback):
            X.append(data[i : i + self.lookback])
            y.append(data[i + self.lookback, 0])
        return np.array(X), np.array(y)
    
    def build_model(self):
        inputs = layers.Input(shape=(self.lookback, self.feature_count))

        x = layers.LSTM(64, return_sequences=True, activation='tanh')(inputs)
        x = layers.Dropout(0.2)(x)

        x = layers.LSTM(32, return_sequences=False, activation='tanh')(x)

        x = layers.Dense(16, activation='relu')(x)
        outputs = layers.Dense(1)(x)

        self.model = Model(inputs, outputs)
        self.model.compile(optimizer='adam', loss='mse', metrics=['mae'])
        print('Model Initialized')
    
    def train(self, X, y, epochs=20, batch_size=32):
        return self.model.fit(X, y, epochs=epochs, batch_size=batch_size, validation_split=0.1)
    
    def forecast_next_hour(self, scaled_data):
        last_window = scaled_data[-self.lookback:]
    
        prediction_input = last_window[np.newaxis, ...]
        prediction_scaled = self.model.predict(prediction_input)
        
        dummy = np.zeros((1, self.feature_count))
        dummy[0, 0] = prediction_scaled[0, 0]
        prediction_final = self.scaler.inverse_transform(dummy)[0, 0]

        return prediction_final
    
    def forecast_date(self, scaled_data, target_date):
        now = pd.Timestamp.now(tz='UTC')
        target = pd.to_datetime(target_date, utc=True)
        
        diff_seconds = (target - now).total_seconds()
        hours_to_predict = int(diff_seconds // 3600)

        if hours_to_predict <= 0:
            last_val_scaled = scaled_data[-1, 0]
            dummy = np.zeros((1, self.feature_count))
            dummy[0, 0] = last_val_scaled
            return self.scaler.inverse_transform(dummy)[0, 0]
        
        current_window = scaled_data[-self.lookback:].copy()
        last_prediction_scaled = scaled_data[-1, 0]

        for _ in range(hours_to_predict):
            prediction_input = current_window[np.newaxis, ...]
            pred_scaled = self.model.predict(prediction_input, verbose=0)

            new_row = np.zeros((1, self.feature_count))
            new_row[0][0] = pred_scaled[0, 0]

            current_window = np.append(current_window[1:], new_row, axis=0)
            last_prediction_scaled = pred_scaled[0, 0]
        
        dummy = np.zeros((1, self.feature_count))
        dummy[0, 0] = last_prediction_scaled
        prediction_final = self.scaler.inverse_transform(dummy)[0, 0]

        return prediction_final
    
    def save_csv(self, response):
        hourly = response.Hourly()
        
        time_index = pd.date_range(
            start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
            end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
            freq=pd.Timedelta(seconds=hourly.Interval()),
            inclusive="left"
        )
        
        temp_values = hourly.Variables(0).ValuesAsNumpy()
        
        data = []
        for i in range(len(temp_values)):
            data.append({
                'sourceId': 'Open-Meteo-API',
                'referenceTime': time_index[i],
                'elementId': 'temperature_2m',
                'value': temp_values[i],
                'unit': 'Celsius',
                'timeOffset': response.UtcOffsetSeconds()
            })

        df = pd.DataFrame(data)
        features = ['sourceId', 'referenceTime', 'elementId', 'value', 'unit', 'timeOffset']
        
        df = df[features]
        filename = "data.csv"
        df.to_csv(filename, index=False)
        print(f"Successfully saved {filename}")
