# IMPORT LIBRARIES
from fn__libs_data import *
import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
from io import StringIO
from urllib.request import urlopen
import plotly.graph_objs as go, plotly.subplots as sp



# PAGE CONFIG
# st.set_page_config(page_title="ITACA Streamlit App", page_icon='🍝', layout="wide")
from fn__page_header import create_page_header
create_page_header()





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



##### FUNCTION TO LOAD DICT DATA
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


##### FILE PATHS AND DATA LOAD
# file_path = os.path.join(DataFolder, 'AmbaAradan_4_aps.csv')
LOCAL_PATH  = r'C:/_GitHub/andreabotti/absrd-timeseries-deco/data/'
FTP_PATH    = r'https://absrd.xyz/streamlit_apps/timeseries-analysis/data/SWA/'


df0 = load_data_csv(source='ftp', data_path=FTP_PATH, filename='SWA_ConsumptionStatement_1200051133916.csv')

df_hourly, df_daily, df_monthly = process_data_sw_energy_meter(df0)
# st.dataframe(df_hourly)



#####
col1, col2 = st.columns([5,2])
col2.markdown('###### Data exploration for Stanton Williams Energy')
col2.caption(f'from {FTP_PATH}')



col2.divider()
col21, col22 = col2.columns([2,3])


# Streamlit widgets to choose granularity and filter DataFrame
granularity = col21.selectbox(label="Select Granularity", options=["Year", "Month", "Week", "Day"], index=1)
df_plot = filter_dataframe(granularity, df_hourly, plot_col=col22)


col2.divider()
col21, col22 = col2.columns([2,3])

# Additional selectbox for specific values
period_values = [1, 6, 12, 24, 24*7]
period_captions = ["", "1 = 1 hour", "6 = 6 hrs", "12 = 12 hrs", "24 = 24 hrs", "168 = 1 wk"]
decompose_period = col21.radio("Decompose Period", options=period_values)
col22.markdown("\n ".join([f"+ {value}" for value in period_captions]))




from statsmodels.tsa.seasonal import seasonal_decompose

time_series_pd = df_plot
time_series = time_series_pd['Energy'].tolist()

# Decompose the time series using seasonal_decompose
result = seasonal_decompose(
    time_series_pd,
    model='additive',
    # period=672,
    period=decompose_period,
    extrapolate_trend=True,
    )



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



# Update the y-axis range for all subplots
# fig.update_yaxes(range=[0, 200], row=1, col=1)
# fig.update_yaxes(range=[0, 200], row=2, col=1)
# fig.update_yaxes(range=[0, 200], row=3, col=1)
# fig.update_yaxes(range=[0, 200], row=4, col=1)

fig.update_layout(height=800, width=800, title_text="Time Series Decomposition")




# Plot the Fourier Transform magnitudes using Plotly
fig2 = go.Figure()
fourier_transform_trace = go.Scatter(x=frequencies, y=magnitudes, mode='markers', name='Fourier Transform')
fig2.add_trace(fourier_transform_trace)
fig2.update_layout(title='Fourier Transform', xaxis_title='Frequency (1/hour)', yaxis_title='Magnitude')



with col1:
    tab1, tab2 = st.tabs(['Time Series Decomposition', 'Fourier Transform'])

    tab1.plotly_chart(fig, use_container_width=True)
    tab2.plotly_chart(fig2)






#####

time_series_pd = result.resid


time_series = time_series_pd.tolist()
# st.dataframe(time_series_pd)



# Decompose the time series using seasonal_decompose
result = seasonal_decompose(
    time_series_pd,
    model='additive',
    # period=672,
    period=7,
    extrapolate_trend=True,
    )


# Compute the Fourier Transform of the time series
fourier_transform = np.fft.fft(time_series)
frequencies = np.fft.fftfreq(len(time_series), d=1)  # d=1 for hourly data
magnitudes = np.abs(fourier_transform)

# Streamlit App
# col1.markdown("#### Time Series Decomposition and Fourier Transform")

# Plot the decomposition results using Plotly
fig_res = sp.make_subplots(rows=4, cols=1, subplot_titles=("Observed", "Trend", "Seasonal", "Residual"))

# Observed
observed_trace = go.Scatter(x=result.observed.index, y=result.observed, mode='lines', name='Observed')
fig_res.add_trace(observed_trace, row=1, col=1)

# Trend
trend_trace = go.Scatter(x=result.trend.index, y=result.trend, mode='lines', name='Trend', line=dict(color='orange'))
fig_res.add_trace(trend_trace, row=2, col=1)

# Seasonal
seasonal_trace = go.Scatter(x=result.seasonal.index, y=result.seasonal, mode='lines', name='Seasonal', line=dict(color='green'))
fig_res.add_trace(seasonal_trace, row=3, col=1)

# Residual
residual_trace = go.Scatter(x=result.resid.index, y=result.resid, mode='lines', name='Residual', line=dict(color='red'))
fig_res.add_trace(residual_trace, row=4, col=1)



# Update the y-axis range for all subplots
# fig_res.update_yaxes(range=[0, 50], row=1, col=1)
# fig_res.update_yaxes(range=[0, 50], row=2, col=1)
# fig_res.update_yaxes(range=[0, 50], row=3, col=1)
# fig_res.update_yaxes(range=[0, 50], row=4, col=1)

fig_res.update_layout(height=800, width=800, title_text="Time Series Decomposition")




# Plot the Fourier Transform magnitudes using Plotly
fig_res_fourier = go.Figure()
fourier_transform_trace = go.Scatter(x=frequencies, y=magnitudes, mode='lines', name='Fourier Transform')

fig_res_fourier.add_trace(fourier_transform_trace)
fig_res_fourier.update_yaxes(range=[0, 1000])
fig_res_fourier.update_xaxes(range=[0, 0.5])
fig_res_fourier.update_layout(title='Fourier Transform', xaxis_title='Frequency (1/hour)', yaxis_title='Magnitude')




with col1:
    st.divider()
    st.markdown('#### Analysing residuals')

    # st.dataframe(time_series_pd)
    tab1, tab2 = st.tabs(['Time Series Decomposition', 'Fourier Transform'])

    tab1.plotly_chart(fig_res, use_container_width=True)
    tab2.plotly_chart(fig_res_fourier, use_container_width=True)





