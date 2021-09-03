import streamlit as st
import pandas as pd
from PIL import Image
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import time
import os
import xlrd
import openpyxl
import numpy as np
import subprocess
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.models import HoverTool
import bokeh.models as bkm
import bokeh.plotting as bkp
from bokeh.models import NumeralTickFormatter
from bokeh.models import ColumnDataSource, DataRange1d, Plot, LinearAxis, Grid, Legend, LegendItem
from operator import itemgetter
from babel.numbers import format_currency
from babel.numbers import format_decimal
from dateutil import parser
from bokeh.models import Range1d, LinearAxis

def upload():

    #pedindo para o usuário subir o(s) arquivo(s) de interesse

    st.markdown("""
        ### Faça upload do(s) .csv da(s) proposta(s)
    """)

    arquivos = st.file_uploader(
        label = '',
        type = 'csv',
        accept_multiple_files = True
    )

    st.write(arquivos)

def main ():

    st.set_page_config(page_title='Proposal Analysis', page_icon="https://static.streamlit.io/examples/cat.jpg", layout='centered')

    pd.options.display.float_format = '${:,.2f}'.format

    st.title("""

    Proposal Analysis

    """)

    st.image(Image.open('nelo.png'), output_format='png', width=300)

    st.markdown(
        """ <style>
                div[role="radiogroup"] >  :first-child{
                    display: none !important;
                }
            </style>
            """,
        unsafe_allow_html=True
    )

    st.markdown('---')

    upload()
