import pandas as pd, numpy as np
import os, glob, time, base64, subprocess, random, colorsys, pickle
import io, re, os, sys, time, json, datetime, requests, urllib.request, base64

from datetime import datetime, timedelta

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import altair as alt

import streamlit as st
from streamlit_super_slider import st_slider
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# from streamlit_pdf import st_pdf






##### ##### ##### ##### 

# def get_csv_files(data_path):
#     """Returns a list of csv files found in the specified directory."""
#     search_pattern = os.path.join(data_path, '*.csv')
#     csv_files = glob.glob(search_pattern)
#     return csv_files



#####

# Function to strip whitespace from strings
def strip_whitespace(x):
    try:
        return x.strip()
    except AttributeError:
        return x


# Function to load and process the data
def load_data(file_path, encoding='ISO-8859-1'):
    try:
        df0 = pd.read_csv(
            file_path,
            header=None,
            encoding=encoding,
            converters={col: strip_whitespace for col in range(1000)},
            low_memory=False,
        )

        print("Initial data loaded:")
        print(df0.head())

        # Transpose the DataFrame
        df1 = df0.T
        # Set the third row as the header
        df1.columns = df1.iloc[2]
        df1 = df1[3:]  # Remove the first three rows
        df1.reset_index(drop=True, inplace=True)

        print("Transposed data with new headers:")
        print(df1.head())

        # Ensure 'Room ID' is a column after transposition
        if 'Room ID' not in df1.columns:
            print("Error: 'Room ID' not found in the DataFrame columns.")
            return pd.DataFrame(), []

        unique_space_IDs = df1['Room ID'].unique()
        print("Unique space IDs:")
        print(unique_space_IDs)

        # Drop unnecessary columns, if any
        df1.drop(['Unit', 'Room Name'], axis=1, inplace=True, errors='ignore')

        return df1, unique_space_IDs

    except Exception as e:
        print(f"Failed to load data: {e}")
        return pd.DataFrame(), []


# Function to create a dictionary of DataFrames based on unique space IDs
def create_dataframe_dict(df, unique_space_IDs):
    # Check if the DataFrame is empty
    if df.empty:
        print("The DataFrame is empty.")
        return {}

    # Assuming the datetime information is in the first column after transposing
    datetime_column = df.columns[0]
    try:
        df[datetime_column] = pd.to_datetime(df[datetime_column], errors='coerce')
        df.set_index(datetime_column, inplace=True)
    except Exception as e:
        print(f"Error parsing datetime: {e}")
        return {}

    print("DataFrame after setting datetime index:")
    print(df.head())

    # Create a dictionary to hold DataFrames for each unique space_ID
    try:
        dfs = {space_id: df[df['Room ID'] == space_id] for space_id in unique_space_IDs}
    except Exception as e:
        print(f"Error creating DataFrame dictionary: {e}")
        return {}

    return dfs










def iesve__col_replacement_dict():

    dict = {
        'Air temperature'           :   'AT__C',
        # 'Dry resultant temperature' :   'DRT__C',
        # 'Mean radiant temperature'  :   'MRT',
        'Operative temperature (TM 52/CIBSE)'   :   'OT_TM52__C',
        'Internal gain'             :   'IntGains__kW',
        'Solar gain'                :   'SolarGains__kW',
        'MacroFlo ext vent gain'    :   'NatVentGains__kW',
        'MacroFlo external vent'    :   'NatVent__l/s',
        # 'Equipment gain'            :   'EqpGains',
        # 'Lighting gain'             :   'LightGains',
        # 'People gain'               :   'PplGains',
        # 'External conduction gain'  :   'ExtConGains',
        # 'Internal conduction gain'  :   'IntConGains',
        # 'Lighting gain'             :   'LightGains',
        'Aux vent gain'             :   'AuxVentGains__kW',
        'Auxiliary vent'            :   'AuxVent__l/s',
        }
    
    return dict









def process_data_sw_energy_meter(df):
    # Exclude non-time columns for melting
    time_columns = df.columns.drop(['Account Number', 'MPAN', 'Meter Serial Number', 'Date'])
    df_corrected_melted = df.melt(id_vars=["Date"], value_vars=time_columns, var_name="Time", value_name="Energy")

    # Combine Date and Time columns to create a datetime index
    df_corrected_melted['Datetime'] = pd.to_datetime(df_corrected_melted['Date'] + ' ' + df_corrected_melted['Time'], dayfirst=True)

    # Set the new datetime index
    df_corrected_melted = df_corrected_melted.set_index('Datetime')

    # Dropping the original Date and Time columns
    df_corrected_melted.drop(columns=['Date', 'Time'], inplace=True)

    # Resample the data to hourly resolution and sum the energy values
    df_hourly = df_corrected_melted.resample('H').sum()

    # Create daily and monthly dataframes by summing up the hourly data
    df_daily = df_hourly.resample('D').sum()
    df_monthly = df_hourly.resample('M').sum()

    return df_hourly, df_daily, df_monthly







# Function to filter DataFrame based on selected criteria
def filter_dataframe(granularity, df, plot_col):
    if granularity == "Year":
        # Do not filter, show entire DataFrame
        return df
    elif granularity == "Month":
        # Show a slider with months
        month = plot_col.slider(
            "Select Month",
            1, 12, 8,
            )
        return df[df.index.month == month]

    elif granularity == "Week":
        # Show a date widget to select start date
        start_date = plot_col.date_input("Select Start Date",   value = datetime.date(2023,8,21))
        end_date = start_date + pd.Timedelta(days=6)
        return df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]

    elif granularity == "Day":
        # Show two date widgets for start and end dates
        start_date = plot_col.date_input(label="Select Start Date", key="start_date",   value = datetime.date(2023,8,21))
        end_date = plot_col.date_input(label="Select End Date",     key="end_date",     value = datetime.date(2023,8,24))
        return df[(df.index >= pd.to_datetime(start_date)) & (df.index <= pd.to_datetime(end_date))]
