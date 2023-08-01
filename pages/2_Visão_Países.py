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

st.set_page_config(page_title='Dashboard Países', page_icon='🌎', layout='wide')

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

def qtde_rest_paises(df):
    cols = ['country_name','restaurant_name']
    df_aux = df[cols].groupby('country_name').nunique().sort_values('restaurant_name', ascending=False).reset_index()
    fig = px.bar(df_aux, 
                 x='country_name', 
                 y='restaurant_name', 
                 labels=dict(restaurant_name='Qtde de restaurantes', 
                             country_name='Países'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Quantidade de restaurantes: %{y}<br>')

    return fig

def qtde_cozinhas_paises(df):
    cols = ['country_name','cuisines']
    df_aux = df[cols].groupby('country_name').nunique().sort_values('cuisines', ascending=False).reset_index()
    fig = px.bar(df_aux, 
                 x='country_name', 
                 y='cuisines',
                 labels=dict(cuisines='Qtde de culinárias', 
                             country_name='Países'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Quantidade de culinárias: %{y}<br>')

    return fig

def preco_medio_dois_paises(df):
    cols = ['country_name','average_cost_for_two_brl']
    df_aux = df[cols].groupby('country_name').mean().sort_values('average_cost_for_two_brl', ascending=False).reset_index()
    df_aux['average_cost_for_two_brl'] = df_aux['average_cost_for_two_brl'].round(2)
    fig = px.bar(df_aux, 
                 x='country_name', 
                 y='average_cost_for_two_brl',
                 labels=dict(average_cost_for_two_brl='Preço médio, em reais', 
                             country_name='Países'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Preço médio: R$ %{y}<br>')

    return fig

def categoria_preco_paises(df):
    
    cols = ['country_name','price_category']
    df_aux = df[cols].groupby(['country_name','price_category'], as_index=False).size()
    fig = px.sunburst(df_aux,
                      path=['country_name','price_category'],
                      values='size',
                      color='price_category',
                      color_continuous_scale='magma',
                      width=800, 
                      height=800)
    fig.update_traces(hovertemplate='<b>%{label}</b>'+
                      '<br>Quantidade de restaurantes: %{value}<br>')

    return fig

def top_notas_paises(df):
    cols = ['country_name','aggregate_rating']
    df_aux = df[cols].groupby('country_name').mean().sort_values('aggregate_rating', ascending=False).reset_index().head(5)
    df_aux['aggregate_rating'] = df_aux['aggregate_rating'].round(2)
    fig = px.bar(df_aux, 
                 x='country_name', 
                 y='aggregate_rating',
                 labels=dict(aggregate_rating='Nota média', 
                             country_name='Países'), 
                 text_auto=True)
    fig.update_traces(textposition='outside',
                      hovertemplate=
                      '<b>%{x}</b>'+
                      '<br>Nota média: %{y}<br>')

    return fig

def bottom_notas_paises(df):
    cols = ['country_name','aggregate_rating']
    df_aux = df[cols].groupby('country_name').mean().sort_values('aggregate_rating', ascending=True).reset_index().head(5)
    df_aux['aggregate_rating'] = df_aux['aggregate_rating'].round(2)
    fig = px.bar(df_aux, 
                 x='country_name', 
                 y='aggregate_rating',
                 labels=dict(aggregate_rating='Nota média', 
                             country_name='Países'), 
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

st.title('🌎 Dashboard Países')

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

country_list = ['Philippines', 'Brazil', 'Australia', 'United States of America', 'Canada',
                'Singapure', 'United Arab Emirates', 'India', 'Indonesia', 'New Zeland',
                'England', 'Qatar', 'South Africa', 'Sri Lanka', 'Turkey']

country_selection = st.sidebar.multiselect(
    label='Selecione os países:',
    options=country_list,
    default=country_list
)

linhas_selecionadas = df['country_name'].isin(country_selection)
df = df.loc[linhas_selecionadas, :]

st.sidebar.markdown("""---""")

st.sidebar.markdown('## Criado por Rodolfo Stremel')

# =========================================================================
# Layout no Streamlit
# =========================================================================

with st.container():
    st.markdown('### Quantidade de Restaurantes por País')
    st.markdown('###### O país com mais restaurantes é a **Índia**.')
    fig = qtde_rest_paises(df)
    st.plotly_chart(fig, use_container_width=True)
    
st.markdown("""---""")

with st.container():
    st.markdown('### Quantidade de Culinárias Distintas por País')
    st.markdown('###### O país com mais culinárias distintas é a **Índia**.')
    fig = qtde_cozinhas_paises(df)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("""---""")

with st.container():
    st.markdown('### Preço Médio para Dois por País, em Reais')
    st.markdown('###### O país com o maior preço médio para dois, em reais, é a **Singapura**.')
    fig = preco_medio_dois_paises(df)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("""---""")

with st.container():
    st.markdown('### Distribuição de Categorias de Preço por País')
    fig = categoria_preco_paises(df)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("""---""")

with st.container():
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('### Os Países com as Melhores Notas Médias')
        st.markdown('###### O país com a melhor nota média é a **Indonésia**.')
        fig = top_notas_paises(df)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('### Os Países com as Piores Notas Médias')
        st.markdown('###### O país com a pior nota média é o **Brasil**.')
        fig = bottom_notas_paises(df)
        st.plotly_chart(fig, use_container_width=True)
            


#bubble chart com x=nota media e y=custo medio
#sunburst com cidade, cozinha e nota media




