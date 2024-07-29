import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

st.set_page_config(
    layout="wide",
    page_title="Hello",
    page_icon="👋",
)


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

st.write("# Welcome to the Storm Damage Dashboard! 👋")

st.sidebar.success("Select a weather type input above.")