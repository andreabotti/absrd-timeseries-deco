# IMPORT LIBRARIES
from fn__libs_data import *
import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
import plotly.graph_objs as go, plotly.subplots as sp

# PAGE CONFIG
from fn__page_header import create_page_header
create_page_header()






##### FILE PATHS AND DATA LOAD
LOCAL_PATH  = r'C:/_GitHub/andreabotti/absrd-timeseries-deco/data/'
FTP_PATH    = r'https://absrd.xyz/streamlit_apps/timeseries-analysis/data/Unipol/'


data_folder = './data'

# Define file paths for the CSVs
file_path_hourly = os.path.join(data_folder, 'POE_Unipol__AllMetersData__hourly.csv')
file_path_daily = os.path.join(data_folder, 'POE_Unipol__AllMetersData__daily.csv')
file_path_weekly = os.path.join(data_folder, 'POE_Unipol__AllMetersData__weekly.csv')
file_path_monthly = os.path.join(data_folder, 'POE_Unipol__AllMetersData__monthly.csv')




# Use a progress bar to monitor the loading and processing of the dataframe
progress_bar = st.progress(0)



# Check if the dataframes are already in session state
if 'METERS_DATA__hourly' not in st.session_state or \
   'METERS_DATA__daily' not in st.session_state or \
   'METERS_DATA__weekly' not in st.session_state or \
   'METERS_DATA__monthly' not in st.session_state:

    # Step 1: Load the data only if not already in session state
    st.markdown('Loading POE_Unipol__AllMetersData CSVs')
    progress_bar.progress(10)  # Update progress

    # Step 2: Load each CSV
    METERS_DATA_hourly  = pd.read_csv(file_path_hourly, index_col=0, parse_dates=True)
    METERS_DATA_daily   = pd.read_csv(file_path_daily,  index_col=0, parse_dates=True)
    METERS_DATA_weekly  = pd.read_csv(file_path_weekly, index_col=0, parse_dates=True)
    METERS_DATA_monthly = pd.read_csv(file_path_monthly,index_col=0, parse_dates=True)

    METERS_DATA_hourly.index = pd.to_datetime(METERS_DATA_hourly.index,format='%d/%m/%Y %H:%M')
    METERS_DATA_daily.index = pd.to_datetime(METERS_DATA_daily.index,format='%d/%m/%Y')
    METERS_DATA_weekly.index = pd.to_datetime(METERS_DATA_weekly.index,format='%d/%m/%Y')
    METERS_DATA_monthly.index = pd.to_datetime(METERS_DATA_monthly.index,format='%d/%m/%Y')


    # Store each dataframe in session state
    st.session_state['METERS_DATA__hourly']   = METERS_DATA_hourly
    st.session_state['METERS_DATA__daily']    = METERS_DATA_daily
    st.session_state['METERS_DATA__weekly']   = METERS_DATA_weekly
    st.session_state['METERS_DATA__monthly']  = METERS_DATA_monthly

    # Update progress
    progress_bar.progress(80)

else:
    # Use the dataframes already stored in session state
    METERS_DATA_hourly  = st.session_state['METERS_DATA__hourly']
    METERS_DATA_daily   = st.session_state['METERS_DATA__daily']
    METERS_DATA_weekly  = st.session_state['METERS_DATA__weekly']
    METERS_DATA_monthly = st.session_state['METERS_DATA__monthly']
    
    # Indicate that the data is already loaded
    progress_bar.progress(80)




# Check if the dataframe is already in session state
if 'POE_Unipol__SensorMatrix' not in st.session_state:

    st.markdown('Loading POE_Unipol__SensorMatrix')

    df_meters_matrix = pd.read_csv( os.path.join(data_folder, 'TorreUnipol__All5__Merged_Sensor_Matrix.csv') )

    # Reorder the columns based on sorting CAT1 and CAT2 alphabetically
    df_meters_matrix = df_meters_matrix[['Sensor_ID', 'Metered_Zone'] + sorted(df_meters_matrix.columns[2:])]

    # Store the dataframe in session state
    st.session_state['POE_Unipol__SensorMatrix'] = df_meters_matrix

    progress_bar.progress(100)

else:
    # Use the dataframe already stored in session state
    df_meters_matrix = st.session_state['POE_Unipol__SensorMatrix']
    progress_bar.progress(100)  # Indicate that the data is already loaded



iso_seu_dict = {
    'CAT01': {'Cat_eng': 'HVAC Cooling', 'Cat_ita': 'Climatizzazione estiva'},
    'CAT02': {'Cat_eng': 'HVAC Heating', 'Cat_ita': 'Climatizzazione invernale'},
    'CAT03': {'Cat_eng': 'Pumps HTG', 'Cat_ita': 'Pompaggio caldo (secondario)'},
    'CAT04': {'Cat_eng': 'Pumps CLG', 'Cat_ita': 'Pompaggio freddo (secondario)'},
    'CAT05': {'Cat_eng': 'HVAC Ventilation', 'Cat_ita': 'HVAC (ventilazione)'},
    'CAT06': {'Cat_eng': 'Domestic Hot Water', 'Cat_ita': 'Acqua calda sanitaria'},
    'CAT07': {'Cat_eng': 'Lifts', 'Cat_ita': 'Ascensori'},
    'CAT08': {'Cat_eng': 'Lighting', 'Cat_ita': 'Illuminazione'},
    'CAT09': {'Cat_eng': 'Mechanical Power', 'Cat_ita': 'Forza motrice'},
    'CAT10': {'Cat_eng': 'HVAC FanCoils', 'Cat_ita': 'Ventilconvettori'},
    'CAT11': {'Cat_eng': 'Other Systems', 'Cat_ita': 'Altro'}
}
# Predefined color dictionary for each category in iso_seu_dict
category_color_dict = {
    'CAT01': '#1f77b4',  # Blue for 'HVAC - Cooling'
    'CAT02': '#ff7f0e',  # Orange for 'HVAC - Heating'
    'CAT03': '#2ca02c',  # Green for 'Water Heating & Distribution'
    'CAT04': '#d62728',  # Red for 'Water Cooling & Distribution'
    'CAT05': '#9467bd',  # Purple for 'Ventilation Systems'
    'CAT06': '#8c564b',  # Brown for 'Domestic Hot Water'
    'CAT07': '#e377c2',  # Pink for 'Lifts'
    'CAT08': '#7f7f7f',  # Gray for 'Lighting'
    'CAT09': '#bcbd22',  # Yellow-green for 'Mechanical Power'
    'CAT10': '#17becf',  # Teal for 'HVAC - Air Distribution'
    'CAT11': '#bcbd22'   # Yellow-green for 'Other Systems'
}




st.session_state['POE_Unipol__ISO_SEU_Dict'] = iso_seu_dict
st.session_state['POE_Unipol__CatColor_Dict'] = category_color_dict



custom_hr()

with st.expander('Monthly Data'):
    st.dataframe(METERS_DATA_monthly)

with st.expander('Weekly Data'):
    st.dataframe(METERS_DATA_weekly)

with st.expander('Daily Data'):
    st.dataframe(METERS_DATA_daily)

with st.expander('Hourly Data'):
    st.dataframe(METERS_DATA_hourly)



custom_hr()



####################################################################################
col_1,spacing, col_2 = st.columns([16,1,10])

col_1.dataframe(df_meters_matrix, use_container_width=True, height=900)

col_2.write(iso_seu_dict)

