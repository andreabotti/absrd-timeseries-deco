# IMPORT LIBRARIES
from fn__libs_data import *
# import streamlit as st



def create_page_header(cat_dict, color_dict):

    ##### PAGE CONFIG
    st.set_page_config(page_title="Timeseries Analysis App",   page_icon=':mostly_sunny:', layout="wide")
    st.markdown(
        """<style>.block-container {padding-top: 1rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem;}</style>""",
        unsafe_allow_html=True)


    ##### TOP CONTAINER
    top_col1, top_col2 = st.columns([3,5])
    with top_col1:

        st.write('')

        st.markdown("## Data Analysis App for Unipol POE")
        # st.markdown("#### Analisi di dati meteorologici ITAliani per facilitare l'Adattamento ai Cambiamenti Climatici")
        st.caption('Developed by AB.S.RD - https://absrd.xyz/')

    custom_hr()


    with top_col2:

        st.write('. \n')


        # Concatenate HTML labels with colors in a single line
        color_labels = " ".join(
            [
                f"<span style='background-color:{color_dict[key]}; padding: 5px 10px; color:white; border-radius:3px; margin-right:5px'>{value['Cat_eng']}</span>"
                for key, value in cat_dict.items() if key in cat_dict
            ]
        )

        # Display the concatenated HTML string as markdown
        st.markdown(color_labels, unsafe_allow_html=True)