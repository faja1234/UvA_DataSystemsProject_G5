import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

############################################################################################

import sqlite3
import geopandas as gpd
from shapely import wkt
import leafmap.foliumap as leafmap
import calendar
import pickle
from functions import predict_manual_damage, get_firestation_data

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
    <div style="display: flex; align-items: center; justify-content: space-between; background-color:{bar_color}; padding:10px; color:white;">
        <div style="display: flex; align-items: center;">
            <img src="{logo_url}" alt="Logo" style="height: 50px; width: 150px; margin-right: 10px;">
            <h1 style="color:white; margin: 0; line-height: 1; text-align:center;">{bar_text}</h1>
        </div>
        <div style="flex: 1;"></div>
    </div>
    """,
    unsafe_allow_html=True
)

# Create a horizontal container
horizontal_container = st.container()

# Inside the horizontal container, add your content
with horizontal_container:
    st.write("# Create A Manual Storm to Run a Simulation For")

# Create two columns
col1, col2 = st.columns([0.2,0.8], gap='large')

with col1:
    
    with st.form('Manual weather input', clear_on_submit=False, border=False):
    
        # List of months
        months = [
            "January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"
        ]

        # Dropdown for selecting a month
        month = st.selectbox("Select a Month", months)
        
        if month in ['October','November', 'December','January', 'February', 'March']:
            leaveson = 0
        else:
            leaveson = 1

        # Slider values for the manual storm variables 
        temperature = st.slider("Select Temperature (°C)", -10, 40, 15)
        rain = st.slider("Select Rainfall over past week (mm)", 0, 50, 15)
        windspeed = st.slider("Select Current Windspeed (m/s)", 0, 25, 10)
        windgusts = st.slider("Select Current Wind Gusts (m/s)", 0, 35, 15)
        pastwind = st.slider("Select Strong Wind Over Past 2 Days (m/s)", 0, 48, 3)
        pastwindavg = st.slider("Select Average Wind Over Past 2 Days (m/s)", 0, 25, 10)
        pastwindgusts = st.slider("Select Max Wind Over Past Day (m/s)", 0, 25, 5)


        # Display the button
        runsimulation = st.form_submit_button("Run Simulation")

        # Run the simulation code (put code to run the model here)
        if runsimulation:
            # Run simulation code with the variables from the sliders above
            # Save the result of the simulation as the map data in the session state
            st.session_state.manual_map_data = predict_manual_damage(leaveson, rain, windspeed, windgusts, pastwind, pastwindavg, pastwindgusts)
            

with col2:
    # If no simulation has been performed yet, show the default map of amsterdam
    m = leafmap.Map(center=(52.360, 4.886), zoom=12, google_map="ROADMAP")
    
    if "manual_map_data" not in st.session_state:
        pass
    
    # Otherwise show the last simulation data on the map
    else:
        prediction_gdf = st.session_state.manual_map_data

        m.add_data(data=prediction_gdf, 
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