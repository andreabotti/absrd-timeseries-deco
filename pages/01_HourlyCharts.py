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
# Sidebar options for date selection method
date_selection_method = st.sidebar.radio(
    "Choose Date Selection Method:",
    ('All Year', 'Week Number', 'Choose Dates'),
    horizontal=True
)

if date_selection_method == 'Choose Dates':
    # Create two sub-columns for start and end date selection
    col_start, col_end = st.sidebar.columns(2)

    # Select start date and end date from the calendar for 2023
    start_date = col_start.date_input("Start Date", value=datetime.date(2023, 1, 1), min_value=datetime.date(2023, 1, 1), max_value=datetime.date(2023, 12, 31))
    end_date = col_end.date_input("End Date", value=datetime.date(2023, 1, 31), min_value=datetime.date(2023, 1, 1), max_value=datetime.date(2023, 12, 31))

    # Ensure start date is before or equal to the end date
    if start_date > end_date:
        st.sidebar.error("Start date must be before or equal to the end date.")

    # Filter the data for the selected date range
    filtered_df_meters_data = METERS_DATA_HOURLY[(METERS_DATA_HOURLY.index >= pd.Timestamp(start_date)) & (METERS_DATA_HOURLY.index <= pd.Timestamp(end_date))]

elif date_selection_method == 'Week Number':
    # Dropdown to select a week number (1-52) for 2023
    selected_week = st.sidebar.slider(label="Select Week Number:", min_value=1, max_value=53, value=4)

    # Get the start and end dates for the selected week in 2023
    start_date = datetime.datetime.strptime(f'2023-W{int(selected_week )}-1', "%Y-W%W-%w").date()
    end_date = start_date + datetime.timedelta(days=6)  # Add 6 days to get the end of the week

    # Filter the data for the selected week
    filtered_df_meters_data = METERS_DATA_HOURLY[(METERS_DATA_HOURLY.index >= pd.Timestamp(start_date)) & (METERS_DATA_HOURLY.index <= pd.Timestamp(end_date))]


elif date_selection_method == 'All Year':
    filtered_df_meters_data = METERS_DATA_HOURLY

# st.dataframe(filtered_df_meters_data)




####################################################################################
with st.sidebar:
    custom_hr()

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
    "Choose ISO Category (english or italian):",
    ['Cat_eng', 'Cat_ita'],
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
    filtered_df_meters_data = filtered_df_meters_data[selected_meters]

    # Ensure the data is numeric to avoid TypeError
    filtered_df_meters_data = filtered_df_meters_data.apply(pd.to_numeric, errors='coerce')


else:
    st.write("No meters selected.")
    filtered_df_meters_data = pd.DataFrame()  # Empty datafram







####################################################################################
# TABS
tab_calplot, tab_scatter = st.tabs(['CALENDAR HEATMAP', 'SCATTER CHARTS'])





####################################################################################
with tab_scatter:


    with st.sidebar:
        custom_hr()
    # Display chart type menu
    chart_type = st.sidebar.radio("Choose chart type:", ("Line Chart", "Stacked Area Chart"))



    # Adjust the logic for handling colors for multiple categories
    if not filtered_df_meters_data.empty:

        # Generate color variations for each selected category
        trace_colors = []
        for selected_cat_key in selected_cat_keys:
            main_color = iso_cat__color_dict.get(selected_cat_key, '#1f77b4')  # Default to blue if category not found
            trace_colors += create_color_variations(main_color, len(filtered_df_meters_data.columns))

        # Plot based on the selected chart type
        if chart_type == "Line Chart":
            fig = px.line(
                filtered_df_meters_data,
                x=filtered_df_meters_data.index,
                y=filtered_df_meters_data.columns,
                title='Energy Usage Over Time',
                color_discrete_sequence=trace_colors
            )

        elif chart_type == "Stacked Area Chart":
            # Create a stacked area chart
            fig = go.Figure()
            for meter in filtered_df_meters_data.columns:
                fig.add_trace(go.Scatter(
                    x=filtered_df_meters_data.index,
                    y=filtered_df_meters_data[meter],
                    mode='lines',
                    stackgroup='one',  # This enables stacking
                    name=meter
                ))
            fig.update_layout(title='Stacked Area Chart of Energy Usage Over Time', xaxis_title='Timestamp', yaxis_title='Energy Usage')


        fig.update_layout(
        # title='Hourly Meter Data',
        xaxis=dict(
            # title='Time',
            rangeselector=dict(
                buttons=list([
                    dict(count=3, label="3d", step="day", stepmode="backward"),
                    dict(count=7, label="7d", step="day", stepmode="backward"),
                    dict(count=14, label="14d", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            ),
            type="date",
            rangeslider=dict(visible=True),
        ),
        yaxis_title='Energy (kWh)',
        # legend_title='GH',
        height=600,
        # width=800,
        margin=dict(l=10, r=10, t=80, b=10),
        )

        st.plotly_chart(fig)

    else:
        st.write("No data to display for the selected filters.")








####################################################################################
with tab_calplot:

    calplot_figsize = {
    'width_px' : 6600,     # Desired pixel dimensions
    'height_px' : 1000,     # Desired pixel dimensions
    'dpi' : 600,           # Define DPI (dots per inch)
    }

    # Plot calendar heatmap
    create_calplot(filtered_df_meters_data, show_values=True, figsize=calplot_figsize)




