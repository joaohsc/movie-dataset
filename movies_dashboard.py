import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import altair as alt
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split, KFold, cross_val_score
from sklearn.metrics import mean_squared_error, r2_score

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
    with_profit_df = movies[movies['profit'] > 0]
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
    step=1,
    key="key_1"
)

genre_select = ['all'] + list(genres['name'].unique())

genero_escolhido = st.sidebar.selectbox("Seleciona os gêneros:", genre_select)

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

choices_f = ['Filmes','Gênero']
genre_or_movie = st.sidebar.selectbox("Selecione visualização por Gênero ou Filme:", choices_f)

st.sidebar.subheader("Figura 3:")

choices = ['Orçamento', 'Receita']
Coluna = st.sidebar.selectbox("Selecione a coluna:", choices)

companhias_disponiveis = production_companies['name'].dropna().unique()
companhias_escolhidas = st.sidebar.multiselect(
    "Selecione as companhias disponiveis",
    options = companhias_disponiveis,
    default = ["Universal Pictures"],
)

st.sidebar.subheader("Figura 4:")
genero_escolhidoReg = st.sidebar.selectbox(
    "Seleciona os gêneros:",
    genres['name'].unique(),
    key="year_slider_6"  # <-- chave diferente
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
    if genero_escolhido != 'all':
        # Filtra apenas os filmes do gênero selecionado
        filmes_genero = genres_movies[genres_movies["name_name"] == genero_escolhido]
        df_filter = movies[movies["id"].isin(filmes_genero["movie_id"])]
    movie_counts = df_filter.groupby('year').size().reset_index(name='qtd')

    movie_counts['year'] = pd.to_datetime(movie_counts['year'].astype(str), format='%Y')

    fig = px.line(
        movie_counts, 
        x='year', 
        y=['qtd'],
        title=f'Qtd filme X Ano ({genero_escolhido})',
    )
    st.plotly_chart(fig)


with col2:
    st.subheader(f"2) Análise de Receita a partir de {genre_or_movie} e ano")
    st.write(f"""Gráfico para visualizar quais {genre_or_movie} apresentaram
             maiores receitas em um ano específico. Obs.: o filtro permite ver por filmes ou gêneros.
              """)
    
    #filtrar por ano
    with_revenue_df = with_revenue_df.rename(columns={"id": "movie_id"})

    with_revenue_df["release_date"] = pd.to_datetime(with_revenue_df["release_date"], errors="coerce")

    # 2. Extrai o ano
    with_revenue_df["year"] = with_revenue_df["release_date"].dt.year

    filmes_ano = with_revenue_df[(with_revenue_df["year"] == ano_escolhido)]

    filmes_lucro = filmes_ano.sort_values("revenue", ascending=False).head(top_ranking)

    filmes_long = filmes_lucro.melt(
        id_vars="title",
        value_vars=["revenue", "budget"],
        var_name="Tipo",
        value_name="Valor"
    )

    chart = alt.Chart(filmes_long).mark_bar().encode(
        x=alt.X("Valor:Q", title="Valor (US$)", axis=alt.Axis(format="$,.0f")),
        y=alt.Y("title:N", title="Título", sort="-x"),
        color=alt.Color("Tipo:N", title="Tipo"),
        tooltip=["title", "Tipo", "Valor"]
    ).properties(
        title=f"Receita x Orçamento dos Filmes mais lucrativos em {ano_escolhido}",
        height=400
    )

    if genre_or_movie == 'Gênero':
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
    st.write(f"""Este gráfico relaciona {Coluna} dos filmes com suas avaliações. Obs.: 
             o filtro permite ver por orçamento ou receita.""")
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
    st.subheader("Análise 4) Previsão de Receita por gênero")
    st.write("Esse gráfico utiliza Random Forest Regressor para prever futuras receitas a partir do gênero")
    
    # Validação: é necessário escolher apenas 1 gênero
    
    GEN = genero_escolhidoReg

    # Ajuste do nome da coluna de gênero
    genres_movies = genres_movies.rename(columns={'name_name': 'genre_name'})

    # Merge usando id (with_revenue_df) e movie_id (genres_movies)
    df_merged = pd.merge(with_revenue_df, genres_movies, left_on='movie_id', right_on='movie_id')

    # Filtra pelo gênero selecionado
    df_genero = df_merged[df_merged['genre_name'] == GEN].copy()

    df_genero['release_date'] = pd.to_datetime(df_genero['release_date'], errors='coerce')
    df_genero = df_genero.dropna(subset=['release_date'])

    for col in ['budget', 'popularity', 'revenue']:
        df_genero[col] = pd.to_numeric(df_genero[col], errors='coerce')

    df_genero['year'] = df_genero['release_date'].dt.year

    df_receita_por_ano = df_genero.groupby('year').agg({
        'revenue': 'sum',
        'budget': 'mean',
        'movie_id': 'count',  # usaremos 'id' no lugar de movie_id
        'popularity': 'mean'
    }).reset_index()

    df_receita_por_ano.rename(columns={
        'movie_id': 'num_filmes',
        'budget': 'orcamento_medio',
        'popularity': 'popularidade_media'
    }, inplace=True)

    df_receita_por_ano = df_receita_por_ano[
        (df_receita_por_ano['year'] >= 1970) & (df_receita_por_ano['year'] < 2017)
    ]

    # Features e target
    features = ['year', 'orcamento_medio', 'num_filmes', 'popularidade_media']
    target = 'revenue'

    X = df_receita_por_ano[features]
    y = np.log1p(df_receita_por_ano[target])

    # Split e modelo
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    modelo = RandomForestRegressor(n_estimators=200, random_state=42)

    # Validação cruzada
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(modelo, X_train, y_train, scoring='neg_root_mean_squared_error', cv=cv)

    modelo.fit(X_train, y_train)
    y_pred = modelo.predict(X_test)
    y_pred_real = np.expm1(y_pred)
    y_test_real = np.expm1(y_test)

    rmse = np.sqrt(mean_squared_error(y_test_real, y_pred_real))
    r2 = r2_score(y_test_real, y_pred_real)

    st.markdown(f"""
    *Validação Cruzada (RMSE médio):* {(-scores.mean()):.2f}  
    *RMSE no teste:* {rmse:.2f}  
    *R² no teste:* {r2:.2f}
    """)

    # Previsão para anos
    anos_futuros = pd.DataFrame({'year': list(range(1970, 2026))})

    # Função para estimar tendência linear
    def prever_tendencia(col):
        modelo_lin = LinearRegression()
        X_ano = df_receita_por_ano[['year']]
        y_col = df_receita_por_ano[col]
        modelo_lin.fit(X_ano, y_col)
        return modelo_lin.predict(anos_futuros[['year']])

    # Aplica projeções lineares
    anos_futuros['orcamento_medio'] = prever_tendencia('orcamento_medio')
    anos_futuros['num_filmes'] = prever_tendencia('num_filmes')
    anos_futuros['popularidade_media'] = prever_tendencia('popularidade_media')

    #Previsão
    X_futuro = anos_futuros[features]
    anos_futuros['receita_prevista'] = np.expm1(modelo.predict(X_futuro))

    # Gráfico
    # Usando Plotly Express
    
fig4 = px.line(
    anos_futuros,
    x='year',
    y='receita_prevista',
    title=f'Previsão de Receita para Filmes do Gênero \"{GEN}\" (1970–2025)',
    labels={'year': 'Ano', 'receita_prevista': 'Receita Total (USD)'},
    markers=True,
    height=500
)

fig4.add_scatter(
    x=df_receita_por_ano['year'],
    y=df_receita_por_ano['revenue'],
    mode='markers',
    marker=dict(color='orange', size=8),
    name='Receita Real'
)

fig4.update_layout(
    xaxis_title='Ano',
    yaxis_title='Receita Total (USD)',
    legend=dict(font=dict(size=12)),
    xaxis=dict(tickangle=45),
    #plot_bgcolor='white',
    hovermode='x unified',
    margin=dict(l=40, r=40, t=60, b=40)
)

fig4.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')
fig4.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray')

st.plotly_chart(fig4, use_container_width=True)

st.markdown("---")
st.markdown("""
**Fonte dos dados:** https://www.kaggle.com/datasets/rounakbanik/the-movies-dataset?select=movies_metadata.csv
**Aplicação desenvolvida com:** Streamlit e Plotly  
**Contexto:** Aula de Ciência de Dados - Visualização Interativa
""")


