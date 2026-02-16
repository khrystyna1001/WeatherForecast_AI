import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, Model
from sklearn.preprocessing import MinMaxScaler

class WeatherLSTM:
    def __init__(self, lookback_hours=24, feature_count=5):
        self.lookback = lookback_hours
        self.feature_count = feature_count
        self.scaler = MinMaxScaler()
        self.model = None

    def preprocess_json(self, json_data):
        df = pd.json_normalize(
            json_data, 
            record_path=['observations'], 
            meta=['referenceTime']
        )

        df_pivot = df.pivot_table(
            index=['referenceTime', 'timeOffset'], 
            columns='elementId', 
            values='value',
            aggfunc='mean'
        )

        df_pivot = df_pivot.reset_index()
        df_pivot['referenceTime'] = pd.to_datetime(df_pivot['referenceTime'])
        df_pivot = df_pivot.sort_values(['referenceTime', 'timeOffset'])
        
        df_final = df_pivot.drop(columns=['referenceTime', 'timeOffset'])
        df_final = df_final.interpolate(method='linear').bfill().ffill()
        
        scaled_data = self.scaler.fit_transform(df_final)
        self.feature_count = df_final.shape[1]
        
        print(f"Success! Data Shape: {df_final.shape}")
        return scaled_data
    
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
    
    def save_csv(self, data):
        df = pd.DataFrame(data)
        features = ['sourceId','referenceTime','elementId','value','unit','timeOffset']
        df = df[features]
        filename = "data.csv"
        df.to_csv(filename)
