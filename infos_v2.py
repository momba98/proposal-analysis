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

st.set_page_config(layout="wide")

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

with open('ctg 2.csv', 'r') as f:
    dl_button = download_button(f.read(), 'arquivo_proposta_exemplo.csv', 'Baixe aqui o arquivo exemplo de proposta!')
    c1.markdown(dl_button, unsafe_allow_html=True)

st.markdown("""---""",True)

if uploaded_file is not None:

    arquivos = {}
    arquivos_giga = {}

    for arquivo in uploaded_file:
        nome_arquivo = arquivo.name.replace('_',' ')[:-4]
        arquivos[nome_arquivo] = pd.read_csv(arquivo, sep=';', decimal=',')

    for index,nome in arquivos.items():
        delete = st.text_input(f'Qual é a base ativa de {index}?')
        if delete:
            arquivos[index] = (arquivos[index],delete)
            #to_be_deleted.add(delete)
        if not delete:
            arquivos[index] = (arquivos[index],0)

    n = st.selectbox(
        'Intervalo de validação dos valores de TM e Receita: ',
        options=['',100,500,1000,2500,5000,10000],
    )

    for nome,(tabela,base) in arquivos.items():

        #st.write(nome, tabela, base)

        tabela['QtdPontos'] = tabela['Ate']-tabela['A partir de']+1
        tabela['ValorIntervalo'] = tabela['Valor BRL'] * tabela['QtdPontos']
        tabela['CumValorIntervalo'] = tabela['ValorIntervalo'].cumsum()
        tabela['TM'] = tabela['CumValorIntervalo']/tabela['Ate']
        tabela['Base'] = np.nan

        tabela.loc[-1] = ''
        tabela.loc[-1]['Ate'] = 1
        tabela.loc[-1]['A partir de'] = 1
        tabela.loc[-1]['TM'] = tabela.iloc[0]['TM']
        tabela.loc[-1]['CumValorIntervalo'] = 0
        tabela.loc[-1]['Intervalo'] = tabela.iloc[0]['Intervalo']
        tabela.loc[-1]['Intervalo'] = tabela.iloc[0]['Intervalo']

        tabela.index = tabela.index+1

        tabela.sort_index(inplace=True)

        #st.write(tabela['Ate'])

        # #n = 1
        # a = np.array(tabela['Ate'].astype(float))
        # new_size = a.size + (a.size - 1) * n
        # x = np.linspace(a.min(), a.max(), new_size)
        # xp = np.linspace(a.min(), a.max(), a.size)
        # fp = a
        # result = np.interp(x, xp, fp)
        #st.write('interpol', result)

        if n == '':
            data = tabela['Ate']
        else:
            data = np.arange(tabela['Ate'].min()-1,tabela['Ate'].max()+n,n)

        giga_tabela = pd.DataFrame(data=data,columns=['Ate']) #np.arange(tabela['Ate'].min()-1,tabela['Ate'].max()+2500,2500

        giga_tabela.loc[0] = 1

        teste = giga_tabela.merge(tabela[['Ate','Intervalo','CumValorIntervalo','TM', 'Base']], on='Ate', how='outer')

        #st.write('aqui',teste)

        teste = teste.append(
            {
                'Ate' : int(base),
                'Base' : True
            }, True
        )

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

        arquivos_giga[nome] = teste.copy()

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

    #criação das figuras

    figuras = {}

    infos_grafico = {}

    infos_grafico['tm'] = [
        'Ticket Médio esperado com evolução da base ativa',
        'Ticket Médio (BRL)',
        'tm',
        'top_right',
        "@tm{$ 0.00}"
    ]

    infos_grafico['cumvalorintervalo'] = [
        'Receita mensal esperada com evolução da base ativa',
        'Receita Mensal (BRL)',
        'cumvalorintervalo',
        'top_left',
        "@cumvalorintervalo{$ 0,0}"
    ]

    hover_complexo = st.checkbox('Mostrar mais de uma informação ao mesmo tempo ao passar o mouse em cima dos pontos')

    for figura in [infos_grafico['tm'], infos_grafico['cumvalorintervalo']]:

        figuras[figura[2]] = bkp.figure(
            height=500,
            title=figura[0]
        )

        figuras[figura[2]].title.text_font_size = '16pt'

        figuras[figura[2]].yaxis.axis_label = figura[1]
        figuras[figura[2]].xaxis.axis_label = 'Número de Clientes'

        plots_l = {}
        plots_s = {}
        legendas = {}

        for chave, tabela in arquivos_giga.items():

            table_t = tabela

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

            st.write(chave.split(' ')[0].upper())

            if chave.split(' ')[0].upper() == 'XP':
                cor = (np.random.randint(249-75,255),np.random.randint(193-75,255),np.random.randint(0,4+75))
                st.write(chave, cor)
            elif chave.split(' ')[0].upper() == 'BTG':
                cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))
            elif chave.split(' ')[0].upper() == 'MODAL':
                cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))
            elif chave.split(' ')[0].upper() == 'GENIAL':
                cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))
            elif chave.split(' ')[0].upper() == 'CLEAR':
                cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))
            elif chave.split(' ')[0].upper() == 'RICO':
                cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))
            elif chave.split(' ')[0].upper() == 'TORO':
                cor = (np.random.randint(50,255),np.random.randint(50,255),np.random.randint(50,255))

            plots_l[chave] = bkm.Line(
                x='ate',
                y=figura[2],
                line_color = cor,
                line_width=2
            )

            figuras[figura[2]].add_glyph(source_or_glyph=source, glyph=plots_l[chave])

            plots_s[chave] = bkm.Scatter(
                x='ate',
                y=figura[2],
                fill_color = cor,
                size = 8
            )

            figuras[figura[2]].add_glyph(source_or_glyph=source, glyph=plots_s[chave])

            legendas[chave] = LegendItem(label=chave, renderers=[figuras[figura[2]].renderers[2*(len(plots_l))-1]])

            figuras[figura[2]].add_tools(
                bkm.HoverTool(
                    renderers = [figuras[figura[2]].renderers[2*(len(plots_l))-1]],
                    tooltips=[
                        ('Proposta', f"{chave}"),
                        ('Intervalo', "@intervalo"),
                        (figura[1], figura[4]),
                        ('Número de Clientes', "@ate{0}"),
                    ],
                    line_policy='nearest',
                    mode='vline' if hover_complexo else 'mouse'
                )
            )

        if any([base_ativa[1] for base_ativa in arquivos.values()]) > 0:

            for chave, tabela in arquivos_giga.items():

                table_t = tabela[tabela['Base'] == True]

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

                cor = (255,0,0)

                plots_s[chave+'base'] = bkm.Scatter(
                    x='ate',
                    y=figura[2],
                    fill_color = cor,
                    fill_alpha = 1,
                    size = 12.5
                )

                figuras[figura[2]].add_glyph(source_or_glyph=source, glyph=plots_s[chave+'base'])

                legendas['Base Ativa'] = LegendItem(label='Base Ativa', renderers=[figuras[figura[2]].renderers[len(plots_s)]])

        legend = Legend(items=list(legendas.values()), location=figura[3])
        figuras[figura[2]].add_layout(legend)

        figuras[figura[2]].yaxis[0].ticker.desired_num_ticks = 7
        figuras[figura[2]].xaxis[0].ticker.desired_num_ticks = 7
        figuras[figura[2]].yaxis.formatter=NumeralTickFormatter(format="$ 0,0")
        figuras[figura[2]].xaxis.formatter=NumeralTickFormatter(format="0")
        figuras[figura[2]].xaxis.major_label_text_font_size = '12pt'
        figuras[figura[2]].yaxis.major_label_text_font_size = '12pt'
        #p.legend.click_policy = 'hide' #or hide

        #if st.button('Gerar gráfico'):

        st.bokeh_chart(
            figuras[figura[2]],
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
