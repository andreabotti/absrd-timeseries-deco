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
selected_cat_keys, selected_meters = absrd__create_filter_widgets_FLOOR_CAT(cat_dict=iso_seu_dict, meters_matrix=df_meters_matrix, floors=floors)

if selected_meters:
    df_plot = METERS_DATA_hourly[selected_meters]

    # Ensure the data is numeric to avoid TypeError
    # df = df.apply(pd.to_numeric, errors='coerce')

else:
    st.write("No meters selected.")
    df_plot = pd.DataFrame()  # Return an empty dataframe



####################################################################################
start_date, end_date = absrd__create_filter_widgets_DATES()

df_plot = df_plot[(df_plot.index >= pd.Timestamp(start_date)) & (df_plot.index <= pd.Timestamp(end_date))]





####################################################################################
# TABS
tab_calplot, tab_scatter = st.tabs(['CALENDAR HEATMAP', 'SCATTER CHARTS'])


with tab_scatter:

    with st.sidebar:
        custom_hr()
    # Display chart type menu
    chart_type = st.sidebar.radio("Choose chart type:", ("Lines", "Stacked Areas"), horizontal=True)



    # Adjust the logic for handling colors for multiple categories
    if not df_plot.empty:

        # st.dataframe(df_plot[:3])

        # Generate color variations for each selected category
        trace_colors = []
        for selected_cat_key in selected_cat_keys:
            main_color = iso_cat__color_dict.get(selected_cat_key, '#1f77b4')  # Default to blue if category not found
            trace_colors += create_color_variations(main_color, len(df_plot.columns))

        # Plot based on the selected chart type
        if chart_type == "Lines":
            fig = px.line(
                df_plot,
                x=df_plot.index,
                y=df_plot.columns,
                title='Energy Usage Over Time',
                color_discrete_sequence=trace_colors
            )

        elif chart_type == "Stacked Areas":
            # Create a stacked area chart
            fig = go.Figure()
            for meter in df_plot.columns:
                fig.add_trace(go.Scatter(
                    x=df_plot.index,
                    y=df_plot[meter],
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
    create_calplot(df_plot, show_values=True, figsize=calplot_figsize)




