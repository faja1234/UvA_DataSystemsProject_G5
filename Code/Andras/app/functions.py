import openmeteo_requests
import requests_cache
import pandas as pd
import numpy as np
from retry_requests import retry
import datetime as dt
import streamlit as st
import sqlite3
import geopandas as gpd
from shapely import wkt
import calendar
import pickle
from itertools import product

# Setup the Open-Meteo API client with cache and retry on error
cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
openmeteo = openmeteo_requests.Client(session = retry_session)

current_parameters = ["temperature_2m", "precipitation", "rain", "showers", "snowfall", 
                        "surface_pressure", "wind_speed_10m", "wind_direction_10m", 
                        "wind_gusts_10m"]

forecast_parameters = ["temperature_2m", "precipitation_probability", "precipitation", 
                        "rain", "showers", "snowfall", "snow_depth", "surface_pressure", 
                        "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", 
                        "soil_temperature_0cm", "soil_temperature_6cm", "soil_temperature_18cm", 
                        "soil_temperature_54cm", "soil_moisture_0_to_1cm", "soil_moisture_1_to_3cm", 
                        "soil_moisture_3_to_9cm", "soil_moisture_9_to_27cm", "soil_moisture_27_to_81cm"]

historical_parameters = ["temperature_2m", "precipitation", "rain", "snowfall", "snow_depth", 
                            "surface_pressure", "wind_speed_10m", "wind_direction_10m", "wind_gusts_10m", 
                            "soil_temperature_0_to_7cm", "soil_temperature_7_to_28cm", 
                            "soil_temperature_28_to_100cm", "soil_temperature_100_to_255cm", 
                            "soil_moisture_0_to_7cm", "soil_moisture_7_to_28cm", "soil_moisture_28_to_100cm", 
                            "soil_moisture_100_to_255cm"]



@st.cache_data
def openmeteo_historical_data(list_of_parameters=['precipitation', 'wind_speed_10m', 'wind_gusts_10m'], 
                              start_date = '2024-01-01', 
                              end_date = str(dt.date.today())):

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
    retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
    openmeteo = openmeteo_requests.Client(session = retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 52.374,
        "longitude": 4.890,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": list_of_parameters,
        "wind_speed_unit": "ms",
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    
    datetimes = {"timestamp": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s"),
    end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
    )}
    
    historical_data = pd.DataFrame(data = datetimes)
    
    # Forecast values. The order of variables needs to be the same as requested.
    for i,param in enumerate(list_of_parameters):
        historical_data[param] = hourly.Variables(i).ValuesAsNumpy()
        
    return historical_data

@st.cache_data
def openmeteo_forecast_data(list_of_parameters=['precipitation', 'wind_speed_10m', 'wind_gusts_10m'], past_days=0, future_days=16):

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 52.374,
        "longitude": 4.890,
        "hourly": list_of_parameters,
        "timezone": "Europe/Berlin",
        "forecast_days": future_days,
        "past_days": past_days
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    hourly = response.Hourly()
    
    datetimes = {"timestamp": pd.date_range(
    start = pd.to_datetime(hourly.Time(), unit = "s"),
    end = pd.to_datetime(hourly.TimeEnd(), unit = "s"),
    freq = pd.Timedelta(seconds = hourly.Interval()),
    inclusive = "left"
    )}
    
    forecast_data = pd.DataFrame(data = datetimes)
    
    # Forecast values. The order of variables needs to be the same as requested.
    for i,param in enumerate(list_of_parameters):
        forecast_data[param] = hourly.Variables(i).ValuesAsNumpy()
        
    return forecast_data
 
@st.cache_data
def convert_to_daily(result):

    # add column that transforms the timestamp in just the date
    result['date'] = result['timestamp'].dt.date

    # move column 'date' to the left of the dataframe (this is purely for aesthetic reasons)
    cols = list(result)
    cols.insert(0, cols.pop(cols.index('date')))
    result = result.loc[:, cols]    

    # group by date
    grouped_result = result.groupby('date')

    # average precipitation (grouped by date)
    avg_precipitation_daily = grouped_result["precipitation"].mean()

    # average wind speed (grouped by date)
    avg_windspeed_daily = grouped_result["wind_speed_10m"].mean()

    # max wind speed (grouped by date)
    max_windspeed_daily = grouped_result["wind_speed_10m"].max()

    # average strong wind (>15 m/s) (grouped by date)
    avg_strong_windspeed_daily = grouped_result["wind_speed_10m"].apply(lambda x: np.average(x > 15))

    # make a dataframe with the results
    df_results_daily = pd.DataFrame({'avg_precipitation': avg_precipitation_daily,
                            'avg_windspeed': avg_windspeed_daily,
                            'max_windspeed': max_windspeed_daily,
                            'avg_strong_windspeed': avg_strong_windspeed_daily})

    return df_results_daily

@st.cache_data
def openmeteo_predictors(hist_result, forecast_result):
    '''Prep data'''

    
    hist_result = hist_result.dropna()

    # find datetime of the last entry in the historical data
    last_entry=hist_result.index[-1]

    '''Forecast -> Hourly + Hourly Rolling'''

    # concatenating the past and future values

    df_complete = pd.concat([hist_result[['timestamp', 'precipitation', 'wind_speed_10m', 'wind_gusts_10m']],
                             forecast_result[['timestamp', 'precipitation', 'wind_speed_10m', 'wind_gusts_10m']]],
                             ignore_index=True)
    df_complete["date"] = df_complete["timestamp"].dt.date
    df_complete = df_complete.groupby("date").agg({"precipitation":"sum",
                                                   "wind_speed_10m":"mean",
                                                   "wind_gusts_10m":"max"}).reset_index()


    #rolling summary of the predictor values and separation of date, time
    df_complete["Precipitation past two week"] = df_complete["precipitation"].rolling(14).sum()
    df_complete["Average wind past three days"] = df_complete["wind_speed_10m"].rolling(3).mean()
    #df_complete["Strong wind past two days"] = df_complete["wind_speed_10m"].rolling(48).apply(lambda x: (x > 15).sum())
    #df_complete["Max wind past day"] = df_complete["wind_gusts_10m"].rolling(24).max()
    
    #df_complete["time"] = df_complete["timestamp"].dt.time
    df_complete["Leaves on or not"] = df_complete["date"].apply(lambda x: x.month in [4,5,6,7,8,9]).astype(int)
    df_complete.rename(columns={"wind_speed_10m":"Average hourly wind speed (m/s)",
                                "wind_gusts_10m":"Maximum hourly wind speed (m/s)"}, inplace=True)

    # remove all entries before the last entry of hist_result
    df_complete = df_complete[df_complete["date"] >= dt.date.today()]

    return df_complete


@st.cache_data
def get_firestation_data(database_path):
    
    # Load data from SQLite database
    with sqlite3.connect(database_path) as conn:
        firestation_data = pd.read_sql('SELECT * FROM Firestations', conn)
    
    # Select relevant columns
    firestations = firestation_data[['Service area', 'gemeente', 'Vehicle Count']]
    service_areas = firestation_data[['Service area', 'gemeente']]
    
    # Convert geometry from text to object
    firestations['geometry'] = firestation_data['Firestation location'].apply(wkt.loads)
    service_areas['geometry'] = firestation_data['Service area geometry'].apply(wkt.loads)
    
    firestations_gdf = gpd.GeoDataFrame(firestations, crs='epsg:28992')
    service_areas_gdf = gpd.GeoDataFrame(service_areas, crs='epsg:28992')
    
    return firestations_gdf, service_areas_gdf


@st.cache_data
def get_ams_base_grid_data(database_path):

    # Load data from SQLite database
    with sqlite3.connect(database_path) as conn:
        ams_grid_data = pd.read_sql('SELECT * FROM AMS_grid_blocks', conn)

    # Convert geometry from text to object
    ams_grid_data['geometry'] = ams_grid_data['geometry'].apply(wkt.loads)
    
    return ams_grid_data

@st.cache_data
def load_tree_damage_model(pickle_path):
    
    # Tree damage model    
    with open(pickle_path, 'rb') as handle:
        tree_pipeline = pickle.load(handle)
    
    return tree_pipeline
    
@st.cache_data
def load_building_damage_model(pickle_path):
    
    # Building damage model
    with open(pickle_path, 'rb') as handle:
        building_pipeline = pickle.load(handle)

    return building_pipeline

@st.cache_data
def predict_manual_damage(leaveson, past_rain, wind_speed_average, wind_speed_maximum, past_strong_wind, past_avg_wind, past_max_wind):
    
    # Copy grid data to prediction df
    prediction_df = get_ams_base_grid_data("Code/data/model_data.sqlite")

    # Add weather data to the prediction df
    weather_columns = [
        'Hour',
        'Leaves on or not',
        'Average hourly wind speed (m/s)', 
        'Maximum hourly wind speed (m/s)',
        'Precipitation past week',
        'Strong wind past two days',
        'Average wind past two days',
        'Max wind past day']

    prediction_df[weather_columns] = [12, leaveson, past_rain, wind_speed_average, wind_speed_maximum, past_strong_wind, past_avg_wind, past_max_wind]

    # Define the column names that were used for the model fitting
    building_pipeline = load_building_damage_model('Code/Andras/xgb_building_pipeline.pickle')
    tree_pipeline = load_building_damage_model('Code/Andras/xgb_tree_pipeline.pickle')
    
    building_columns = building_pipeline.feature_names_in_
    tree_columns = tree_pipeline.feature_names_in_

    # Run model prediction
    prediction_df['building_proba'] = building_pipeline.predict_proba(prediction_df[building_columns])[:,1]
    prediction_df['tree_proba'] = tree_pipeline.predict_proba(prediction_df[tree_columns])[:,1]
    prediction_df['total_proba'] = prediction_df['building_proba'] + prediction_df['tree_proba'] ## NEEDS TO BE FIXED (events not independent)

    # Convert to geopandas
    prediction_gdf = gpd.GeoDataFrame(prediction_df, crs='epsg:28992')
    
    return prediction_df

@st.cache_data
def predict_future_damage(forecast_df):
    # Copy grid data to prediction df
    grid_df = get_ams_base_grid_data("Code/data/model_data.sqlite")

    # Create a new DataFrame by combining the grid and weather forecasts
    all_combinations = list(product(range(len(grid_df)), range(len(forecast_df))))
    prediction_df = pd.DataFrame([grid_df.iloc[i[0]].tolist() + forecast_df.iloc[i[1]].tolist() for i in all_combinations],
                             columns=list(grid_df.columns) + list(forecast_df.columns))
    
    # Define the column names that were used for the model fitting
    building_pipeline = load_building_damage_model('Code/Andras/xgb_building_pipeline.pickle')
    tree_pipeline = load_building_damage_model('Code/Andras/xgb_tree_pipeline.pickle')
    
    building_columns = building_pipeline.feature_names_in_
    tree_columns = tree_pipeline.feature_names_in_

    # Run model prediction
    prediction_df['building_proba'] = building_pipeline.predict_proba(prediction_df[building_columns])[:,1]
    prediction_df['tree_proba'] = tree_pipeline.predict_proba(prediction_df[tree_columns])[:,1]
    prediction_df['total_proba'] = prediction_df['building_proba'] + prediction_df['tree_proba'] ## NEEDS TO BE FIXED (events not independent)

    # Convert to geopandas
    prediction_gdf = gpd.GeoDataFrame(prediction_df, crs='epsg:28992')

    return prediction_gdf


