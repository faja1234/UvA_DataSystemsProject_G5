import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

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
    # List of months
    months = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    ]

    # Dropdown for selecting a month
    month = st.selectbox("Select a Month", months)

    # List of wind directions
    wind_directions = [
        "North", "North-Northeast", "Northeast", "East-Northeast",
        "East", "East-Southeast", "Southeast", "South-Southeast",
        "South", "South-Southwest", "Southwest", "West-Southwest",
        "West", "West-Northwest", "Northwest", "North-Northwest"
    ]

    # Dropdown for selecting a wind direction
    selected_wind_direction = st.selectbox("Select Wind Direction", wind_directions)

    # Slider values for the manual storm variables 
    temperature = st.slider("Select Temperature (°C)", -10, 40, 15)
    rain = st.slider("Select Rainfall (mm)", 0, 50, 15)
    windspeed = st.slider("Select Windspeed (km/h)", 0, 120, 70)
    windgusts = st.slider("Select Wind Gusts (km/h)", 0, 150, 80)

    # Display the button
    runsimulation = st.button("Run Simulation", key="run_sim")

    # Run the simulation code
    if runsimulation:
        # code
        st.write("Simulation Complete!")

with col2:
    #Map
    map_data = pd.DataFrame(
        np.random.randn(300, 2) / [50, 50] + [52.377956, 4.897070],
        columns=['lat', 'lon'])
    st.map(map_data)
    # Checkbox for toggling the fire station area overlay
    firestationsoverlay = st.checkbox("Show Fire Stations?")