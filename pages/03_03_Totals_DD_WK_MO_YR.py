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
df_monthly  = METERS_DATA_monthly
df_weekly   = METERS_DATA_weekly
df_daily    = METERS_DATA_daily
df_hourly   = METERS_DATA_hourly




####################################################################################
selected_cat_keys, selected_meters = absrd__create_filter_widgets_FLOOR_CAT(cat_dict=iso_seu_dict, meters_matrix=df_meters_matrix, floors=floors)

if selected_meters:
    df_plot = METERS_DATA_hourly[selected_meters]

    # Ensure the data is numeric to avoid TypeError
    # df = df.apply(pd.to_numeric, errors='coerce')

else:
    st.write("No meters selected.")
    df_plot = pd.DataFrame()  # Return an empty dataframe




# Calculate the daily, monthly, weekly, totals
daily_totals = df_plot.resample('D').sum()
weekly_totals = df_plot.resample('W').sum()
monthly_totals = df_plot.resample('M').sum()
yearly_totals = df_plot.resample('Y').sum()



# Function to split the dataframe into multiple ones based on the prefix in a tuple-based column
def split_by_prefix(df):
    # Assuming the first element of the tuple is the prefix (e.g., 'S01')
    prefixes = sorted( set([col.split("_")[0] for col in df.columns]) )
    # st.write(prefixes)
    
    # Create a dictionary to hold the dataframes for each prefix
    yearly_totals__dict = {}
    
    for prefix in prefixes:
        # Filter the columns that have the current prefix as the first element in the tuple
        filtered_columns = [col for col in df.columns if col.split("_")[0] == prefix]
        
        # Slice the dataframe to only include the filtered columns
        sliced_df = df[filtered_columns]
        
        # Resample to yearly totals
        yearly_totals = sliced_df.resample('Y').sum()
        
        # Add the prefix as a new index
        yearly_totals['Prefix'] = prefix
        yearly_totals.set_index('Prefix', inplace=True)

        # Store the result in the dictionary
        yearly_totals__dict[prefix] = yearly_totals
    
    return yearly_totals__dict









####################################################################################

tab_daily, tab_weekly, tab_monthly, tab_yearly, tab_yearly_all = st.tabs([
'daily_totals', 'weekly_totals', 'monthly_totals', 'yearly_totals', 'yearly_totals_ALL_meters'
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
    st.write("##### Yearly Totals (kWh)")
    st.dataframe(yearly_totals)


with tab_yearly_all:
    # col_table, col_chart = st.columns([2,5])
    st.write("##### Yearly Totals (kWh) - All meters")

    # Apply the function to your dataframe
    yearly_totals__dict = split_by_prefix(df=METERS_DATA_monthly)

    for f in floors:
        col_1, col_2, col_3 = st.columns([1,3,6])

        year_total_df = yearly_totals__dict[f]
        year_total_df['total'] = year_total_df.sum(axis=1)

        col_1.metric(label=f'**{f}**: Yearly Total kWh ', value=year_total_df.at[f,'total'] )
        col_3.dataframe(year_total_df)

        absrd__create_grouping_color_coding_FLOOR_CAT(cat_dict=iso_seu_dict, meters_matrix=df_meters_matrix, floors=floors)

        custom_hr()