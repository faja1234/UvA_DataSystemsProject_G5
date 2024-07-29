import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime, date, timedelta
from functions import predict_future_damage, get_firestation_data, openmeteo_historical_data, openmeteo_forecast_data, openmeteo_predictors
import leafmap.foliumap as leafmap
import geopandas as gpd

st.set_page_config(
    layout="wide",
    page_title="Simulation",
    page_icon="👈",
)

#Sidebar text
st.sidebar.header("Simulation Page")

# Set the desired background color
background_color = "#D9D9D9"  
st.markdown(
    f"""
    <style>
        body {{
            background-color: {background_color};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Set the background color and text for the bar
bar_color = "#D0021B"  
bar_text = "Storm Damage Dashboard"
logo_url = "https://wesselopublicvalue.nl/wp-content/uploads/2019/07/brandweer.png"  
st.markdown(
    f"""
    <div style="display: flex; align-items: center; justify-content: space-between; background-color:{bar_color}; padding:10px; color:white; margin-bottom:10px;">
        <div style="display: flex; align-items: center;">
            <img src="{logo_url}" alt="Logo" style="height: 50px; width: 150px; margin-right: 10px;">
            <h1 style="color:white; margin: 0; line-height: 1; text-align:center;">{bar_text}</h1>
        </div>
        <div style="flex: 1;"></div>
    </div>
    """,
    unsafe_allow_html=True
)

# Load the weather forecast dataframe
startdate = date.today() - timedelta(days=8)
forecast_result = openmeteo_forecast_data()
hist_result = openmeteo_historical_data(start_date = startdate) 
df_complete = openmeteo_predictors(hist_result, forecast_result)
df_predictions = predict_future_damage(df_complete)

# Function to get or set the selected date in cache
@st.cache_data
def get_or_set_selected_date(selected_date=None):
    if selected_date is None:
        selected_date = datetime.now().date()
    return selected_date

# Function to get or set the selected time in cache
@st.cache_data
def get_or_set_selected_time(selected_time=None):
    if selected_time is None:
        selected_time = 0
    return selected_time

# Create a horizontal container
horizontal_container = st.container()

# Inside the horizontal container, add your content
with horizontal_container:
    
    # Create two columns
    col1, col2 = st.columns([0.2,0.8], gap='large')

    with col1:
        # Create the make report button
        createreport = st.button("📝 Create Report", key="report")

        # Run the make report code
        if createreport:
            # code
            st.write("Report Created!")

    with col2:
        # Data for the alpha value of the boxes
        data = [0.4,0.5,0.3,0.1,0.1,0.2,0.3,0.5,0.7,0.9,1,0.7]

        # Creation of a bar with blocks horizontally, each containing the time range and a color red with an alpha value based on the data
        block_html = ""
        words = ["0-2", "2-4", "4-6", "6-8", "8-10", "10-12", "12-14", "14-16", "16-18", "18-20", "20-22", "22-24"]

        for i in range(12):
            alpha = data[i]
            block_color = f"rgba(255, 0, 0, {alpha})"
            block_html += f'<div style="display: inline-block; width: 8.165%; height: 50px; margin: 1px; background-color: {block_color}; text-align: center; line-height: 50px;">{words[i]}</div>'

        st.write(block_html, unsafe_allow_html=True)


        # Create a slider for selecting the time of day
        selected_time = st.slider(f"Select the time of the day", 0, 24, step=1, value=get_or_set_selected_time())
        # Call the function to update the selected time in cache if it's changed
        if selected_time != get_or_set_selected_time():
            get_or_set_selected_time(selected_time)

# Create two columns
col1, col2 = st.columns([0.2,0.8], gap='large')

with col1:
    # Create the date picker
    selected_date = st.date_input("Pick a Date", min_value= datetime.now().date(), max_value = datetime.now().date() + timedelta(days=7),key="date_picker", format="DD/MM/YYYY")
    # Update the selected date in cache if it's changed
    if selected_date != get_or_set_selected_date():
        get_or_set_selected_date(selected_date)
    
    # Create the run simulation button
    runsimulation = st.button("Run Simulation", key="run_sim")

    # Run the simulation code
    if runsimulation:
        # code
        df_selected = df_predictions[df_predictions["date"] == selected_date]
        df_selected.drop(columns="date", inplace=True)
        gdf_selected = gpd.GeoDataFrame(df_selected, crs='epsg:28992')
        st.session_state.manual_map_data = gdf_selected
        st.write("Simulation Complete!")

    

with col2:
    # If no simulation has been performed yet, show the default map of amsterdam
    m = leafmap.Map(center=(52.360, 4.886), zoom=12, google_map="ROADMAP")
    
    if "manual_map_data" not in st.session_state:
        pass
    
    # Otherwise show the last simulation data on the map
    else:
        prediction_gdf = st.session_state.manual_map_data

        m.add_data(data=gdf_selected, 
                    column='building_proba',
                    cmap = 'Reds',
                    layer_name='Building damage prediction', 
                    info_mode='on_click') 
    
    # Checkbox for toggling the fire station area overlay
    firestationsoverlay = st.checkbox("Show Fire Stations?")
    
    if firestationsoverlay:
        db = "Code/data/model_data.sqlite"
        firestations, service_areas = get_firestation_data(db)
        
        m.add_gdf(firestations, layer_name='Firestations')
        m.add_gdf(service_areas, layer_name='Service area boundaries')
       
    m.to_streamlit()
    