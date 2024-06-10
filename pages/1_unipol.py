# IMPORT LIBRARIES
from fn__libs_data import *
import os, requests, datetime, pickle, pandas as pd, numpy as np, streamlit as st
from io import StringIO
from urllib.request import urlopen
import plotly.graph_objs as go, plotly.subplots as sp





##### PAGE CONFIG
st.set_page_config(page_title="IES-VE Viz App",   page_icon=':mostly_sunny:', layout="wide")
st.markdown(
    """<style>.block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem;}</style>""",
    unsafe_allow_html=True)


##### TOP CONTAINER
top_col1, top_col2 = st.columns([6,1])
with top_col1:
    st.markdown("# IES-VE Viz App")
    # st.markdown("#### Analisi di dati meteorologici ITAliani per facilitare l'Adattamento ai Cambiamenti Climatici")
    st.caption('Developed by AB.S.RD - https://absrd.xyz/')

st.divider()




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
LOCAL_PATH  = r'C:/_GitHub/andreabotti/ies-ve_viz/data/'
FTP_PATH    = r'https://absrd.xyz/streamlit_apps/ies-ve_viz/data/'

# DataFolder = 'data/'
# data_dict, room_info = load_data(source='local', data_path=LOCAL_PATH)

df = load_data_csv(source='ftp', data_path=FTP_PATH, filename='Consolidated_ExportData_2023.csv')

df['Datetime'] = pd.to_datetime(df['Datetime'])
df.set_index('Datetime', inplace=True)



#####
col1, col2 = st.columns([5,2])
col2.markdown('###### Sample data exploration for Unipol')
col2.caption(f'from {FTP_PATH}')




col21, col22 = col2.columns([1,1])

# Filter the time series based on the selected date range
start_date = col21.date_input(
    label = "Start date",
    value = datetime.date(2023,8,21),
    )
end_date = col22.date_input(
    label = "End date",
    value = datetime.date(2023,9,3),
    )

# Display the dataframes for the selected Room IDs
df_plot = df[start_date:end_date]
# col1.dataframe(df_plot)





from statsmodels.tsa.seasonal import seasonal_decompose

time_series_pd = df_plot
time_series = time_series_pd['Value'].tolist()

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



with col1:
    tab1, tab2 = st.tabs(['Time Series Decomposition', 'Fourier Transform'])

    tab1.plotly_chart(fig, use_container_width=True)
    tab2.plotly_chart(fig2)




