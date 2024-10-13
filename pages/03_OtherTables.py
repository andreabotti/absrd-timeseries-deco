# IMPORT LIBRARIES
from fn__libs_data import *
import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
from io import StringIO
from urllib.request import urlopen




####################################################################################
# PAGE CONFIG
from fn__page_header import create_page_header
create_page_header()



####################################################################################
##### FILE PATHS AND DATA LOAD
# Check if required session state variables are available
iso_cat__color_dict = st.session_state['POE_Unipol__CatColor_Dict']

if 'POE_Unipol__ISO_SEU_Dict' in st.session_state and \
   'POE_Unipol__SensorMatrix' in st.session_state and \
   'POE_Unipol__SensorData' in st.session_state:
    
    iso_seu_dict = st.session_state['POE_Unipol__ISO_SEU_Dict']
    df_meters_matrix =  st.session_state['POE_Unipol__SensorMatrix']
    METERS_DATA_HOURLY =    st.session_state['POE_Unipol__SensorData']

    # Extract unique floor values from the meter column names
    meter_columns = METERS_DATA_HOURLY.columns.tolist()
    floors = list(set([meter.split('_')[0] for meter in meter_columns]))

    # Sort the floors to display them nicely
    floors.sort()

else:
    st.error("Required session state variables are missing.")


# st.write(METERS_DATA_HOURLY)






####################################################################################
col_1,spacing, col_2 = st.columns([16,1,10])

col_1.dataframe(df_meters_matrix, use_container_width=True, height=900)

col_2.write(iso_seu_dict)

