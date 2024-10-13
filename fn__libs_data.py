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
                margin-top: -5px;
                margin-bottom: 0px;
            }
        </style>
    """, unsafe_allow_html=True)
    # Adding the horizontal line with reduced vertical spacing
    st.markdown('<hr class="hr-line">', unsafe_allow_html=True)





# Function to load CSV from a local file
def load_csv_local(file):
    df = pd.read_csv(file)
    return df

# Function to load CSV from an FTP link
def load_csv_ftp(ftp_url):
    response = urlopen(ftp_url)
    data = response.read().decode('utf-8')
    print(data)
    df = pd.read_csv(data)
    return df


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






#####
# Function to create color variations
def create_color_variations(base_color, num_colors):
    """Create a list of colors varying slightly from a base color."""
    colors = []
    for i in range(num_colors):
        # Create intermediate color
        variation = find_intermediate_color(base_color, 'white', i / (num_colors + 2))  # Lighter shades
        colors.append(variation)
    return colors



# Function to create color variations
def create_color_variations(base_color_hex, num_colors):
    """Create a list of colors varying slightly from a base color."""
    base_color_rgb = hex_to_rgb(base_color_hex)  # Convert hex to RGB
    white_rgb = hex_to_rgb('#FFFFFF')  # White color in RGB
    colors = []
    for i in range(num_colors):
        # Create intermediate color between base color and white
        variation = find_intermediate_color(base_color_rgb, white_rgb, i / (num_colors + 2))  # Lighter shades
        colors.append(f'rgb{variation}')  # Convert to 'rgb(r,g,b)' format
    return colors




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



#####

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




#####

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



#####

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















def absrd_plotly_bar_plot_sensor(df, margin, chart_type):
    if chart_type == "subplots":
        # Create subplots
        fig = make_subplots(rows=len(df.columns), cols=1, shared_xaxes=True, vertical_spacing=0.05)

        # Add a subplot for each column
        for i, column in enumerate(df.columns):
            fig.add_trace(go.Bar(
                x=df.index,
                y=df[column],
                name=column
            ), row=i+1, col=1)

        # Update layout for shared axis, title, and other styling
        fig.update_layout(
            showlegend=True,               # Show legend for each subplot
            height=200*len(df.columns),     # Adjust the height of the chart
            margin=margin if margin else dict(l=10, r=10, t=40, b=20),  # Apply user-defined margins or default
        )
        
    elif chart_type == "stacked_bars":
        # Create a stacked bar chart (single plot)
        fig = go.Figure()
        for column in df.columns:
            fig.add_trace(go.Bar(
                x=df.index,
                y=df[column],
                name=column
            ))

        # Update layout for stacked bars
        fig.update_layout(
            barmode='stack',  # Stacked bar mode
            showlegend=True,  # Show legend
            height=600,       # Set a fixed height for the chart
            margin=margin if margin else dict(l=10, r=10, t=40, b=20),  # Apply user-defined margins or default
        )

    return fig











def absrd_create_calendar_heatmap(df, value_column):
    # Extract the year and ensure the index is a datetime object
    df['date'] = df.index
    df['day_of_year'] = df['date'].dt.dayofyear
    df['day_of_week'] = df['date'].dt.weekday
    df['week_of_year'] = df['date'].dt.isocalendar().week
    
    # Prepare the heatmap grid
    heatmap_data = df.pivot_table(index='week_of_year', columns='day_of_week', values=value_column, aggfunc='sum').fillna(0)

    # Create a heatmap using Plotly
    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_data.values, # heatmap values
            x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], # x-axis labels (days of the week)
            y=heatmap_data.index, # y-axis labels (weeks of the year)
            colorscale='YlGnBu',
            hoverongaps=False
        )
    )
    # Customize layout
    fig.update_layout(
        title=f'Calendar Heatmap for {df["date"].dt.year.unique()[0]}',
        xaxis_title="Day of the Week",
        yaxis_title="Week of the Year",
        yaxis_nticks=52,
        yaxis_autorange="reversed",  # Reverse to have Week 1 at the top
        height=800
    )
    return fig





def absrd_create_calendar_heatmap(df):
    # Extract necessary date components
    df['date'] = df.index
    df['day_of_year'] = df['date'].dt.dayofyear
    df['day_of_week'] = df['date'].dt.weekday
    df['week_of_year'] = df['date'].dt.isocalendar().week

    # Iterate over each column in the dataframe to create a heatmap for each column
    for column in df.columns:
        if column in ['date', 'day_of_year', 'day_of_week', 'week_of_year']:
            continue  # Skip date-related columns we added
        
        # Pivot the data for calendar heatmap
        heatmap_data = df.pivot_table(index='week_of_year', columns='day_of_week', values=column, aggfunc='sum').fillna(0)
        
        # Create heatmap
        fig = go.Figure(
            data=go.Heatmap(
                z=heatmap_data.values,  # Heatmap values
                x=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],  # Day of the week
                y=heatmap_data.index,  # Week of the year
                colorscale='YlGnBu',
                hoverongaps=False
            )
        )
        
        # Customize layout
        fig.update_layout(
            title=f'Calendar Heatmap for {column} ({df["date"].dt.year.unique()[0]})',
            xaxis_title="Day of the Week",
            yaxis_title="Week of the Year",
            yaxis_nticks=52,
            yaxis_autorange="reversed",  # Week 1 on top
            height=800
        )
        
        return fig








import calplot
import matplotlib.pyplot as plt

def create_calplot(df, show_values, figsize):

    width_in = figsize['width_px'] / figsize['dpi']
    height_in = figsize['height_px'] / figsize['dpi']

    for column in df.columns:
        values = df[column].dropna()

        # Create the calplot
        fig, axs = calplot.calplot(
            values,
            # suptitle=f'Calendar Heatmap for {column}',
            cmap='viridis_r',  # Custom color map for heatmap
            # vmin=-2, vmax=2,  # Min and Max range for heatmap values
            linewidth=0.5,
            linecolor='white',
            colorbar=True,
            textformat='{:.0f}' if show_values else None,  # Display values on heatmap
            textcolor='white',  # Color of text values
            textfiller='-',     # Placeholder for missing values
            figsize=(width_in, height_in),
        )

        # Iterate over the axes to set the text properties
        for ax in axs:
            for label in ax.texts:  # This accesses the text elements
                label.set_fontsize(6)
                label.set_fontfamily('Arial')

        spacing_factor = 1.01


        # Get the first axis to add week numbers (assuming one year per axis)
        ax = axs[0]

        # # Add week numbers on the top x-axis
        # week_ticks = pd.Series(values.index).dt.isocalendar().week  # Get the week numbers
        # unique_weeks = week_ticks.unique()

        # ax_top = ax.twiny()  # Create a second x-axis on top
        # ax_top.set_xlim(ax.get_xlim())  # Match the limits of the original x-axis

        # # Calculate the number of weeks and set tick positions across the entire chart width
        # num_weeks = len(unique_weeks)
        # tick_positions = np.linspace(ax.get_xlim()[0], ax.get_xlim()[1], num_weeks) * spacing_factor

        # # Set the shifted ticks and corresponding week numbers
        # ax_top.set_xticks(tick_positions)
        # ax_top.set_xticklabels([f'{int(w)}' for w in unique_weeks], fontsize=10, color='blue')

        # # Hide the ticks but keep the labels
        # ax_top.tick_params(top=False)



        # Customize day labels
        for ax in fig.axes:

            # Customize month labels (months of the year)
            month_labels = ax.get_xticklabels()
            for text in month_labels:
                text.set_fontsize(7)
                text.set_color('black')
                text.set_fontfamily('Arial')

            # Customize year labels
            year_labels = ax.get_yticklabels()
            for text in year_labels:
                text.set_fontsize(8)
                text.set_color('black')
                text.set_fontfamily('Arial')

        # Manually create a single colorbar for the figure
        # cbar = fig.colorbar(ax.get_children()[0], ax=ax, orientation='vertical')
        # cbar.ax.yaxis.set_tick_params(labelsize=8, colors='black')
        # cbar.ax.set_yticklabels(cbar.ax.get_yticklabels(), fontfamily='Arial')
        
        # # Adjust the layout to prevent the colorbar from being misaligned
        # plt.tight_layout()

        # Display the plot in Streamlit
        st.markdown(f'##### Calendar Heatmap for {column}')
        st.pyplot(fig, dpi=figsize['dpi'])
        custom_hr()

