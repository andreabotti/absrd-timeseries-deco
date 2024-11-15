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

create_page_header(cat_dict=iso_seu_dict, color_dict=iso_cat__color_dict, show_cat_color_labels=False)




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


# IESVE_hourly = st.session_state['IESVE_export_data']





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



# custom_hr()
start_date, end_date = absrd__create_filter_widgets_DATES()





####################################################################################
col_01, col_02 = st.columns([2,5])


with col_01:
    df0 = absrd__upload_and_process_xlsx_all_columns()


datetime_range = create_datetime_range(start_date=start_date, end_date=end_date, freq='H')  # You can switch 'H' to 'D' for daily frequency
df0.index = datetime_range

IESVE_hourly = df0





####################################################################################
digi_df_hourly = IESVE_hourly
real_df_hourly = df_hourly

# Extract the start and end datetime from the digital_df
start_datetime  = digi_df_hourly.index.min()
end_datetime    = digi_df_hourly.index.max()

# Use the start and end datetime to slice the real_df
real_df = real_df_hourly.loc[start_datetime:end_datetime]


# Split each column header at the first "__" and reassign them to the DataFrame
new_headers = [header.split("__", 1)[0] if "__" in header else header for header in digi_df_hourly.columns]
digi_df_hourly.columns = new_headers


with col_02:
    with st.expander('DIGITAL DATA'):
        st.dataframe(digi_df_hourly, height=250)
        # st.write(digi_df_hourly.columns)


    with st.expander('METERED DATA'):
        st.dataframe(real_df_hourly, height=250)



digi_df_hourly = IESVE_hourly
real_df_hourly = df_hourly

digi_df_monthly = digi_df_hourly.resample('M').sum()
digi_df_weekly  = digi_df_hourly.resample('W-SUN').sum()
digi_df_daily   = digi_df_hourly.resample('D').sum()

real_df_monthly = real_df_hourly.resample('M').sum()
real_df_weekly  = real_df_hourly.resample('W-SUN').sum()
real_df_daily   = real_df_hourly.resample('D').sum()



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






table_height = 250
chart_height = 250

chart_margins = {
    'left': 10,
    'right': 10,
    'top': 20,
    'bottom': 0,
}


# Step 4: Set up the tabs before looping through each sensor
tab1, tab2, tab3 = st.tabs(
    [
    "Daily Comparison",
    "Weekly Comparison",
    "Monthly Comparison"],
    )



# Define colors for digital and real traces outside the function
digital_color = '#0c6681'  # Color for "Daily Digital"
real_color = '#ff5733'     # Color for "Daily Real"


# Step 5: Loop through each selected sensor (i.e., columns of the input dataframe) and display their comparison tables in the relevant tab
for meter_id in digi_df_monthly.columns:  # No need to drop 'month_year' since it's no longer a column

    # Skip meter IDs with 'GR' in the header
    if 'GR' in meter_id:
        continue

    try:
        with tab1:
            # Create a daily comparison dataframe for the selected meter_id
            df_daily_comparison = pd.DataFrame({
                "datetime": digi_df_daily.index,
                "Daily Digital": pd.to_numeric(digi_df_daily[meter_id], errors='coerce'),
                "Daily Real": pd.to_numeric(real_df_daily[meter_id], errors='coerce')
            })
            df_daily_comparison.set_index("datetime", inplace=True)

            absrd_plot_comparison_digital_real(
                meter_id=meter_id,
                plot_data=df_daily_comparison,
                timeframe="Daily",
                table_height=table_height, chart_height=chart_height, chart_margins=chart_margins,
                digital_color=digital_color, real_color=real_color,
                )
    except:
        ''


    try:
        # Monthly comparison in Tab 1
        with tab2:

            # Create a daily comparison dataframe for the selected meter_id
            df_weekly_comparison = pd.DataFrame({
                "datetime": digi_df_weekly.index,
                "Weekly Digital": pd.to_numeric(digi_df_weekly[meter_id], errors='coerce'),
                "Weekly Real": pd.to_numeric(real_df_weekly[meter_id], errors='coerce')
            })
            df_weekly_comparison.set_index("datetime", inplace=True)

            absrd_plot_comparison_digital_real(
                meter_id=meter_id,
                plot_data=df_weekly_comparison,
                timeframe="Weekly",
                table_height=table_height, chart_height=chart_height, chart_margins=chart_margins,
                digital_color=digital_color, real_color=real_color,
            )
    except:
        ''



    try:
        # Monthly comparison in Tab 1
        with tab3:

            # Create a daily comparison dataframe for the selected meter_id
            df_monthly_comparison = pd.DataFrame({
                "datetime": digi_df_monthly.index,
                "Monthly Digital": pd.to_numeric(digi_df_monthly[meter_id], errors='coerce'),
                "Monthly Real": pd.to_numeric(real_df_monthly[meter_id], errors='coerce')
            })
            df_monthly_comparison.set_index("datetime", inplace=True)

            absrd_plot_comparison_digital_real(
                meter_id=meter_id,
                plot_data=df_monthly_comparison,
                timeframe="Monthly",
                table_height=table_height, chart_height=chart_height, chart_margins=chart_margins,
                digital_color=digital_color, real_color=real_color,
            )
    except:
        ''



