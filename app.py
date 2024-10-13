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


# Use a progress bar to monitor the loading and processing of the dataframe
progress_bar = st.progress(0)

# Check if the dataframe is already in session state
if 'POE_Unipol__SensorData' not in st.session_state:
    # Step 1: Load the data only if not already in session state

    st.markdown('Loading POE_Unipol__SensorData')
    progress_bar.progress(10)  # Update progress

    # file_path = os.path.join(data_folder, 'Elenco meters - Torre Unipol.xlsx')  # Replace with the correct path
    # df_meters_data = pd.read_excel(file_path, sheet_name='Foglio1')

    file_path = os.path.join(data_folder, 'TorreUnipol__AllMetersData.csv')  # Replace with the correct path
    df_meters_data = pd.read_csv(file_path)

    # Step 2: Data preprocessing - Transpose the data so each row corresponds to a time series for each meter
    progress_bar.progress(30)  # Update progress
    # Transpose the data
    df_meters_data = df_meters_data.T
    df_meters_data.columns = df_meters_data.iloc[1]
    df_meters_data = df_meters_data.drop(df_meters_data.index[0])

    # Convert the index (which is the transposed columns) into a datetime format
    progress_bar.progress(60)  # Update progress
    df_meters_data.index = pd.to_datetime(df_meters_data.index, format='%d/%m/%y %H.%M', errors='coerce')
    df_meters_data = df_meters_data[:-1]

    # Store the dataframe in session state
    st.session_state['POE_Unipol__SensorData'] = df_meters_data
  
    # Complete progress
    progress_bar.progress(80)

else:
    # Use the dataframe already stored in session state
    df_meters_data = st.session_state['POE_Unipol__SensorData']
    progress_bar.progress(80)  # Indicate that the data is already loaded



# Check if the dataframe is already in session state
if 'POE_Unipol__SensorMatrix' not in st.session_state:

    st.markdown('Loading POE_Unipol__SensorMatrix')

    df_meters_matrix = pd.read_csv( os.path.join(data_folder, 'TorreUnipol__All5__Merged_Sensor_Matrix.csv') )


    # Reorder the columns based on sorting CAT1 and CAT2 alphabetically
    df_meters_matrix = df_meters_matrix[['Sensor_ID', 'Metered_Zone'] + sorted(df_meters_matrix.columns[2:])]

    # Store the dataframe in session state
    st.session_state['POE_Unipol__SensorMatrix'] = df_meters_matrix

    # Complete progress
    progress_bar.progress(100)

else:
    # Use the dataframe already stored in session state
    df_meters_data = st.session_state['POE_Unipol__SensorData']
    progress_bar.progress(100)  # Indicate that the data is already loaded



iso_seu_dict = {
    'CAT01': {'Cat_eng': 'HVAC - Cooling', 'Cat_ita': 'Climatizzazione estiva'},
    'CAT02': {'Cat_eng': 'HVAC - Heating', 'Cat_ita': 'Climatizzazione invernale'},
    'CAT03': {'Cat_eng': 'Pumps - Heating', 'Cat_ita': 'Pompaggio caldo (secondario)'},
    'CAT04': {'Cat_eng': 'Pumps - Cooling', 'Cat_ita': 'Pompaggio freddo (secondario)'},
    'CAT05': {'Cat_eng': 'Ventilation', 'Cat_ita': 'HVAC (ventilazione)'},
    'CAT06': {'Cat_eng': 'Domestic Hot Water', 'Cat_ita': 'Acqua calda sanitaria'},
    'CAT07': {'Cat_eng': 'Lifts', 'Cat_ita': 'Ascensori'},
    'CAT08': {'Cat_eng': 'Lighting', 'Cat_ita': 'Illuminazione'},
    'CAT09': {'Cat_eng': 'Mechanical Power', 'Cat_ita': 'Forza motrice'},
    'CAT10': {'Cat_eng': 'HVAC - Air Distribution', 'Cat_ita': 'Ventilconvettori'},
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


# Display the final transposed dataframe in Streamlit
# st.dataframe(df_meters_data, height=300)
# st.dataframe(df_meters_matrix, height=300)



