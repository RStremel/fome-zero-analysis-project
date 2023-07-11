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

st.set_page_config(page_title='Dashboard Culinárias', page_icon='👨‍🍳', layout='wide')

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
        return 'cheap'
    elif price_range == 2:
        return 'normal'
    elif price_range == 3:
        return 'expensive'
    else:
        return 'gourmet'

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

def cozinhas_mais_comuns(df):
    cols = ['restaurant_id','cuisines']
    df_aux = df[cols].groupby('cuisines').count().sort_values('restaurant_id', ascending=False).reset_index().head(10)
    fig = px.bar(df_aux, 
                 x='cuisines', 
                 y='restaurant_id',
                 labels=dict(restaurant_id='Qtde de restaurantes', 
                             cuisines='Culinárias'), 
                 text_auto=True)
    fig.update_traces(textposition='outside')

    return fig

def top_notas_cozinhas(df):
    cols = ['cuisines','aggregate_rating']
    df_aux = df[cols].groupby('cuisines').mean().sort_values('aggregate_rating', ascending=False).reset_index().head(5)
    fig = px.bar(df_aux, 
                 x='cuisines', 
                 y='aggregate_rating',
                 labels=dict(aggregate_rating='Nota média', 
                             cuisines='Culinárias'), 
                 text_auto=True)
    fig.update_traces(textposition='outside')

    return fig

def bottom_notas_cozinhas(df):
    cols = ['cuisines','aggregate_rating']
    df_aux = df[cols].groupby('cuisines').mean().sort_values('aggregate_rating', ascending=True).reset_index().head(5)
    fig = px.bar(df_aux, 
                 x='cuisines', 
                 y='aggregate_rating',
                 labels=dict(aggregate_rating='Nota média', 
                             cuisines='Culinárias'), 
                 text_auto=True)
    fig.update_traces(textposition='outside')

    return fig

def top_preco_medio_dois_cozinhas(df):
    cols = ['cuisines','average_cost_for_two_brl']
    df_aux = df[cols].groupby(['cuisines']).mean().sort_values('average_cost_for_two_brl', ascending=False).reset_index().head(5)
    fig = px.bar(df_aux, 
                 x='cuisines', 
                 y='average_cost_for_two_brl',
                 labels=dict(average_cost_for_two_brl='Preço médio, em reais', 
                             cuisines='Culinárias'), 
                 text_auto=True)
    fig.update_traces(textposition='outside')

    return fig

def bottom_preco_medio_dois_cozinhas(df):
    cols = ['cuisines','average_cost_for_two_brl']
    df_aux = df[cols].groupby(['cuisines']).mean().sort_values('average_cost_for_two_brl', ascending=True).reset_index().head(5)
    fig = px.bar(df_aux, 
                 x='cuisines', 
                 y='average_cost_for_two_brl',
                 labels=dict(average_cost_for_two_brl='Preço médio, em reais', 
                             cuisines='Culinárias'), 
                 text_auto=True)
    fig.update_traces(textposition='outside')

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

st.title('👨‍🍳 Dashboard Culinárias')

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

st.sidebar.markdown('# Dashboard Culinárias')

st.sidebar.markdown("""---""")

# =========================================================================
# Filtros no Streamlit
# =========================================================================

cuisines_list = df[['restaurant_id',
                    'cuisines']].groupby('cuisines').count().sort_values('restaurant_id', 
                                                                         ascending=False).reset_index().head(10)['cuisines']

cuisines_selection = st.sidebar.multiselect(
    label='Selecione as culinárias:',
    options=df['cuisines'].unique(),
    default=cuisines_list
)

linhas_selecionadas = df['cuisines'].isin(cuisines_list)
df = df.loc[linhas_selecionadas, :]

st.sidebar.markdown("""---""")

st.sidebar.markdown('## Criado por Rodolfo Stremel')

# =========================================================================
# Layout no Streamlit
# =========================================================================

with st.container():
    st.markdown('### Tipos de Culinária Mais Comuns')
    st.markdown('###### A culinária mais comum é a **Indiana**.')
    fig = cozinhas_mais_comuns(df)
    st.plotly_chart(fig, use_container_width=True)
    
st.markdown("""---""")
    
with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### As Culinárias com as Melhores Notas Médias')
        st.markdown('###### A culinária com a melhor nota média é a **Americana**.')
        fig = top_notas_cozinhas(df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('### As Culinárias com as Piores Notas Médias')
        st.markdown('###### A culinária com a pior nota média é o **Fast Food**.')
        fig = bottom_notas_cozinhas(df)
        st.plotly_chart(fig, use_container_width=True)
    
st.markdown("""---""")

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### As Culinárias com os Maiores Preços Médios para Dois, em Reais')
        st.markdown('###### A culinária com o maior preço médio é a de **Frutos do Mar**.')
        fig = top_preco_medio_dois_cozinhas(df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('### As Culinárias com os Menores Preços Médios para Dois, em Reais')
        st.markdown('###### A culinária com o menor preço médio é o **Fast Food**.')
        fig = bottom_preco_medio_dois_cozinhas(df)
        st.plotly_chart(fig, use_container_width=True)