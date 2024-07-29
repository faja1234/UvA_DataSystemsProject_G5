import pandas as pd
import geopandas as gpd
import streamlit as st
import pickle
import sqlite3
from shapely import wkt
import calendar
from streamlit_folium import st_folium

# Load pre-trained models

# Building damage model
with open('Code/models/clf_building_logistic.pickle', 'rb') as handle:
    building_pipeline = pickle.load(handle)
    
with open('Code/models/clf_tree_logistic.pickle', 'rb') as handle:
    tree_pipeline = pickle.load(handle)
    
# Load AMS grid from database

with sqlite3.connect('Code/data/model_data.sqlite') as conn:
    amsgrid = pd.read_sql('SELECT * FROM AMS_grid_blocks', conn)

# Convert geometry text to shapely objects
amsgrid['geometry'] = amsgrid['geometry'].apply(wkt.loads)

# TODO: Load points of interest to apply weighting factors

# Function to predict storm damage

# Set categorical variables
from pandas.api.types import CategoricalDtype
cat_type_dir = CategoricalDtype(categories=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'], ordered=False)
cat_type_hour = CategoricalDtype(categories=range(24), ordered=False)
cat_type_month = CategoricalDtype(categories=[calendar.month_name[i+1] for i in range(12)], ordered=False)

# Define function here
@st.cache_data
def predict_damage(hour, month, wind_direction, wind_speed_average, wind_speed_maximum):

    # Copy grid data to prediction df
    prediction_df = amsgrid.copy()

    # Add weather data to the prediction df
    weather_columns = [
        'Hour', 
        'month', 
        'Wind direction (direction)', 
        'Average hourly wind speed (m/s)', 
        'Maximum hourly wind speed (m/s)']

    prediction_df[weather_columns] = [hour, month, wind_direction, wind_speed_average, wind_speed_maximum]

    prediction_df['Wind direction (direction)'] = prediction_df['Wind direction (direction)'].astype(cat_type_dir)
    prediction_df['Hour'] = prediction_df['Hour'].astype(cat_type_hour)
    prediction_df['month'] = prediction_df['month'].astype(cat_type_month)

    # Set dummy variables
    for column in ['Wind direction (direction)', 'Hour', 'month']:
        prediction_df = pd.concat([prediction_df, pd.get_dummies(prediction_df[column])], axis=1)
        prediction_df = prediction_df.drop(columns=[column])
    prediction_df.columns = prediction_df.columns.astype(str)

    # Define the column names that were used for the model fitting
    building_columns = building_pipeline.feature_names_in_
    tree_columns = tree_pipeline.feature_names_in_

    # Run model prediction
    prediction_df['building_proba'] = building_pipeline.predict_proba(prediction_df[building_columns])[:,1]
    prediction_df['tree_proba'] = tree_pipeline.predict_proba(prediction_df[tree_columns])[:,1]
    prediction_df['total_proba'] = prediction_df['building_proba'] + prediction_df['tree_proba'] ## NEEDS TO BE FIXED (events not independent)

    # Convert to geopandas
    prediction_gdf = gpd.GeoDataFrame(prediction_df, crs='epsg:28992')
    
    return prediction_gdf


##############################

# Create color map based on color and transparancy

import branca.colormap as cm
custom_cmap = cm.LinearColormap(colors=['white','red'], vmin=0, vmax=1.5)

# SET parameters here
hour = 15
month = 'February'
wind_direction = 'NE'
wind_speed_average = 20
wind_speed_maximum = 25

# Run prediction
prediction_damage = predict_damage(hour, month, wind_direction, wind_speed_average, wind_speed_maximum)

# Select damage of interest
damage = 'total_proba'

# Remove cells with probability less than 0.05
prediction_damage = prediction_damage[prediction_damage[damage]>0.05]

m1 = prediction_damage[['Average hourly wind speed (m/s)', 'Maximum hourly wind speed (m/s)', 'average_building_age',
    'building_area', 'trees', 'geometry', 'Verzorgingsgebied', 'building_proba', 'tree_proba', 'total_proba']].explore(
            damage,
            legend=True, 
            cmap=custom_cmap,
            tiles='cartodbpositron',
            style_kwds={'weight':0.1, 'opacity':0.4, 'fillOpacity':0.8}, 
            tooltip=False, 
            popup=True)

# Call to render Folium map in Streamlit, but don't get any data back
# from the map (so that it won't rerun the app when the user interacts)
st_folium(m1, width=800, height=600, returned_objects=[])

# m2 = prediction_gdf[['Average hourly wind speed (m/s)', 'Maximum hourly wind speed (m/s)', 'average_building_age',
#        'building_area', 'trees', 'geometry', 'building_proba', 'tree_proba', 'total_proba']].explore(
#            'tree_proba',
#             legend=True, 
#             cmap='viridis', 
#             tiles='cartodbpositron', 
#             style_kwds={'weight':0.1, 'opacity':0.4, 'fillOpacity':0.8}, 
#             tooltip=False, 
#             popup=True)
# st_folium(m2)
       
