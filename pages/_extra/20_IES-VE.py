# IMPORT LIBRARIES
from fn__libs_data import *
import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
import plotly.graph_objs as go, plotly.subplots as sp





# PAGE CONFIG
# st.set_page_config(page_title="ITACA Streamlit App", page_icon='🍝', layout="wide")
from fn__page_header import create_page_header
create_page_header()




##### FUNCTION TO LOAD DICT DATA
# Function to load data from pickle files
def load_data(source, data_path):

    if source=='local':
        with open( os.path.join(data_path,'data_dict.pkl'), 'rb') as f:
            data_dict = pickle.load(f)

        with open( os.path.join(data_path,'room_info.pkl'), 'rb') as f:
            room_info = pickle.load(f)

    elif source=='ftp':
        response = requests.get( os.path.join(data_path,'data_dict.pkl') )
        response.raise_for_status()
        data_dict = pd.read_pickle(io.BytesIO(response.content))

        response = requests.get( os.path.join(data_path,'room_info.pkl') )
        response.raise_for_status()
        room_info = pd.read_pickle(io.BytesIO(response.content))

    return data_dict, room_info


##### FILE PATHS AND DATA LOAD
# file_path = os.path.join(DataFolder, 'AmbaAradan_4_aps.csv')
LOCAL_PATH  = r'C:/_GitHub/andreabotti/absrd-timeseries-deco/data/'
FTP_PATH    = r'https://absrd.xyz/streamlit_apps/timeseries-analysis/data/IES-VE/'


# DataFolder = 'data/'
# data_dict, room_info = load_data(source='local', data_path=LOCAL_PATH)
data_dict, room_info = load_data(source='ftp', data_path=FTP_PATH)




##### STREAMLIT SELECT ROOM ID AND DISPLAY DATA
col_list = [
    "Air temperature",
    "Operative temperature (ASHRAE)",
    "Heating plant sensible load",
    "Cooling plant sensible load",
    "Internal gain",
    "Solar gain",
    ]




#####
col1, col2 = st.columns([5,2])

col2.markdown('##### Sample data exploration for Amba Aradam')
col2.caption(f'from {FTP_PATH}')


selected_room_ids = col2.multiselect(
    "Select Room ID(s)",
    options = list(room_info.keys()),
    default = 'P100005D',
    )
selected_var = col2.multiselect(
    "Select Output Variable(s)",
    options = col_list,
    default = "Solar gain",
    )



col21, col22 = col2.columns([1,1])

# Filter the time series based on the selected date range
start_date = col21.date_input(
    label = "Start date",
    value = datetime.date(2023,7,1),
    )
end_date = col22.date_input(
    label = "End date",
    value = datetime.date(2023,8,31),
    )

# Display the dataframes for the selected Room IDs
for room_id in selected_room_ids:
    col1.markdown(f"###### Room ID: {room_id}, Room Name: {room_info[room_id]}")
    df = data_dict[room_id]

    for var in selected_var:
        df_var = df[[var]]
        df_var = df_var[start_date:end_date]
        col2.dataframe(df_var)

    # st.write(list(df.columns))








from statsmodels.tsa.seasonal import seasonal_decompose

time_series_pd = df_var
time_series = time_series_pd.values.tolist()

# Decompose the time series using seasonal_decompose
result = seasonal_decompose(time_series_pd, model='additive', period=24)


# Compute the Fourier Transform of the time series
fourier_transform = np.fft.fft(time_series)
frequencies = np.fft.fftfreq(len(time_series), d=1)  # d=1 for hourly data
magnitudes = np.abs(fourier_transform)

# Streamlit App
# col1.markdown("#### Time Series Decomposition and Fourier Transform")

# Plot the decomposition results using Plotly
fig = sp.make_subplots(rows=4, cols=1, subplot_titles=("Observed", "Trend", "Seasonal", "Residual"))

# Observed
observed_trace = go.Scatter(x=result.observed.index, y=result.observed, mode='lines', name='Observed')
fig.add_trace(observed_trace, row=1, col=1)

# Trend
trend_trace = go.Scatter(x=result.trend.index, y=result.trend, mode='lines', name='Trend', line=dict(color='orange'))
fig.add_trace(trend_trace, row=2, col=1)

# Seasonal
seasonal_trace = go.Scatter(x=result.seasonal.index, y=result.seasonal, mode='lines', name='Seasonal', line=dict(color='green'))
fig.add_trace(seasonal_trace, row=3, col=1)

# Residual
residual_trace = go.Scatter(x=result.resid.index, y=result.resid, mode='lines', name='Residual', line=dict(color='red'))
fig.add_trace(residual_trace, row=4, col=1)

fig.update_layout(height=800, width=800, title_text="Time Series Decomposition")



# Plot the Fourier Transform magnitudes using Plotly
fig2 = go.Figure()
fourier_transform_trace = go.Scatter(x=frequencies, y=magnitudes, mode='markers', name='Fourier Transform')
fig2.add_trace(fourier_transform_trace)
fig2.update_layout(title='Fourier Transform', xaxis_title='Frequency (1/hour)', yaxis_title='Magnitude')







LOCAL_PATH_GH  = r'C:\_GitHub\andreabotti\absrd-timeseries-deco\data\GH'
FileName = '2215_AA__solar_gains.csv'

df_gh = pd.read_csv( os.path.join(LOCAL_PATH_GH, FileName) )

# Apply datetime index
date_rng = pd.date_range(start='1/1/2023', end='12/31/2023 23:00:00', freq='H')
df_gh.set_index(date_rng, inplace=True)
df_gh_plot = df_gh[start_date:end_date]



# Create a trace for the current station's temperature data
df1 = df_gh_plot
df2 = df_var

fig_solar = go.Figure()

trace_gh = go.Scatter(
    x=df1.index,  # Assuming the DataFrame index is the datetime
    y=df1['solar_gains'],  # Assuming 'temp' column holds the temperature data
    mode='lines',  # Line plot
    line=dict(width=2),  # Black, thin, dotted line
    name=str('HoneyBee')  # Use the station ID as the trace name
)

trace_ies = go.Scatter(
    x=df2.index,
    y=df2['Solar gain'],
    mode='lines',  # Line plot
    line=dict(width=2),  # Black, thin, dotted line
    name=str('IES VE')
)

fig_solar.add_trace(trace_gh)
fig_solar.add_trace(trace_ies)


fig_solar.update_layout(
title='Solar Gains Data',
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
yaxis_title='Solar Gains (kW)',
legend_title='GH',
height=600,
# width=800,
margin=dict(l=10, r=10, t=100, b=10),
)





with col1:
    tab1, tab2, tab3 = st.tabs(['Time Series Visualisation', 'Time Series Decomposition', 'Fourier Transform'])

    tab1.plotly_chart(fig_solar, use_container_width=True)
    tab2.plotly_chart(fig, use_container_width=True)
    tab3.plotly_chart(fig2)
