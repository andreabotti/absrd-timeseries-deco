# IMPORT LIBRARIES
from fn__libs_data import *
import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
import plotly.graph_objs as go, plotly.subplots as sp





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
iso_seu_dict = {
    'CAT01': {'Cat_eng': 'Cooling', 'Cat_ita': 'Climatizzazione estiva'},
    'CAT02': {'Cat_eng': 'Heating', 'Cat_ita': 'Climatizzazione invernale'},
    'CAT03': {'Cat_eng': 'PumpsHTG', 'Cat_ita': 'Pompaggio caldo (secondario)'},
    'CAT04': {'Cat_eng': 'PumpsCLG', 'Cat_ita': 'Pompaggio freddo (secondario)'},
    'CAT05': {'Cat_eng': 'Ventilation', 'Cat_ita': 'HVAC (ventilazione)'},
    'CAT06': {'Cat_eng': 'DHW', 'Cat_ita': 'Acqua calda sanitaria'},
    'CAT07': {'Cat_eng': 'Lifts', 'Cat_ita': 'Ascensori'},
    'CAT08': {'Cat_eng': 'Lighting', 'Cat_ita': 'Illuminazione'},
    'CAT09': {'Cat_eng': 'Power', 'Cat_ita': 'Forza motrice'},
    'CAT10': {'Cat_eng': 'FanCoils', 'Cat_ita': 'Ventilconvettori'},
    'CAT11': {'Cat_eng': 'Other', 'Cat_ita': 'Altro'}
}


iso_cat__color_dict = {
    'CAT01': '#1f77b4',  # Blue for 'HVAC - Cooling'
    'CAT02': '#ff7f0e',  # Orange for 'HVAC - Heating'
    'CAT03': '#2ca02c',  # Green for 'Water Heating & Distribution'
    'CAT04': '#d62728',  # Red for 'Water Cooling & Distribution'
    'CAT05': '#9467bd',  # Purple for 'Ventilation Systems'
    'CAT06': '#8c564b',  # Brown for 'Domestic Hot Water'
    'CAT07': '#e377c2',  # Pink for 'Lifts'
    'CAT08': '#FFCA1A',  # Gray for 'Lighting'
    'CAT09': '#2ca02c',  # Yellow-green for 'Mechanical Power'
    'CAT10': '#17becf',  # Teal for 'HVAC - Air Distribution'
    'CAT11': '#bcbd22'   # Yellow-green for 'Other Systems'
}



####################################################################################
# PAGE CONFIG
from fn__page_header import create_page_header
create_page_header(cat_dict=iso_seu_dict, color_dict=iso_cat__color_dict)



####################################################################################
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

# Check if the original dataframes are already in session state
if 'METERS_DATA__original_hourly' not in st.session_state:
    # Load each CSV and store a copy of the original data
    METERS_DATA_hourly  = pd.read_csv(file_path_hourly, index_col=0, parse_dates=True)
    METERS_DATA_daily   = pd.read_csv(file_path_daily,  index_col=0, parse_dates=True)
    METERS_DATA_weekly  = pd.read_csv(file_path_weekly, index_col=0, parse_dates=True)
    METERS_DATA_monthly = pd.read_csv(file_path_monthly,index_col=0, parse_dates=True)

    # Set datetime index formats
    METERS_DATA_hourly.index = pd.to_datetime(METERS_DATA_hourly.index, format='%d/%m/%Y %H:%M')
    METERS_DATA_daily.index = pd.to_datetime(METERS_DATA_daily.index, format='%d/%m/%Y')
    METERS_DATA_weekly.index = pd.to_datetime(METERS_DATA_weekly.index, format='%d/%m/%Y')
    METERS_DATA_monthly.index = pd.to_datetime(METERS_DATA_monthly.index, format='%d/%m/%Y')

    # Store the original data in session state for later use
    st.session_state['METERS_DATA__original_hourly'] = METERS_DATA_hourly.copy()
    st.session_state['METERS_DATA__original_daily'] = METERS_DATA_daily.copy()
    st.session_state['METERS_DATA__original_weekly'] = METERS_DATA_weekly.copy()
    st.session_state['METERS_DATA__original_monthly'] = METERS_DATA_monthly.copy()

    progress_bar.progress(60)

# Reset data from the original each time to avoid cumulative changes
METERS_DATA_hourly = st.session_state['METERS_DATA__original_hourly'].copy()
METERS_DATA_daily = st.session_state['METERS_DATA__original_daily'].copy()
METERS_DATA_weekly = st.session_state['METERS_DATA__original_weekly'].copy()
METERS_DATA_monthly = st.session_state['METERS_DATA__original_monthly'].copy()





####################################################################################

# Define the lists for the target column and columns to subtract
target_column = ['F08_E_104']
columns_to_subtract = ['F08_E_226', 'F08_E_227', 'F08_E_228', 'F08_E_229', 'F08_E_230', 'F08_E_231', 'F08_E_232']

# Add backup columns for the original target column values to use in calculations
for df in [METERS_DATA_hourly, METERS_DATA_daily, METERS_DATA_weekly, METERS_DATA_monthly]:
    target = target_column[0]
    if f'{target}GR' not in df.columns:
        df[f'{target}GR'] = df[target]

# Apply the function to each dataset
METERS_DATA_hourly = subtract_columns(METERS_DATA_hourly, target_column, columns_to_subtract)
METERS_DATA_daily = subtract_columns(METERS_DATA_daily, target_column, columns_to_subtract)
METERS_DATA_weekly = subtract_columns(METERS_DATA_weekly, target_column, columns_to_subtract)
METERS_DATA_monthly = subtract_columns(METERS_DATA_monthly, target_column, columns_to_subtract)




####################################################################################
# Define the lists for the target column and columns to subtract
target_column = ['F08_E_108']
columns_to_subtract = ['F08_E_233', 'F08_E_234', 'F08_E_235']

# Add backup columns for the original target column values to use in calculations
for df in [METERS_DATA_hourly, METERS_DATA_daily, METERS_DATA_weekly, METERS_DATA_monthly]:
    target = target_column[0]
    if f'{target}GR' not in df.columns:
        df[f'{target}GR'] = df[target]

# Apply the function to each dataset
METERS_DATA_hourly = subtract_columns(METERS_DATA_hourly, target_column, columns_to_subtract)
METERS_DATA_daily = subtract_columns(METERS_DATA_daily, target_column, columns_to_subtract)
METERS_DATA_weekly = subtract_columns(METERS_DATA_weekly, target_column, columns_to_subtract)
METERS_DATA_monthly = subtract_columns(METERS_DATA_monthly, target_column, columns_to_subtract)



####################################################################################

# Display dataframes for verification
with st.expander('Monthly Data'):
    st.dataframe(METERS_DATA_monthly)

with st.expander('Weekly Data'):
    st.dataframe(METERS_DATA_weekly)

with st.expander('Daily Data'):
    st.dataframe(METERS_DATA_daily)

with st.expander('Hourly Data'):
    st.dataframe(METERS_DATA_hourly)


# Store each updated dataframe in session state
st.session_state['METERS_DATA__hourly']   = METERS_DATA_hourly
st.session_state['METERS_DATA__daily']    = METERS_DATA_daily
st.session_state['METERS_DATA__weekly']   = METERS_DATA_weekly
st.session_state['METERS_DATA__monthly']  = METERS_DATA_monthly






####################################################################################

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




custom_hr()
col_meter_matrix, col_seu_dict = st.columns([5,2]) 

with col_meter_matrix.expander('Meter Matrix'):
    st.dataframe(df_meters_matrix, use_container_width=True, height=550)

with col_seu_dict.expander('SEU Categories'):
    st.write(iso_seu_dict)



st.session_state['POE_Unipol__ISO_SEU_Dict'] = iso_seu_dict
st.session_state['POE_Unipol__CatColor_Dict'] = iso_cat__color_dict


