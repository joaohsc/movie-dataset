import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import altair as alt

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


st.sidebar.subheader("Figura 1:")

min_year = int(movies['year'].min())
max_year = int(movies['year'].max())

min_profit = int(movies['profit'].min())
max_profit = int(movies['profit'].max())

year_range = st.sidebar.slider(
    "Selecione o intervalo de anos",
    min_value=min_year,
    max_value=max_year,
    value=(1900, 2014),
    step=1
)

st.sidebar.subheader("Figura 2:")
ano_padrao = 2014
# Garante que ele está na lista e pega o índice
anos = sorted(movies['year'].unique())
index_padrao = anos.index(ano_padrao) if ano_padrao in anos else 0
ano_escolhido = st.sidebar.selectbox("Selecione o ano:", anos,index=index_padrao)
#genero_escolhido = st.sidebar.multiselect("Seleciona os gêneros:", genres['name'].unique())

top_ranking = st.sidebar.slider(
    "Selecione o Top N gêneros",
    min_value=1,
    max_value=20,
    value=(5),
    step=1
)

st.sidebar.subheader("Figura 3:")

choices = ['Orçamento', 'Receita']
Coluna = st.sidebar.selectbox("Selecione a coluna:", choices)

companhias_disponiveis = production_companies['name'].dropna().unique()
companhias_escolhidas = st.sidebar.multiselect(
    "Selecione as companhias disponiveis",
    options = companhias_disponiveis,
    default = ["Universal Pictures"],
)

# Primeira linha com duas colunas
col1, col2 = st.columns([1, 1])
with col1:
    st.subheader("1) Qtd Filmes por Ano")
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
    st.subheader("2) Análise de lucro a partir de gênero e ano")
    st.write("""Gráfico para visualizar quais gêneros apresentaram
             maior lucro naquele ano
              """)
    
    #filtrar por ano
    with_revenue_df = with_revenue_df.rename(columns={"id": "movie_id"})

    with_revenue_df["release_date"] = pd.to_datetime(with_revenue_df["release_date"], errors="coerce")

    # 2. Extrai o ano
    with_revenue_df["year"] = with_revenue_df["release_date"].dt.year

    filmes_ano = with_revenue_df[(with_revenue_df["year"] == ano_escolhido)]

    df_tmp = pd.merge(genres_movies, filmes_ano, on="movie_id")
    # Conta quantos gêneros cada filme tem
    df_tmp["num_generos"] = df_tmp.groupby("movie_id")["name_name"].transform("count")
    # Receita proporcional por gênero
    df_tmp["revenue_per_genre"] = df_tmp["revenue"] / df_tmp["num_generos"]
    # Agrupa por gênero
    genero_lucro = df_tmp.groupby("name_name")["revenue_per_genre"].sum().reset_index()
    genero_lucro = genero_lucro.sort_values("revenue_per_genre", ascending=False).head(top_ranking)

    chart = alt.Chart(genero_lucro).mark_bar().encode(
        x=alt.X("revenue_per_genre:Q", title="Receita Total (US$)", axis=alt.Axis(format="$,.0f")),
        y=alt.Y("name_name:N", title="Gênero", sort="-x"),
        tooltip=["name_name", "revenue_per_genre"]
    ).properties(
        title=f"Gêneros mais lucrativos em {ano_escolhido}",
        height=400
    )

    st.altair_chart(chart, use_container_width=True)

#-------------------------------------------------------------------------------------------

# Segunda linha com duas colunas
col3, col4 = st.columns([1, 1])
with col3:
    st.subheader(f"3) Comparação de {Coluna} com Avaliações")
    st.write(f"""Este gráfico relaciona {Coluna} dos filmes com suas avaliações""")
    #st.write(production_companies_movies.columns.tolist())


    # Filtrar companhias escolhidas direto no production_companies_movies, coluna 'name_name'
    if companhias_escolhidas:
        filmes_filtrados = production_companies_movies[
            production_companies_movies['name_name'].isin(companhias_escolhidas)
        ]
    else:
        filmes_filtrados = production_companies_movies.copy()

    # Juntar com filmes para ter receita e avaliação
    filmes_filtrados = filmes_filtrados.merge(movies, left_on='movie_id', right_on='id', how='left')

    col = "budget"
    if Coluna == 'Receita':
        col = 'revenue'
    filmes_filtrados = filmes_filtrados.dropna(subset=[col, 'vote_average', 'title'])
    filmes_filtrados = filmes_filtrados[filmes_filtrados[col] > 0]


    fig3 = px.scatter(
        filmes_filtrados,
        x="vote_average",
        y=col,
        color="name_name",
        hover_data=["title", col, "vote_average"],
        title="Receita vs Avaliação por Companhia",
        labels={"vote_average": "Nota Média", col: f"{Coluna}", "name": "Companhia"},
        height=600
    )

    st.plotly_chart(fig3)
with col4:
    st.subheader("Análise 4")
    st.write("Work in Progress")

st.markdown("---")
st.markdown("""
**Fonte dos dados:** https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset?select=movies_metadata.csv
**Aplicação desenvolvida com:** Streamlit e Plotly  
**Contexto:** Aula de Ciência de Dados - Visualização Interativa
""")