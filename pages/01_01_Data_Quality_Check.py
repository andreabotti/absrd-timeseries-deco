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

if selected_meters:
    df_monthly = METERS_DATA_monthly[selected_meters]
    df_weekly = METERS_DATA_weekly[selected_meters]
    df_daily = METERS_DATA_daily[selected_meters]
    df_hourly = METERS_DATA_hourly[selected_meters]

    # Ensure the data is numeric to avoid TypeError
    # df = df.apply(pd.to_numeric, errors='coerce')

else:
    st.write("No meters selected.")
    df_plot = pd.DataFrame()  # Return an empty dataframe


def swap_day_month(df):
    # Ensure the day values are valid months after swapping
    if df.index.day.max() > 12:
        raise ValueError("Day values exceed 12, cannot swap with month.")
    df.index = pd.to_datetime({
        'year': df.index.year,
        'month': df.index.day,
        'day': df.index.month
    })
    return df

# Use the function
df_monthly = swap_day_month(df_monthly)





####################################################################################
# Step 1: Calculate Totals (as before)
# Monthly totals
monthly_from_weekly = df_weekly.resample('M').sum()
monthly_from_daily = df_daily.resample('M').sum()
monthly_from_hourly = df_hourly.resample('M').sum()

# Weekly totals
# weekly_from_daily = df_daily.resample('W').sum()
# weekly_from_hourly = df_hourly.resample('W').sum()
weekly_from_daily = df_daily.resample('W-SUN').sum()
weekly_from_hourly = df_hourly.resample('W-SUN').sum()
# weekly_from_daily = df_daily.resample('W-MON').sum()
# weekly_from_hourly = df_hourly.resample('W-MON').sum()



# Daily totals
daily_from_hourly = df_hourly.resample('D').sum()

# Step 2: Create a 'month_year' column, set it as index, and drop the old datetime index
df_monthly['month_year'] = df_monthly.index.strftime('%Y-%m')
df_monthly = df_monthly.set_index('month_year', drop=True)

monthly_from_weekly['month_year'] = monthly_from_weekly.index.strftime('%Y-%m')
monthly_from_weekly = monthly_from_weekly.set_index('month_year', drop=True)

monthly_from_daily['month_year'] = monthly_from_daily.index.strftime('%Y-%m')
monthly_from_daily = monthly_from_daily.set_index('month_year', drop=True)

monthly_from_hourly['month_year'] = monthly_from_hourly.index.strftime('%Y-%m')
monthly_from_hourly = monthly_from_hourly.set_index('month_year', drop=True)





# Align indexes by concatenating based on 'month_year' column to avoid index misalignment
def concatenate_by_month(sensor_data_dict, sensor_id):
    """
    Concatenate multiple sensor data sources by 'month_year', ensuring that only 1D series are included.
    """
    df_concat = pd.concat([
        sensor_data_dict['Original Monthly'][[sensor_id]],          # 1D series for Original Monthly
        sensor_data_dict['Monthly from Weekly'][[sensor_id]],       # 1D series for Monthly from Weekly
        sensor_data_dict['Monthly from Daily'][[sensor_id]],        # 1D series for Monthly from Daily
        sensor_data_dict['Monthly from Hourly'][[sensor_id]]        # 1D series for Monthly from Hourly
    ], axis=1)
    
    # Rename the columns for clarity
    df_concat.columns = ['Original Monthly', 'Monthly from Weekly', 'Monthly from Daily', 'Monthly from Hourly']

    return df_concat




####################################################################################
table_height = 300
chart_height = 300

chart_margins = {
    'left': 10,
    'right': 10,
    'top': 20,
    'bottom': 0,
}


# Step 4: Set up the tabs before looping through each sensor
tab1, tab2, tab3 = st.tabs(["Monthly Totals Comparison", "Weekly Totals Comparison", "Daily Totals Comparison"])


# Step 5: Loop through each selected sensor (i.e., columns of the input dataframe) and display their comparison tables in the relevant tab
for sensor_id in df_monthly.columns:  # Now no need to drop 'month_year' since it's no longer a column


    # Monthly comparison in Tab 1
    with tab1:
        # Dictionary to pass the data
        monthly_data_dict = {
            'Original Monthly': df_monthly,
            'Monthly from Weekly': monthly_from_weekly,
            'Monthly from Daily': monthly_from_daily,
            'Monthly from Hourly': monthly_from_hourly
        }

        # Concatenate data by 'month_year' for the current sensor
        df_monthly_comparison = concatenate_by_month(monthly_data_dict, sensor_id)
        display_comparison_for_sensor(sensor_id, df_monthly_comparison, "Monthly", table_height, chart_height, chart_margins)


    # Weekly comparison in Tab 2 (same logic can be applied for weekly data)
    with tab2:
        df_weekly_comparison = pd.DataFrame({
            "Original Weekly": df_weekly[sensor_id],          # 1D series for Original Weekly
            "Weekly from Daily": weekly_from_daily[sensor_id],  # 1D series for Weekly from Daily
            "Weekly from Hourly": weekly_from_hourly[sensor_id]  # 1D series for Weekly from Hourly
        })
        df_weekly_comparison.index.name = 'datetime'  # Ensure the index has a name for plotting
        display_comparison_for_sensor(sensor_id, df_weekly_comparison, "Weekly", table_height, chart_height, chart_margins)


    # Daily comparison in Tab 3 (same logic can be applied for daily data)
    with tab3:
        df_daily_comparison = pd.DataFrame({
            "Original Daily": df_daily[sensor_id],            # 1D series for Original Daily
            "Daily from Hourly": daily_from_hourly[sensor_id]   # 1D series for Daily from Hourly
        })
        df_daily_comparison.index.name = 'datetime'  # Ensure the index has a name for plotting
        display_comparison_for_sensor(sensor_id, df_daily_comparison, "Daily", table_height, chart_height, chart_margins)


