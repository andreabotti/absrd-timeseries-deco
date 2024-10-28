# IMPORT LIBRARIES
from fn__libs_data import *
from fn__libs_charts import *

import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
from io import StringIO
from urllib.request import urlopen


####################################################################################
# PAGE CONFIG
from fn__page_header import create_page_header
iso_cat__color_dict = st.session_state['POE_Unipol__CatColor_Dict']
iso_seu_dict = st.session_state['POE_Unipol__ISO_SEU_Dict']

create_page_header(cat_dict=iso_seu_dict, color_dict=iso_cat__color_dict, show_cat_color_labels=True)



####################################################################################
##### FILE PATHS AND DATA LOAD
# Check if required session state variables are available

if 'POE_Unipol__ISO_SEU_Dict' not in st.session_state and \
   'POE_Unipol__SensorMatrix' not in st.session_state and \
   'METERS_DATA_hourly' not in st.session_state:

    st.error("Required session state variables are missing. Please visit the first page of the app first")

else:

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
        filtered_columns = sorted( [col for col in df.columns if col.split("_")[0] == prefix] )
        filtered_columns = [col for col in filtered_columns if 'GR' not in col]

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
    st.write("##### Yearly Totals (kWh) - All meters")

    # Apply the function to your dataframe
    yearly_totals__dict = split_by_prefix(df=METERS_DATA_monthly)

    for f in floors:
        col_1, space, col_2, space, col_3 = st.columns([5, 1, 15, 1, 24])


        year_total_df = yearly_totals__dict[f]
        year_total_df['total'] = year_total_df.sum(axis=1)

        # Display yearly total metric
        col_1.metric(label=f'**{f}**: Yearly Total kWh ', value=year_total_df.at[f, 'total'])
        col_3.dataframe(year_total_df)

        # Initialize the figure
        fig_stacked_bars_h = go.Figure()

        # Drop the total column for plotting
        year_total_df__plot = year_total_df.drop(['total'], axis=1)

        # Dictionary to collect columns by selected category
        grouped_data = {}

        for col in year_total_df__plot.columns:
            # Define category mappings and filters
            cat_dict = iso_seu_dict
            meters_matrix = df_meters_matrix
            filter_type = 'Cat_eng'
            cat_mapping = {
                'Cat_num': {key: key for key in cat_dict},
                'Cat_eng': {key: cat_dict[key]['Cat_eng'] for key in cat_dict},
                'Cat_ita': {key: cat_dict[key]['Cat_ita'] for key in cat_dict}
            }

            try:
                # Matching row in the matrix for color and category
                meter_column_name = 'Sensor_ID'  # Replace with actual column name if different
                matching_row = meters_matrix[meters_matrix[meter_column_name] == col].iloc[0]
                selected_cat = matching_row[matching_row == "Y"].index.tolist()[0]  # Column where value is "Y"
                selected_color = iso_cat__color_dict[selected_cat]

                # Add to grouped data dictionary by category
                if selected_cat not in grouped_data:
                    grouped_data[selected_cat] = {
                        'color': selected_color,
                        'data': []
                    }
                grouped_data[selected_cat]['data'].append((col, year_total_df[col]))

            except Exception as e:
                # Print the error if needed
                print(f"Error processing sensor {col}: {e}")

        # Add traces to the figure by category group
        for category, group in grouped_data.items():
            for col, data in group['data']:
                # Simplify the trace name to the last part after '_'
                simple_name = col.split('_')[-1]

                fig_stacked_bars_h.add_trace(
                    go.Bar(
                        x=data,                      # Data for x-axis (horizontal bars)
                        y=year_total_df.index,       # Data for y-axis (categories)
                        name=simple_name,            # Use simplified name in the legend
                        orientation='h',
                        marker=dict(color=group['color']),  # Apply group color
                    )
                )

        # Update layout for stacked bars and legend at the top
        fig_stacked_bars_h.update_layout(
            barmode='stack',

            xaxis=dict(
                range=[0, 101000],           # Set fixed x-axis range
                dtick=10000,           # Set dtick for intervals (adjust as needed)
                showgrid=True,               # Show gridlines
                gridcolor="LightGray",       # Gridline color
                gridwidth=0.1,                # Gridline width
            ),

            height=140,
            showlegend=True,                   # Show legend
            legend=dict(
                orientation="h",               # Horizontal legend
                yanchor="bottom",
                y=1.02,                        # Position above chart
                xanchor="center",
                x=0.5
            ),
            margin=dict(l=10, r=10, t=10, b=0)  # Adjust margins
        )

        # Display the plot
        col_2.plotly_chart(fig_stacked_bars_h)

        custom_hr()  # Render custom horizontal line, if defined



