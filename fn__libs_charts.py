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

import calplot

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






####################################################################################
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





####################################################################################

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





####################################################################################

def create_calplot(df, show_values, figsize):

    width_in = figsize['width_px'] / figsize['dpi']
    height_in = figsize['height_px'] / figsize['dpi']

    # Ensure that the index is in datetime format
    df.index = pd.to_datetime(
        df.index,
        format='%d/%m/%Y %H:%M',
        )

    for column in df.columns:
        values = df[column].dropna()

        # Create the calplot
        fig, axs = calplot.calplot(
            values,
            # suptitle=f'Calendar Heatmap for {column}',
            cmap='viridis_r',  # Custom color map for heatmap
            # vmin=-2, vmax=2,  # Min and Max range for heatmap values
            linewidth=0.8,
            linecolor='white',
            colorbar=False,
            textformat='{:.0f}' if show_values else None,  # Display values on heatmap
            textcolor='white',  # Color of text values
            textfiller='-',     # Placeholder for missing values
            figsize=(width_in, height_in),
            yearlabel_kws={
                "fontsize": 14,           # Font size for the year label
                "color": "black",      # Font color for the year label
                "fontfamily": "Arial",    # Font family
                # "weight": "bold"          # Font weight, optional
                },
        )

        # Iterate over the axes to set the text properties
        for ax in axs:
            for label in ax.texts:  # This accesses the text elements
                label.set_fontsize(7)
                label.set_fontfamily('Arial')

        spacing_factor = 0.904
        spacing_factor = 0.9634


        # Get the first axis to add week numbers (assuming one year per axis)
        ax = axs[0]
        # # Add week numbers on the top x-axis
        week_ticks = pd.Series(values.index).dt.isocalendar().week  # Get the week numbers
        unique_weeks = ['.','.','.'] + (sorted(week_ticks.unique()))
        print(unique_weeks)

        ax_top = ax.twiny()  # Create a second x-axis on top
        ax_top.set_xlim(ax.get_xlim())  # Match the limits of the original x-axis

        # # Calculate the number of weeks and set tick positions across the entire chart width
        num_weeks = len(unique_weeks)
        tick_positions = np.linspace(ax.get_xlim()[0], ax.get_xlim()[1], num_weeks) * spacing_factor

        # # Set the shifted ticks and corresponding week numbers
        ax_top.set_xticks(tick_positions)
        ax_top.set_xticklabels([f'{str(w)}' for w in unique_weeks], fontsize=7, color='grey')

        # # Hide the ticks but keep the labels
        ax_top.tick_params(top=False)



        # Customize day labels
        for ax in fig.axes:

            # ax.legend().set_visible(False)

            # Customize month labels (months of the year)
            month_labels = ax.get_xticklabels()
            for text in month_labels:
                text.set_fontsize(7)
                text.set_color('black')
                text.set_fontfamily('Arial')

            # Customize year labels
            year_labels = ax.get_yticklabels()
            for text in year_labels:
                text.set_fontsize(7.5)
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






# Function to display comparison tables and charts for a specific sensor within a tab
def display_comparison_for_sensor(sensor_id, data, timeframe, table_height, chart_height, chart_margins):
    # Create two columns: one for the table and one for the chart
    col1, col2 = st.columns([2,3])

    # In the first column, display the table
    with col1:
        st.markdown(f"##### {timeframe} totals for meter: {sensor_id} (table)")
        st.dataframe(data, height=table_height)

    # In the second column, plot the comparison as a column chart
    with col2:
        st.markdown(f"##### {timeframe} totals for meter: {sensor_id} (chart)")

        # Ensure the index is reset to use 'month_year' or 'datetime' in the plot
        if 'month_year' in data.columns:
            x_axis = 'month_year'
        else:
            x_axis = data.index.name  # For 'datetime' in weekly and daily comparisons

        fig = px.bar(
            data.reset_index(),
            x=x_axis,
            y=data.columns,
            barmode='group',
            height=chart_height,
            # title=f'{timeframe} Totals Comparison for Sensor: {sensor_id}',
            )
        
        # Hide x-axis title
        fig.update_xaxes(title=None)

        # Customize the margins using the user-defined margins
        fig.update_layout(margin=dict(l=chart_margins['left'], r=chart_margins['right'], t=chart_margins['top'], b=chart_margins['bottom']))

        st.plotly_chart(fig)

    custom_hr()






def plot_typical_week_box_plot(df, meter_id, plot_height, orientation, boxgap, boxgroupgap):
    fig = go.Figure()

    # Define day names for easier plotting
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_names = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']

    # Create box plots for each day of the week for the given sensor
    for day in range(7):
        # Filter the dataframe for the specific day of the week
        day_data = df[df.index.dayofweek == day]

        # Adjust orientation based on user preference
        if orientation == 'h':  # Horizontal layout
            fig.add_trace(go.Box(
                x=day_data[meter_id],  # x holds the energy consumption values
                y=[day_names[day]] * len(day_data[meter_id]),  # y is now the day names (horizontal axis labels)
                name=day_names[day],
                boxmean=True,  # Show mean on box plot
                orientation='h',  # Horizontal orientation
                boxpoints='outliers',  # Hide individual points inside the box for a cleaner look
            ))
        else:  # Vertical layout (standard)
            fig.add_trace(go.Box(
                y=day_data[meter_id],  # y holds the energy consumption values
                x=[day_names[day]] * len(day_data[meter_id]),  # x is now the day names (vertical axis labels)
                name=day_names[day],
                boxmean=True,  # Show mean on box plot
                orientation='v',  # Vertical orientation
                boxpoints='outliers',  # Hide individual points inside the box for a cleaner look
            ))

    # Update layout to control the appearance of the chart
    if orientation == 'h':
        fig.update_layout(
            title=f'Box Plot for {meter_id} (Typical Week)',
            xaxis_title='Energy Consumption (kWh)',
            # yaxis_title='Day of Week',
            showlegend=False,
            height=plot_height,  # Adjust height for horizontal layout
            boxmode='group',
            boxgap=boxgap,  # Control the gap between boxes within a group (set to 0 for wider boxes)
            boxgroupgap=boxgroupgap,  # Reduce the gap between groups of boxes
            yaxis = dict(
                # tickangle=90,
                range=[-2, 7],
                ), # Compress the y-axis to make boxes appear wider
        )
    else:
        fig.update_layout(
            title=f'Box Plot for {meter_id} (Typical Week)',
            yaxis_title='Energy Consumption (kWh)',
            # xaxis_title='Day of Week',
            xaxis = dict(
                # tickangle=90,
                range=[-1, 7],
                ), # Compress the y-axis to make boxes appear wider
            showlegend=False,
            height=plot_height,  # You can adjust this based on how compressed the plot looks
            boxmode='group',
            boxgap=boxgap,  # Control the gap between boxes within a group (set to 0 for wider boxes)
            boxgroupgap=boxgroupgap,  # Reduce the gap between groups of boxes
        )



    return fig










# Function to display comparison tables and charts for a specific sensor within a tab
def absrd_plot_comparison_digital_real(meter_id, df, timeframe, table_height, chart_height, chart_margins, digital_color, real_color):

    df_table = df.copy()

    # Add a new column 'Diff %'
    df_table["Diff %"] = 100* (df_table["Digital"] - df_table["Real"]) / df_table["Real"]
    # Add "+" to positive values
    df_table["Diff %"] = df_table["Diff %"].apply(lambda x: f"+{x:.0f}%" if x > 0 else f"{x:.0f}%")

    col1, col2 = st.columns([2, 5])

    # In the first column, display the table
    with col1:
        st.markdown(f"##### {timeframe} totals for meter: {meter_id}")
        st.dataframe(round(df_table,1), height=table_height)

    # In the second column, plot the comparison as a column chart
    with col2:
        st.markdown('')
        st.markdown('')

        # Reshape data into long-form for Plotly
        df_chart = df
        df_chart_long = df_chart.reset_index().melt(id_vars='datetime', var_name='Type', value_name='Total')

        # Create a Plotly figure with separate traces for digital and real data
        fig = px.bar(
            df_chart_long,
            x='datetime',
            y='Total',
            color='Type',  # Color by 'Type' to differentiate 'Daily Digital' and 'Daily Real'
            color_discrete_map={'Digital': digital_color, 'Real': real_color},
            barmode='group',
            height=chart_height,
            # labels={'Daily Total': 'Daily Totals', 'datetime': 'Date'}
        )

        # Customize the margins using the user-defined margins
        fig.update_layout(margin=dict(l=chart_margins['left'], r=chart_margins['right'], t=chart_margins['top'], b=chart_margins['bottom']))

        st.plotly_chart(fig)

    custom_hr()
