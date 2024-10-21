# IMPORT LIBRARIES
from fn__libs_data import *
from fn__libs_charts import *

import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
from io import StringIO
from urllib.request import urlopen
from datetime import datetime, timedelta  # Explicitly import datetime class from the datetime module


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

selected_cat_keys, selected_meters = absrd__create_filter_widgets_FLOOR_CAT(cat_dict=iso_seu_dict, meters_matrix=df_meters_matrix, floors=floors)

if selected_meters:
    df_monthly  = METERS_DATA_hourly[selected_meters]
    df_weekly   = METERS_DATA_weekly[selected_meters]
    df_daily    = METERS_DATA_daily[selected_meters]
    df_hourly   = METERS_DATA_hourly[selected_meters]



def create_datetime_range(start_date, end_date, freq):
    # Adjust end date to include the entire last day by setting time to 23:59:59 for hourly frequency
    if freq == 'H':
        end_date = datetime.combine(end_date, datetime.max.time())  # Set to the end of the day (23:59:59)
    
    datetime_range = pd.date_range(start=start_date, end=end_date, freq=freq)
    
    return datetime_range



####################################################################################
all_data, sheet_names, column_indices = absrd__upload_and_process_xlsx_by_position()

all_data.columns = all_data.columns.str.replace('Electricity: ', '').str.strip()


with st.sidebar:

    custom_hr()
    start_date, end_date = absrd__create_filter_widgets_MONTH_WEEK()
    st.write(start_date, end_date)

# Generate a datetime range between the start and end dates with hourly frequency ('H') or daily frequency ('D')
datetime_range = create_datetime_range(start_date=start_date, end_date=end_date, freq='H')  # You can switch 'H' to 'D' for daily frequency
all_data.index = datetime_range


custom_hr()

#####
st.write(f"Data from columns at positions: {column_indices}")
st.dataframe(all_data)

st.session_state['IESVE_export_data'] = all_data
