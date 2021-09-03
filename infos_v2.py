import streamlit as st
import requests
import matplotlib.pyplot as plt
import matplotlib.pylab as pl
import numpy as np
import pandas as pd
import base64
import json
import uuid
import re
import bokeh.plotting as bkp
import bokeh.models as bkm
from bokeh.models import ColumnDataSource, DataRange1d, Plot, LinearAxis, Grid, Legend, LegendItem
from bokeh.models import NumeralTickFormatter

st.set_page_config(layout="centered")

def download_button(object_to_download, download_filename, button_text):
    """
    Generates a link to download the given object_to_download.
    Params:
    ------
    object_to_download:  The object to be downloaded.
    download_filename (str): filename and extension of file. e.g. mydata.csv,
    some_txt_output.txt download_link_text (str): Text to display for download
    link.
    button_text (str): Text to display on download button (e.g. 'click here to download file')
    pickle_it (bool): If True, pickle file.
    Returns:
    -------
    (str): the anchor tag to download object_to_download
    Examples:
    --------
    download_link(your_df, 'YOUR_DF.csv', 'Click to download data!')
    download_link(your_str, 'YOUR_STRING.txt', 'Click to download text!')
    """

    button_uuid = str(uuid.uuid4()).replace('-', '')
    button_id = re.sub('\d+', '', button_uuid)

    custom_css = f"""
        <style>
            #{button_id} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }}
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    b64 = base64.b64encode(object_to_download.encode()).decode()
    dl_link = custom_css + f'<a download="{download_filename}" id="{button_id}" href="data:text/plain;base64,{b64}">{button_text}</a><br></br>'

    return dl_link

c1, c2 = st.beta_columns((2, 1))

c1.title("""
    Proposal Analysis
""")

uploaded_file = c1.file_uploader(
    label='Faça upload dos arquivos de proposta',
    type='csv',
    accept_multiple_files=True
)

with open('btg2.csv', 'r') as f:
    dl_button = download_button(f.read(), 'arquivo_proposta_exemplo.csv', 'Baixe aqui o arquivo exemplo de proposta!')
    c1.markdown(dl_button, unsafe_allow_html=True)

st.markdown("""---""",True)

if uploaded_file is not None:

    arquivos = {}
    arquivos_giga = {}

    for arquivo in uploaded_file:
        arquivos[arquivo.name] = pd.read_csv(arquivo, sep=';', decimal=',')

    for nome,tabela in arquivos.items():

        st.write(nome)

        tabela['QtdPontos'] = tabela['Ate']-tabela['A partir de']+1
        tabela['ValorIntervalo'] = tabela['Valor BRL'] * tabela['QtdPontos']
        tabela['CumValorIntervalo'] = tabela['ValorIntervalo'].cumsum()
        tabela['TM'] = tabela['CumValorIntervalo']/tabela['Ate']

        tabela.loc[-1] = ''
        tabela.loc[-1]['Ate'] = 1
        tabela.loc[-1]['A partir de'] = 1
        tabela.loc[-1]['TM'] = tabela.iloc[0]['TM']
        tabela.loc[-1]['CumValorIntervalo'] = 0
        tabela.loc[-1]['Intervalo'] = tabela.iloc[0]['Intervalo']
        tabela.loc[-1]['Intervalo'] = tabela.iloc[0]['Intervalo']

        tabela.index = tabela.index+1

        tabela.sort_index(inplace=True)

        st.write(tabela['Ate'])

        giga_tabela = pd.DataFrame(data=np.arange(tabela['Ate'].min()-1,tabela['Ate'].max()+2500,2500),columns=['Ate'])

        giga_tabela.loc[0] = 1

        teste = giga_tabela.merge(tabela[['Ate','Intervalo','CumValorIntervalo','TM']], on='Ate', how='outer')

        #st.write(teste)

        teste.sort_values(
            by='Ate',
            ascending=True,
            inplace=True
        )

        #st.write('sorted', teste)

        teste.reset_index(drop=True,inplace=True)

        #st.write('sorted2', teste)

        teste.set_index(
            keys='Ate',
            drop=True,
            inplace=True
        )

        #st.write('indexado', teste)

        teste['Intervalo'] = teste['Intervalo'].fillna(method='bfill')
        teste['CumValorIntervalo'] = teste['CumValorIntervalo'].astype(float).interpolate(method='index')
        teste['TM'] = teste['TM'].astype(float).interpolate(method='index')

        #st.write('calculado',teste)

        teste.reset_index(inplace=True)

        #st.write('normalizado', teste)

        arquivos_giga[nome+'_giga'] = teste.copy()

    trocas = {
        'á': 'a',
        'ã': 'a',
        'à': 'a',
        'â': 'a',
        'é': 'e',
        'ê': 'e',
        'í': 'i',
        'ó': 'o',
        'ô': 'o',
        'õ': 'o',
        'ú': 'u',
        'ç': 'c',
        ' ': ''
    }

    p = bkp.figure(
        height=400,
    )

    p.yaxis.axis_label = 'Ticket Médio (BRL)'
    p.xaxis.axis_label = 'Número de Clientes'

    plots_l = {}
    plots_s = {}
    legendas = {}

    for chave, tabela in arquivos_giga.items():

        table_t = tabela

        #st.write(table_t)

        for coluna in table_t.columns:
            coluna_corrigida = coluna
            for crt_errado,crt_certo in trocas.items():
                coluna_corrigida = coluna_corrigida.lower().replace(crt_errado, crt_certo)

            table_t = table_t.rename(
                    {
                    f'{coluna}': f'{coluna_corrigida}'
                    },
                axis='columns'
                )

        source = bkm.ColumnDataSource(data=table_t)

        cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))

        plots_l[chave] = bkm.Line(
            x='ate',
            y='tm',
            line_color = cor,
            line_width=2
        )

        p.add_glyph(source_or_glyph=source, glyph=plots_l[chave])

        plots_s[chave] = bkm.Scatter(
            x='ate',
            y='tm',
            fill_color = cor,
            size = 8
        )

        p.add_glyph(source_or_glyph=source, glyph=plots_s[chave])

        legendas[chave] = LegendItem(label=chave, renderers=[p.renderers[2*(len(plots_l))-1]])

        p.add_tools(
            bkm.HoverTool(
                renderers = [p.renderers[2*(len(plots_l)-1)]],
                tooltips=[
                    ('Proposta', f"{chave}"),
                    ('Intervalo', "@intervalo"),
                    ('Ticket Médio', "@tm{$ 0.00}"),
                    ('Número de Clientes', "@ate{0}"),
                ],
                line_policy='nearest',
                mode='vline'
            )
        )

    legend = Legend(items=list(legendas.values()), location='top_right')
    p.add_layout(legend)

    p.yaxis[0].ticker.desired_num_ticks = 7
    p.xaxis[0].ticker.desired_num_ticks = 7
    p.yaxis.formatter=NumeralTickFormatter(format="$ 0.00")
    p.xaxis.formatter=NumeralTickFormatter(format="0")
    p.xaxis.major_label_text_font_size = '12pt'
    p.yaxis.major_label_text_font_size = '12pt'
    #p.legend.click_policy = 'mute' #or hide

    #if st.button('Gerar gráfico'):

    st.markdown("""
        ### COMPARAÇÃO ENTRE PROPOSTAS
    """)

    st.bokeh_chart(
        p,
        use_container_width=True
    )














thanks_line = """Special thanks to Charly Wargnier for the suggestions and jrieke for making the custom CSS download button!"""
st.markdown("""    <style>
footer {
	visibility: hidden;
	}
footer:after {
	content:'"""+ thanks_line+ """';
	visibility: visible;
	display: block;
	position: relative;
	#background-color: red;
	padding: 5px;
	top: 2px;
}</style>""", unsafe_allow_html=True)
