import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="App Simples de Teste", page_icon="✨")

st.title("✨ Meu Primeiro App Streamlit Simples!")

st.write("Olá! Este é um aplicativo Streamlit básico para testar o deploy.")
st.write("Você pode interagir com os elementos abaixo:")

# Slider simples
valor = st.slider("Selecione um número:", 0, 100, 50)
st.write(f"O número selecionado é: {valor}")

# Gráfico de dados aleatórios
st.header("Dados Aleatórios")
chart_data = pd.DataFrame(
    np.random.randn(20, 3),
    columns=['a', 'b', 'c']
)
st.line_chart(chart_data)

st.success("Seu app está funcionando!")