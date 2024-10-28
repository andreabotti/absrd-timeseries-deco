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
iso_cat__color_dict = st.session_state['POE_Unipol__CatColor_Dict']
iso_seu_dict = st.session_state['POE_Unipol__ISO_SEU_Dict']

create_page_header(cat_dict=iso_seu_dict, color_dict=iso_cat__color_dict, show_cat_color_labels=True




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


IESVE_hourly = st.session_state['IESVE_export_data']



####################################################################################

# Add a widget to select a floor
selected_floor = st.sidebar.multiselect("Select Floors:", options=floors, default='F08')

# Filter the sensors based on the selected categories (CAT01, CAT02, etc.)
all_meters = list(df_meters_matrix['Sensor_ID'])

# Filter the meter options based on the selected floor
selected_meters = [meter for meter in all_meters if any(meter.startswith(f"{f}_") for f in selected_floor)]
# st.write(selected_meters)


if selected_meters:
    df_monthly  = METERS_DATA_hourly[selected_meters]
    df_weekly   = METERS_DATA_weekly[selected_meters]
    df_daily    = METERS_DATA_daily[selected_meters]
    df_hourly   = METERS_DATA_hourly[selected_meters]




####################################################################################
digital_df = IESVE_hourly
real_df = df_hourly

# Extract the start and end datetime from the digital_df
start_datetime = digital_df.index.min()
end_datetime = digital_df.index.max()

# Use the start and end datetime to slice the real_df
real_df = real_df.loc[start_datetime:end_datetime]

# st.dataframe(digital_df)
# st.dataframe(real_df)
# st.write( [c for c in real_df.columns] )
# st.write( [c for c in digital_df.columns] )


# Dictionary to store combined dataframes
combined_data = {}

# Iterate through each column in the real data
for real_col in real_df.columns:

    for digital_col in digital_df.columns:

        digital_col_split = digital_col.rsplit('__',2)[0]
        # st.write(f'{digital_col} - which can be split into - {digital_col_split}')

        # Split the digital column header to find matching real column
        if real_col == digital_col_split:
            # Create a combined dataframe for the current meter
            combined_df = pd.DataFrame({
                'IESVE': digital_df[digital_col],
                'Metered': real_df[real_col]
            })
            # Add the combined dataframe to the dictionary
            combined_data[real_col] = combined_df


# st.write(combined_data)




####################################################################################
# Create tabs
tab_hourly, tab_daily, tab_weekly, tab_total = st.tabs(['Hourly', 'Daily', 'Weekly_Monthly', 'Total'])


# Hourly Tab
with tab_hourly:
    st_cols = st.columns(len(combined_data.keys()))
    for col, (key, df) in zip(st_cols, combined_data.items()):
        # Convert to numeric and display hourly data
        df = df.apply(pd.to_numeric, errors='coerce')
        col.markdown(f"###### {key} - Hourly Data")
        col.dataframe(df, height=400)


# Daily Tab
with tab_daily:
    st_cols = st.columns(len(combined_data.keys()))
    for col, (key, df) in zip(st_cols, combined_data.items()):
        # Convert to numeric and resample to daily
        df = df.apply(pd.to_numeric, errors='coerce')
        daily_from_hourly = df.resample('D').sum().round(0)
        daily_from_hourly.index = daily_from_hourly.index.strftime('%Y-%m-%d')
        col.markdown(f"###### {key} - Daily Data")
        col.dataframe(daily_from_hourly, height=400)


# Weekly Tab
with tab_weekly:
    st_cols = st.columns(len(combined_data.keys()))
    for col, (key, df) in zip(st_cols, combined_data.items()):
        # Convert to numeric and resample to weekly
        df = df.apply(pd.to_numeric, errors='coerce')
        weekly_from_hourly = df.resample('W-SUN').sum().round(0)
        weekly_from_hourly.index = weekly_from_hourly.index.strftime('%Y-%m-%d')
        col.markdown(f"###### {key} - Weekly Data")
        col.dataframe(weekly_from_hourly, height=250, use_container_width=True)

        monthly_from_hourly = df.resample('M').sum().round(0)
        monthly_from_hourly.index = monthly_from_hourly.index.strftime('%Y-%m')
        col.markdown(f"###### {key} - Monthly Data")
        col.dataframe(monthly_from_hourly, height=80, use_container_width=True)



# Hourly Tab
with tab_total:
    st_cols = st.columns(len(combined_data.keys()))
    for col, (key, df) in zip(st_cols, combined_data.items()):
        # Convert to numeric and display hourly data
        df = df.apply(pd.to_numeric, errors='coerce')

        col.markdown(f"###### {key} - Total Sum")
        col.write(df.sum().round(0))

