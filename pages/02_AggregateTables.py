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
df = METERS_DATA_HOURLY


# Add a widget to select a floor
selected_floor = st.sidebar.multiselect("Select Floors:", options=floors, default='F08')

# Create a mapping for each category type
cat_mapping = {
    'Cat_num': {key: key for key in iso_seu_dict},
    'Cat_eng': {key: iso_seu_dict[key]['Cat_eng'] for key in iso_seu_dict},
    'Cat_ita': {key: iso_seu_dict[key]['Cat_ita'] for key in iso_seu_dict}
}

# User selects which category to filter by (ISO Cat Number, ISO Cat Name, or Unipol Cat Name)
filter_type = st.sidebar.radio(
    "Choose ISO category (name or number):",
    ['Cat_num', 'Cat_eng', 'Cat_ita'],
    horizontal=True,
)


# Create a dropdown for the user to select a category based on their filter type selection
selected_categories = st.sidebar.multiselect(
    f"Select {filter_type}(s):",
    options = list( cat_mapping[filter_type].values()), default=list(cat_mapping[filter_type].values())[1],
    )


# Reverse map the selected categories to the corresponding category keys (e.g., 'CAT01', 'CAT02', etc.)
selected_cat_keys = [key for key, value in cat_mapping[filter_type].items() if value in selected_categories]

# Filter the sensors based on the selected categories (CAT01, CAT02, etc.)
filtered_meter_indices = df_meters_matrix[df_meters_matrix[selected_cat_keys].eq('Y').any(axis=1)].index

# Assuming you've now identified the correct column
meter_column_name = 'Sensor_ID'  # Replace with actual column name from df_meters_matrix
filtered_meters = df_meters_matrix.loc[filtered_meter_indices, meter_column_name].tolist()

# Convert all meters to strings and filter out None/NaN values
filtered_meters = [str(meter) for meter in filtered_meters if pd.notnull(meter)]

# Filter the meter options based on the selected floor
filtered_meters = [meter for meter in filtered_meters if any(meter.startswith(f"{f}_") for f in selected_floor)]

# Multi-select widget for selecting meters (filtered by the selected floor)
selected_meters = st.sidebar.multiselect("Select Meters:", options=filtered_meters, default=filtered_meters)

# Filter the dataframe based on the selected meters
if selected_meters:
    df = df[selected_meters]
else:
    st.write("No meters selected.")
    df = pd.DataFrame()  # Empty dataframe






# Calculate the daily, monthly, weekly, totals
daily_totals = df.resample('D').sum()
weekly_totals = df.resample('W').sum()
monthly_totals = df.resample('M').sum()
yearly_totals = df.resample('Y').sum()





####################################################################################

tab_daily, tab_weekly, tab_monthly, tab_yearly = st.tabs([
'daily_totals', 'weekly_totals', 'monthly_totals', 'yearly_totals'
])


with st.sidebar:
    custom_hr()
    chart_type = st.radio(label='Choose either Subplots or Stacked Bars', options=['subplots', 'stacked_bars'], horizontal=True)


with tab_daily:
    col_table, col_chart = st.columns([2,5])
    col_table.write("##### Daily Totals (kWh)")
    col_table.dataframe(daily_totals)
    fig_daily = absrd_plotly_bar_plot_sensor(df=daily_totals, margin=None, chart_type=chart_type)
    col_chart.plotly_chart(fig_daily)


with tab_weekly:
    col_table, col_chart = st.columns([2,5])
    col_table.write("##### Weekly Totals (kWh)")
    col_table.dataframe(weekly_totals)
    fig_weekly = absrd_plotly_bar_plot_sensor(df=weekly_totals, margin=None, chart_type=chart_type)
    col_chart.plotly_chart(fig_weekly)


with tab_monthly:
    col_table, col_chart = st.columns([2,5])
    col_table.write("##### Monthly Totals (kWh)")
    col_table.dataframe(monthly_totals)
    fig_monthly = absrd_plotly_bar_plot_sensor(df=monthly_totals, margin=None, chart_type=chart_type)
    col_chart.plotly_chart(fig_monthly)


with tab_yearly:
    # col_table, col_chart = st.columns([2,5])
    st.write("##### Yearly Totals (kWh)")
    st.dataframe(yearly_totals)
    # fig_yearly = absrd_plotly_bar_plot_sensor(df=yearly_totals, margin=None)
    # col_chart.plotly_chart(fig_yearly)

