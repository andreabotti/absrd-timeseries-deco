# IMPORT LIBRARIES
from fn__libs_data import *
import os, datetime, pickle, pandas as pd, numpy as np, streamlit as st
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





##### FUNCTION TO LOAD DICT DATA
# Function to load data from pickle files
def load_data():
    with open( os.path.join(DataFolder,'data_dict.pkl'), 'rb') as f:
        data_dict = pickle.load(f)

    with open( os.path.join(DataFolder,'room_info.pkl'), 'rb') as f:
        room_info = pickle.load(f)
    
    return data_dict, room_info





##### FILE PATHS AND DATA LOAD
# file_path = os.path.join(DataFolder, 'AmbaAradan_4_aps.csv')
DataFolder = 'data/'
data_dict, room_info = load_data()




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
        df_var = df[var]
        df_var = df_var[start_date:end_date]
        col2.dataframe(df_var)

    # st.write(list(df.columns))





from statsmodels.tsa.seasonal import seasonal_decompose

time_series_pd = df_var
time_series = time_series_pd.tolist()

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



