import pandas as pd, numpy as np
import os, glob, time, base64, subprocess, random, colorsys, pickle
import io, re, os, sys, time, json, datetime, requests, urllib.request, base64
from datetime import datetime, timedelta
import calendar

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.colors import find_intermediate_color, hex_to_rgb
import altair as alt
import matplotlib.pyplot as plt
# Set a default font
plt.rcParams['font.family'] = 'DejaVu Sans'  # Default font available with Matplotlib


import streamlit as st
from streamlit_super_slider import st_slider
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# from streamlit_pdf import st_pdf

import warnings
warnings.filterwarnings("ignore")





#####
def custom_hr():
    # Inject custom CSS to reduce vertical spacing before and after the horizontal line
    st.markdown("""
        <style>
            .hr-line {
                margin-top: -10px;
                margin-bottom: -10px;
            }
        </style>
    """, unsafe_allow_html=True)
    # Adding the horizontal line with reduced vertical spacing
    st.markdown('<hr class="hr-line">', unsafe_allow_html=True)






# Function to load data from pickle files
def load_data_csv(source, data_path, filename):

    if source=='local':
        with open( os.path.join(data_path,filename), 'rb') as f:
            df = pd.read_csv(f)


    elif source=='ftp':
            response = urlopen( os.path.join(data_path,filename) )
            data = response.read().decode('utf-8')
            df = pd.read_csv(StringIO(data))

    return df





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




####################################################################################

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






####################################################################################

def absrd__create_filter_widgets_FLOOR(cat_dict, meters_matrix, floors):
    """
    Filters the meters based on floor and category selection, and returns the filtered dataframe.
    """

    # Add a widget to select a floor
    selected_floor = st.sidebar.multiselect("Select Floors:", options=floors, default='F08')

    all_meters = meters_matrix['Sensor_ID'].to_list()
    filtered_meters = [str(meter) for meter in all_meters if pd.notnull(meter)]

    # Filter the meter options based on the selected floor
    filtered_meters = [meter for meter in filtered_meters if any(meter.startswith(f"{f}_") for f in selected_floor)]

    # Multi-select widget for selecting meters (filtered by the selected floor)
    selected_meters = st.sidebar.multiselect("Select Meters:", options=filtered_meters, default=filtered_meters)

    return selected_meters







def absrd__create_filter_widgets_FLOOR_CAT(cat_dict, meters_matrix, floors):
    """
    Filters the meters based on floor and category selection, and returns the filtered dataframe.
    """

    # Add a widget to select a floor
    selected_floor = st.sidebar.multiselect("Select Floors:", options=floors, default='F08')

    # Create a mapping for each category type
    cat_mapping = {
        'Cat_num': {key: key for key in cat_dict},
        'Cat_eng': {key: cat_dict[key]['Cat_eng'] for key in cat_dict},
        'Cat_ita': {key: cat_dict[key]['Cat_ita'] for key in cat_dict}
    }

    # User selects which category to filter by (ISO Cat Number, ISO Cat Name, or Unipol Cat Name)
    filter_type = st.sidebar.radio(
        label = "Choose ISO Category (english or italian):",
        options = ['Cat_eng', 'Cat_ita'],
        index = 1,
        horizontal=True,
    )

    # Create a dropdown for the user to select a category based on their filter type selection
    selected_categories = st.sidebar.multiselect(
        f"Select {filter_type}(s):",
        options=list(cat_mapping[filter_type].values()), 
        default=list(cat_mapping[filter_type].values())[8],
    )

    # Reverse map the selected categories to the corresponding category keys (e.g., 'CAT01', 'CAT02', etc.)
    selected_cat_keys = [key for key, value in cat_mapping[filter_type].items() if value in selected_categories]

    # Check if selected_cat_keys are in the columns of df_meters_matrix
    missing_keys = [key for key in selected_cat_keys if key not in meters_matrix.columns]

    if missing_keys:
        st.error(f"The following category keys are missing from the data: {missing_keys}")
        return pd.DataFrame()  # Return empty dataframe if keys are missing

    # Filter the sensors based on the selected categories (CAT01, CAT02, etc.)
    filtered_meter_indices = meters_matrix[meters_matrix[selected_cat_keys].eq('Y').any(axis=1)].index

    # Assuming you've now identified the correct column for Sensor IDs
    meter_column_name = 'Sensor_ID'  # Replace with actual column name from df_meters_matrix
    filtered_meters = meters_matrix.loc[filtered_meter_indices, meter_column_name].tolist()

    # Convert all meters to strings and filter out None/NaN values
    filtered_meters = [str(meter) for meter in filtered_meters if pd.notnull(meter)]


    # Filter the meter options based on the selected floor
    filtered_meters = [meter for meter in filtered_meters if any(meter.startswith(f"{f}_") for f in selected_floor)]

    # Multi-select widget for selecting meters (filtered by the selected floor)
    selected_meters = st.sidebar.multiselect("Select Meters:", options=filtered_meters, default=filtered_meters)

    return selected_cat_keys, selected_meters



####################################################################################


def absrd__create_filter_widgets_DATES():

    # Sidebar options for date selection method
    date_selection_method = st.sidebar.radio(
        "Choose Date Selection Method:",
        ('Entire Year', 'Week Num', 'Dates'),
        horizontal=True,
    )

    if date_selection_method == 'Dates':
        # Create two sub-columns for start and end date selection
        col_start, col_end = st.sidebar.columns(2)

        # Select start date and end date from the calendar for 2023
        start_date = col_start.date_input(
            "Start Date",
            value=datetime.date(2023, 1, 1),
            min_value=datetime.date(2023, 1, 1),
            max_value=datetime.date(2023, 12, 31),
            )
        end_date = col_end.date_input(
            "End Date",
            value=datetime.date(2023, 1, 31),
            min_value=datetime.date(2023, 1, 1),
            max_value=datetime.date(2023, 12, 31),
            )

        # Ensure start date is before or equal to the end date
        if start_date > end_date:
            st.sidebar.error("Start date must be before or equal to the end date.")

        # Filter the data for the selected date range

    elif date_selection_method == 'Week Num':
        # Dropdown to select a week number (1-52) for 2023
        selected_week = st.sidebar.slider(label="Select Week Number:", min_value=1, max_value=53, value=4)

        # Get the start and end dates for the selected week in 2023
        start_date = datetime.strptime(f'2023-W{int(selected_week)}-1', "%Y-W%W-%w").date()
        end_date = start_date + timedelta(days=6)
        # start_date = datetime.datetime.strptime(f'2023-W{int(selected_week )}-1', "%Y-W%W-%w").date()
        # end_date = start_date + datetime.timedelta(days=6)  # Add 6 days to get the end of the week


    elif date_selection_method == 'Entire Year':

        start_date = datetime(2023, 1, 1).date()
        end_date = datetime(2023, 12, 31).date()


    return start_date, end_date




####################################################################################



def absrd__create_grouping_color_coding_FLOOR_CAT(cat_dict, meters_matrix, floors):

    # Create a mapping for each category type
    cat_mapping = {
        'Cat_num': {key: key for key in cat_dict},
        'Cat_eng': {key: cat_dict[key]['Cat_eng'] for key in cat_dict},
        'Cat_ita': {key: cat_dict[key]['Cat_ita'] for key in cat_dict}
    }


    # User selects which category to filter by (ISO Cat Number, ISO Cat Name, or Unipol Cat Name)
    filter_type = 'Cat_eng'

    # Create a dropdown for the user to select a category based on their filter type selection
    selected_categories = list(cat_mapping[filter_type].values())
    st.write(selected_categories)

    # Reverse map the selected categories to the corresponding category keys (e.g., 'CAT01', 'CAT02', etc.)
    selected_cat_keys = [key for key, value in cat_mapping[filter_type].items() if value in selected_categories]

    st.write(selected_cat_keys)

    # Filter the sensors based on the selected categories (CAT01, CAT02, etc.)
    filtered_meter_indices = meters_matrix[meters_matrix[selected_cat_keys].eq('Y').any(axis=1)].index

    # Assuming you've now identified the correct column for Sensor IDs
    meter_column_name = 'Sensor_ID'  # Replace with actual column name from df_meters_matrix
    filtered_meters = meters_matrix.loc[filtered_meter_indices, meter_column_name].tolist()

    # Convert all meters to strings and filter out None/NaN values
    filtered_meters = [str(meter) for meter in filtered_meters if pd.notnull(meter)]

    # Filter the meter options based on the selected floor
    filtered_meters = [meter for meter in filtered_meters if any(meter.startswith(f"{f}_") for f in selected_floor)]

    # Multi-select widget for selecting meters (filtered by the selected floor)
    selected_meters = st.sidebar.multiselect("Select Meters:", options=filtered_meters, default=filtered_meters)

    return selected_cat_keys, selected_meters






####################################################################################

def absrd__upload_and_process_xlsx_by_position():

    col_1, col_2, col_3, col_4 = st.columns([5,3,5,3])
    # File uploader widget for xlsx files
    uploaded_file = col_1.file_uploader("Upload an Excel file", type=['xlsx'])
    
    main_df = pd.DataFrame()

    if uploaded_file is not None:
        # Read all sheets from the Excel file
        xlsx_data = pd.read_excel(uploaded_file, sheet_name=None)  # Read all sheets as a dictionary
        
        # List all the sheets in the uploaded file
        sheet_names = list(xlsx_data.keys())
        selected_sheet = col_2.selectbox("Select a sheet to view", sheet_names)
        
        # Load the selected sheet into a DataFrame
        df_tmp = xlsx_data[selected_sheet]      

        # Display available columns in the selected sheet
        with col_3:
            st.write("Columns available in this sheet:", df_tmp.columns.tolist())
        
        # Let the user pick column positions
        num_columns = len(df_tmp.columns)
        column_indices = col_4.slider(
            f"Select column positions (0 to {num_columns - 1})", 
            min_value=0, max_value=num_columns-1, value=num_columns-1,
        )


        # If column indices are selected, filter by those positions
        for s in sheet_names:

            # st.write(s)
            df_sheet = xlsx_data[s]
            
            if column_indices:
                df_sheet = df_sheet.iloc[:, column_indices]
                df_sheet.drop([0,1], axis=0, inplace=True)

                main_df = pd.concat([main_df, df_sheet], axis=1)
                # st.write(df_sheet[:2])
                # st.write(main_df[:2])

        return main_df, sheet_names, column_indices

    else:
        st.write("Please upload an Excel file.")
        return None




####################################################################################


def absrd__create_filter_widgets_MONTH_WEEK():
    # Sidebar options for date selection method
    date_selection_method = st.sidebar.radio(
        "Choose Date Selection Method:",
        ('Month Num', 'Week Num'),
        horizontal=True,
    )

    if date_selection_method == 'Month Num':
        # Dropdown to select a month number (1-12) for 2023
        selected_month = st.slider(label="Select Month Number:", min_value=1, max_value=12, value=1)

        # Get the start date (first day of the month)
        start_date = datetime(2023, selected_month, 1).date()
        
        # Get the last day of the selected month using calendar.monthrange()
        last_day_of_month = calendar.monthrange(2023, selected_month)[1]
        end_date = datetime(2023, selected_month, last_day_of_month).date()

    elif date_selection_method == 'Week Num':
        # Dropdown to select a week number (1-52) for 2023
        selected_week = st.slider(label="Select Week Number:", min_value=1, max_value=53, value=4)

        # Get the start and end dates for the selected week in 2023
        start_date = datetime.strptime(f'2023-W{int(selected_week)}-1', "%Y-W%W-%w").date()
        end_date = start_date + timedelta(days=6)

    return start_date, end_date







####################################################################################


# Define a function that performs the subtraction operation on the target column
def subtract_columns(df, target_col, cols_to_subtract):
    """
    Subtracts the values of each column in cols_to_subtract from the target_col in the dataframe.
    """
    required_columns = target_col + cols_to_subtract
    target = target_col[0]  # Extract the target column name as a string
    
    if all(col in df.columns for col in required_columns):
        # Preserve the original target column values before any subtraction
        if f'{target}GRO' not in df.columns:
            df[f'{target}GR'] = df[target]  # Create a backup column for original values if not already done

        # Calculate the total to subtract by summing columns to subtract
        total_subtraction = df[cols_to_subtract].sum(axis=1)

        # Assign the result of target minus total_subtraction to the target column
        df[target] = df[f'{target}GR'] - total_subtraction
    else:
        missing_cols = [col for col in required_columns if col not in df.columns]
        print(f"Missing columns in DataFrame: {missing_cols}")
    return df
