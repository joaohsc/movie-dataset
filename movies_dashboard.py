import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Análise de Dados de Filmes ",
    page_icon="📊",
    layout="wide"
)

# Título e descrição
st.title("📊 Análise de Dados de Filmes ")
st.markdown("""
    Esta aplicação tem como objetivo realizar uma análise exploratória dos dados contidos em um conjunto com informações sobre filmes. 
    O dataset, que conta com aproximadamente 45 mil registros, oferece diversas oportunidades para investigação e geração de insights relevantes.
""")

# Função para carregar os dados
@st.cache_data
def carregar_dados():
    base_path = 'files/processed_data/'
    collections = pd.read_csv(f'{base_path}collections.csv')
    countries_movies = pd.read_csv(f'{base_path}countries_movies.csv')
    countries = pd.read_csv(f'{base_path}countries.csv')
    genres_movies = pd.read_csv(f'{base_path}genres_movies.csv')
    genres = pd.read_csv(f'{base_path}genres.csv')
    movies = pd.read_csv(f'{base_path}movies.csv')
    production_companies_movies = pd.read_csv(f'{base_path}production_companies_movies.csv')
    production_companies = pd.read_csv(f'{base_path}production_companies.csv')
    spoken_languages_movies = pd.read_csv(f'{base_path}spoken_languages_movies.csv')
    spoken_languages = pd.read_csv(f'{base_path}spoken_languages.csv')

    movies['budget'] = pd.to_numeric(movies['budget'], errors='coerce').round(2)
    movies['revenue'] = pd.to_numeric(movies['revenue'], errors='coerce').round(2)

    # Sidebar com filtro de anos
    movies['release_date'] = pd.to_datetime(movies['release_date'], errors='coerce')
    # Extrair o ano
    movies['year'] = movies['release_date'].dt.year
    #calculo de lucro
    movies['profit'] = movies['revenue'] - movies['budget']
    

    with_budget_df = movies[movies['budget'] > 0]
    with_revenue_df = movies[movies['revenue'] > 0]
    with_runtime_df = movies[movies['runtime'].notna()]
    with_overview_df = movies[movies['overview'].notna()]
    
    return (
        collections,
        countries_movies,
        countries,
        genres_movies,
        genres,
        movies,
        production_companies_movies,
        production_companies,
        spoken_languages_movies,
        spoken_languages,
        with_budget_df,
        with_revenue_df,
        with_runtime_df,
        with_overview_df
    )

(
    collections,
    countries_movies,
    countries,
    genres_movies,
    genres,
    movies,
    production_companies_movies,
    production_companies,
    spoken_languages_movies,
    spoken_languages,
    with_budget_df,
    with_revenue_df,
    with_runtime_df,
    with_overview_df
) = carregar_dados()

# Sidebar para filtros
st.sidebar.header("Filtros")



min_year = int(movies['year'].min())
max_year = int(movies['year'].max())

min_profit = int(movies['profit'].min())
max_profit = int(movies['profit'].max())






year_range = st.sidebar.slider(
    "Figura 1: Selecione o intervalo de anos",
    min_value=min_year,
    max_value=max_year,
    value=(1900, 2014),
    step=1
)

st.sidebar.subheader("Figura 2:")
ano_escolhido = st.sidebar.selectbox("Selecione o ano:", sorted(movies['year'].unique()))
genero_escolhido = st.sidebar.multiselect("Seleciona os gêneros:", genres['name'].unique())

profit_range = st.sidebar.slider(
    "Selecione o intervalo de lucro (em dólares)",
    min_value=min_profit,
    max_value=max_profit,
    value=(min_profit, max_profit),
    step=1000000
)

# Primeira linha com duas colunas
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("Figura 1) Qtd Filmes por Ano")
    st.write("""
        Gráfico temporal para visualizar a evolução de quantidade 
        de filmes ao longo do tempo.
    """)

    # Filtrar anos entre 1900 e 2014
    df_filter = movies[(movies['year'] >= year_range[0]) & (movies['year'] <= year_range[1])]

    movie_counts = df_filter.groupby('year').size().reset_index(name='qtd')

    movie_counts['year'] = pd.to_datetime(movie_counts['year'].astype(str), format='%Y')

    fig = px.line(
        movie_counts, 
        x='year', 
        y=['qtd'],
        title='Qtd filme X Ano',
    )
    st.plotly_chart(fig)


with col2:
    st.subheader("(Figura 2) Análise de lucro a partir de gênero e ano")
    st.write("""Gráfico para visualizar quais gêneros apresentaram
             maior lucro naquele ano
              """)
    
    #calculo do lucro e extração do ano
    
    #anos_disponiveis = sorted(movies['year'].unique())
    
    #Filtros
    #ano_escolhido = st.selectbox("Selecione o ano:", movies['year'].unique)
    #genero_escolhido = st.multiselect("Seleciona os gêneros:", genres['name'].unique())

    #filtrar por ano
    movies_filtrado = movies[movies['year'] == ano_escolhido].copy()

    #Extrair os nomes dos generos dos filmes(como lista de string)
    def extract_genres(genre_str):
        try:
            genres = eval(genre_str)
            if isinstance(genres, list):
                return [g.get('name') for g in genres if isinstance(g, dict)]
        except:
            return []
        return []

    movies_filtrado['genero_lista'] = movies_filtrado['genres'].apply(extract_genres)

    #Expandir para multiplas linhas por genero
    movies_expandido = movies_filtrado.explode('genero_lista')
    movies_expandido = movies_expandido[movies_expandido['genero_lista'].isin(genero_escolhido)]

    movies_expandido = movies_expandido[
    (movies_expandido['profit'] >= profit_range[0]) & 
    (movies_expandido['profit'] <= profit_range[1])
]

    # Remover filmes com lucro ou valores inválidos
    movies_explodido = movies_expandido.dropna(subset=['profit', 'title', 'vote_average'])
    #grafico
    fig1 = px.scatter(
        movies_expandido,
        x="vote_average",
        y="profit",
        color="genero_lista",
        hover_data=["title", "profit", "vote_average"],
        title=f"Lucro dos Filmes por Gênero",
        labels={"vote_average": "Nota Média", "profit": "Lucro", "genero_lista": "Gênero"},
        height=600
    )

    st.plotly_chart(fig1)


#-------------------------------------------------------------------------------------------

# Segunda linha com duas colunas
col3, col4 = st.columns([1, 1])
with col3:
    st.subheader("Análise 3")
    st.write("""Conteúdo da Análise 3""")

with col4:
    st.subheader("Análise 4")
    st.write("Work in Progress")

st.markdown("---")
st.markdown("""
**Fonte dos dados:** https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset?select=movies_metadata.csv
**Aplicação desenvolvida com:** Streamlit e Plotly  
**Contexto:** Aula de Ciência de Dados - Visualização Interativa
""")