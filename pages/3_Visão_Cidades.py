#importando bibliotecas
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import folium
import geopy.distance
import streamlit as st
from datetime import datetime
from PIL import Image
from streamlit_folium import folium_static
import inflection

st.set_page_config(page_title='Dashboard Cidades', page_icon='🌆', layout='wide')

# =========================================================================
# Funções
# =========================================================================

def code_cleaning(df):

    #removendo linhas vazias
    df = df.dropna()
    
    #removendo a coluna 'Switch to order menu' (todos os valores são 0 e não há descrição da coluna)
    df = df.drop(['Switch to order menu'], axis=1)
    
    #removendo linhas duplicadas
    df = df.drop_duplicates().reset_index(drop=True)
    
    #categorizando os restaurantes somente pela primeira categoria informada
    df['Cuisines'] = df['Cuisines'].apply(lambda x: x.split(',')[0])

    return df

#Preenchimento do nome dos países
country_dict = {
    1: "India",
    14: "Australia",
    30: "Brazil",
    37: "Canada",
    94: "Indonesia",
    148: "New Zeland",
    162: "Philippines",
    166: "Qatar",
    184: "Singapure",
    189: "South Africa",
    191: "Sri Lanka",
    208: "Turkey",
    214: "United Arab Emirates",
    215: "England",
    216: "United States of America",
}

def country_name(country_id):
    return country_dict[country_id]

#Criação do Tipo de Categoria de Comida
def create_price_type(price_range):
    if price_range == 1:
        return 'Cheap'
    elif price_range == 2:
        return 'Normal'
    elif price_range == 3:
        return 'Expensive'
    else:
        return 'Gourmet'

#Criação do nome das Cores
color_dict = {
    "3F7E00": "darkgreen",
    "5BA829": "green",
    "9ACD32": "lightgreen",
    "CDD614": "orange",
    "FFBA00": "red",
    "CBCBC8": "darkred",
    "FF7800": "darkred",
}

def color_name(color_code):
    return color_dict[color_code]

#Renomear as colunas do DataFrame
def rename_columns(df):
    df = df.copy()
    title = lambda x: inflection.titleize(x)
    snakecase = lambda x: inflection.underscore(x)
    spaces = lambda x: x.replace(" ", "")
    cols_old = list(df.columns)
    cols_old = list(map(title, cols_old))
    cols_old = list(map(spaces, cols_old))
    cols_new = list(map(snakecase, cols_old))
    df.columns = cols_new
    return df

#Criando nova coluna com valores da 'average_cost_for_two' convertidos para BRL
currency_to_BRL = {
    'Botswana Pula(P)': 0.36,
    'Brazilian Real(R$)': 1,
    'Dollar($)': 4.92,
    'Emirati Diram(AED)': 1.34, 
    'Indian Rupees(Rs.)': 0.059,
    'Indonesian Rupiah(IDR)': 0.00032, 
    'NewZealand($)': 3.03, 
    'Pounds(£)': 6.27,
    'Qatari Rial(QR)': 1.35,
    'Rand(R)': 0.26,
    'Sri Lankan Rupee(LKR)': 0.016,
    'Turkish Lira(TL)': 0.19
}

def convert_to_BRL(average_cost_for_two):
    return currency_to_BRL[average_cost_for_two]

def qtde_rest_cidades(df):
    cols = ['city','restaurant_name','country_name']
    df_aux = df[cols].groupby(['country_name','city']).nunique().sort_values('restaurant_name', ascending=False).reset_index()
    fig = px.bar(df_aux, 
                 x='city', 
                 y='restaurant_name', 
                 color='country_name', 
                 labels=dict(restaurant_name='Qtde de restaurantes',
                             city='Cidades',
                             country_name='País'))
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Quantidade de restaurantes: %{y}<br>')
    fig.update_xaxes(tickangle=-90)

    return fig

def preco_medio_dois_cidades(df):
    cols = ['city','country_name','average_cost_for_two_brl']
    df_aux = df[cols].groupby(['country_name','city']).mean().sort_values('average_cost_for_two_brl', ascending=False).reset_index()
    df_aux['average_cost_for_two_brl'] = df_aux['average_cost_for_two_brl'].round(2)
    fig = px.bar(df_aux, 
                 x='city', 
                 y='average_cost_for_two_brl', 
                 color='country_name', 
                 labels=dict(average_cost_for_two_brl='Preço médio, em reais', 
                             city='Cidades',
                             country_name='País'))
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Preço médio: R$ %{y}<br>')
    fig.update_xaxes(tickangle=-90)

    return fig

def qtde_cozinhas_cidades(df):
    cols = ['city','country_name','cuisines']
    df_aux = df[cols].groupby(['city','country_name']).nunique().sort_values('cuisines', ascending=False).reset_index().head(20)
    fig = px.bar(df_aux, 
                 x='city', 
                 y='cuisines', 
                 color='country_name',
                 labels=dict(cuisines='Qtde de culinárias', 
                             city='Cidades',
                             country_name='País'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Nota média: %{y}<br>')
    fig.update_xaxes(tickangle=-90)

    return fig

def top_notas_cidades(df):
    cols = ['city','aggregate_rating']
    df_aux = df[cols].groupby('city').mean().sort_values('aggregate_rating', ascending=False).reset_index().head(5)
    df_aux['aggregate_rating'] = df_aux['aggregate_rating'].round(2)
    fig = px.bar(df_aux, 
                 x='city', 
                 y='aggregate_rating',
                 labels=dict(aggregate_rating='Nota média', 
                             city='Cidades'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Nota média: %{y}<br>')

    return fig

def bottom_notas_cidades(df):
    cols = ['city','aggregate_rating']
    df_aux = df[cols].groupby('city').mean().sort_values('aggregate_rating', ascending=True).reset_index().head(5)
    df_aux['aggregate_rating'] = df_aux['aggregate_rating'].round(2)
    fig = px.bar(df_aux, 
                 x='city', 
                 y='aggregate_rating',
                 labels=dict(aggregate_rating='Nota média', 
                             city='Cidades'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Nota média: %{y}<br>')

    return fig


# =========================================================================
# Início da estrutura lógica do código
# =========================================================================

#carregando dataset
csv_path = 'files/dataset/zomato.csv'
df = pd.read_csv(csv_path)

df = code_cleaning(df)

df['Country Name'] = df['Country Code'].map(country_name)

df['Price Category'] = df['Price range'].map(create_price_type)

df['Rating Color Name'] = df['Rating color'].map(color_name)

df['average_cost_for_two_brl'] = df['Average Cost for two'] * df['Currency'].map(convert_to_BRL)

df = rename_columns(df)

#removendo a linha 356, pois o average_cost_for_two_brl é um outlier (mais de R$123mi para duas pessoas)
df = df.drop([356,0]).reset_index(drop=True)

# =========================================================================
# Header no Streamlit
# =========================================================================

st.title('🌆 Dashboard Cidades')

# =========================================================================
# Sidebar no Streamlit
# =========================================================================

image_path = 'zomato_logo.png'
image = Image.open(image_path)

st.markdown(
    """
    <style>
        [data-testid=stSidebar] [data-testid=stImage]{
            text-align: center;
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 100%;
        }
    </style>
    """, unsafe_allow_html=True
)

st.sidebar.image(image, width=160)

# st.sidebar.markdown('# Dashboard Países')

st.sidebar.markdown("""---""")

# =========================================================================
# Filtros no Streamlit
# =========================================================================

#Input de preço médio
avg_price_input_min = st.sidebar.number_input(
    'Selecione o preço médio **mínimo** para dois, em reais:',
    min_value=df['average_cost_for_two_brl'].min(),
    max_value=df['average_cost_for_two_brl'].max(),
    value=df['average_cost_for_two_brl'].min(),
    step=1.0
)

avg_price_input_max = st.sidebar.number_input(
    'Selecione o preço médio **máximo** para dois, em reais:',
    min_value=df['average_cost_for_two_brl'].min(),
    max_value=df['average_cost_for_two_brl'].max(),
    value=df['average_cost_for_two_brl'].max(),
    step=1.0
)

linhas_selecionadas = df['average_cost_for_two_brl'].between(avg_price_input_min, avg_price_input_max)
df = df.loc[linhas_selecionadas, :]

st.sidebar.markdown("""---""")

#Slider de nota média
rating_slider = st.sidebar.slider(
    'Selecione a faixa de avaliação média:',
    float(df['aggregate_rating'].min()), 
    float(df['aggregate_rating'].max()), 
    (float(df['aggregate_rating'].min()), float(df['aggregate_rating'].max())),
    step=0.1
)

linhas_selecionadas = df['aggregate_rating'].between(rating_slider[0], rating_slider[1])
df = df.loc[linhas_selecionadas, :]

st.sidebar.markdown("""---""")

st.sidebar.markdown('## Criado por Rodolfo Stremel')

# =========================================================================
# Layout no Streamlit
# =========================================================================

with st.container():
    st.markdown('### Quantidade de Restaurantes por Cidade')
    st.markdown('###### A cidade com mais restaurantes é a **Cidade de Singapura**, na Singapura.')
    fig = qtde_rest_cidades(df)
    st.plotly_chart(fig, use_container_width=True)
    
st.markdown("""---""")

with st.container():
    st.markdown('### Preço Médio para Dois por Cidade, em Reais')
    st.markdown('###### A cidade com o maior preço médio para dois, em reais, é **Pasay**, nas Filipinas.')
    fig = preco_medio_dois_cidades(df)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("""---""")

with st.container():
    st.markdown('### Quantidade de Culinárias Distintas por Cidade')
    st.markdown('###### A cidade com mais culinárias distintas é **Birmingham**, na Inglaterra.')
    fig = qtde_cozinhas_cidades(df)
    st.plotly_chart(fig, use_container_width=True)
st.markdown("""---""")

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### As Cidades com as Melhores Notas Médias')
        st.markdown('###### A cidade com as melhores notas médias é **Muntinlupa**, nas Filipinas.')
        fig = top_notas_cidades(df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('### As Cidades com as Melhores Notas Médias')
        st.markdown('###### A cidade com as piores notas médias é **Gangtok**, na Índia.')
        fig = bottom_notas_cidades(df)
        st.plotly_chart(fig, use_container_width=True)
