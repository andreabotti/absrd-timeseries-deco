# IMPORT LIBRARIES
from fn__libs_data import *
from fn__libs_charts import *

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

if 'POE_Unipol__ISO_SEU_Dict' not in st.session_state and \
   'POE_Unipol__SensorMatrix' not in st.session_state and \
   'METERS_DATA_hourly' not in st.session_state:

    st.error("Required session state variables are missing. Please visit the first page of the app first")

else:
    iso_cat__color_dict = st.session_state['POE_Unipol__CatColor_Dict']
    iso_seu_dict = st.session_state['POE_Unipol__ISO_SEU_Dict']

    df_meters_matrix =  st.session_state['POE_Unipol__SensorMatrix']

    METERS_DATA_hourly  = st.session_state['METERS_DATA__hourly']
    METERS_DATA_daily   = st.session_state['METERS_DATA__daily']
    METERS_DATA_weekly  = st.session_state['METERS_DATA__weekly']
    METERS_DATA_monthly = st.session_state['METERS_DATA__monthly']

    meter_columns = st.session_state['METERS_DATA__hourly'].columns.tolist()
    floors = list(set([meter.split('_')[0] for meter in meter_columns]))
    floors.sort()




####################################################################################
st.markdown('##### About this page')
st.markdown('This page offers a comparison between metered data extracted at Monthly, Weekly, Daily and Hourly level')




####################################################################################
df_monthly  = METERS_DATA_monthly
df_weekly   = METERS_DATA_weekly
df_daily    = METERS_DATA_daily
df_hourly   = METERS_DATA_hourly



####################################################################################
selected_cat_keys, selected_meters = absrd__create_filter_widgets_FLOOR_CAT(cat_dict=iso_seu_dict, meters_matrix=df_meters_matrix, floors=floors)

# st.write(selected_meters)

if selected_meters:
    df_plot = METERS_DATA_hourly[selected_meters]




####################################################################################




chart_cols = st.columns( len(df_plot.columns) )


for col, df_col in zip(chart_cols, df_plot.columns):

# for meter_id in df_hourly.columns:
    
    col.plotly_chart(
        plot_typical_week_box_plot(
            df=df_plot,
            meter_id=df_col,
            boxgap=0,
            boxgroupgap=0,
            plot_height=500,
            orientation='h',
            )
      )  # Vertical plot

