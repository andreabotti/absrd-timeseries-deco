# IMPORT LIBRARIES
from fn__libs_data import *
# import streamlit as st






def create_page_header():

    ##### PAGE CONFIG
    st.set_page_config(page_title="Timeseries Analysis App",   page_icon=':mostly_sunny:', layout="wide")
    st.markdown(
        """<style>.block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem;}</style>""",
        unsafe_allow_html=True)


    ##### TOP CONTAINER
    top_col1, top_col2 = st.columns([6,1])
    with top_col1:
        st.markdown("# Timeseries Analysis App  for Unipol POE")
        # st.markdown("#### Analisi di dati meteorologici ITAliani per facilitare l'Adattamento ai Cambiamenti Climatici")
        st.caption('Developed by AB.S.RD - https://absrd.xyz/')

    custom_hr()
