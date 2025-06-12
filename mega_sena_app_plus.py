
# mega_sena_app_plus.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests
import random

# --- Traduções ---
TRADUCOES = {
    "pt": {
        "title": "🔢 Mega Sena - Analisador & Gerador de Jogos",
        "freq_title": "📊 Frequência dos Números",
        "generate_title": "🎯 Gerar Jogo Personalizado",
        "required_numbers": "Números obrigatórios:",
        "excluded_numbers": "Números a excluir:",
        "sum_min": "Soma mínima dos números:",
        "sum_max": "Soma máxima dos números:",
        "even_count": "Quantidade de números pares:",
        "generate_button": "🔄 Gerar Jogo",
        "game_result": "🎉 Jogo sugerido: {}",
        "no_result": "⚠️ Não foi possível gerar um jogo com essas condições.",
        "upload_label": "📁 Envie um arquivo CSV com seus jogos",
        "frequent_game": "🔝 Gerar com os + frequentes"
    }
}

# --- Funções ---
def gerar_jogo(excluir, incluir, soma_min, soma_max, num_pares):
    max_tentativas = 1000
    numeros_possiveis = [n for n in range(1, 61) if n not in excluir]

    for _ in range(max_tentativas):
        jogo = incluir.copy()
        restantes = [n for n in numeros_possiveis if n not in jogo]
        random.shuffle(restantes)

        while len(jogo) < 6 and restantes:
            jogo.append(restantes.pop())

        if len(jogo) != 6:
            continue

        soma = sum(jogo)
        pares = len([n for n in jogo if n % 2 == 0])

        if soma_min <= soma <= soma_max and pares == num_pares:
            return sorted(jogo)

    return None

@st.cache_data
def importar_ultimos_sorteios(qtd=30):
    url_base = "https://loteriascaixa-api.herokuapp.com/api/mega-sena"
    sorteios = []
    try:
        response = requests.get(url_base)
        if response.status_code == 200:
            data = response.json()
            concursos = data[:qtd] if isinstance(data, list) else [data]
            for concurso in concursos:
                dezenas = concurso.get("dezenas")
                if dezenas:
                    numeros = sorted(map(int, dezenas))
                    sorteios.append(numeros)
    except Exception as e:
        st.error(f"Erro ao importar dados: {e}")
    return sorteios

def verificar_acertos(jogo, sorteios):
    acertos = {4: 0, 5: 0, 6: 0}
    for s in sorteios:
        intersecao = len(set(jogo) & set(s))
        if intersecao >= 4:
            acertos[intersecao] += 1
    return acertos

def gerar_com_mais_frequentes(freq_df, quantidade=6):
    return sorted(freq_df.sort_values("Frequência", ascending=False).head(quantidade)["Número"].tolist())

# --- Interface Streamlit ---
t = TRADUCOES["pt"]
st.set_page_config(layout="wide")
st.title(t["title"])

qtd_sorteios = st.sidebar.slider("🔢 Número de sorteios para análise", 10, 100, 30)
sorteios = importar_ultimos_sorteios(qtd_sorteios)

frequencia = {}
for jogo in sorteios:
    for numero in jogo:
        frequencia[numero] = frequencia.get(numero, 0) + 1
freq_df = pd.DataFrame(list(frequencia.items()), columns=["Número", "Frequência"]).sort_values("Número")

# Tabs
aba1, aba2, aba3 = st.tabs([t["freq_title"], t["generate_title"], "📁 Jogos do Usuário"])

with aba1:
    st.header(t["freq_title"])
    fig, ax = plt.subplots()
    ax.bar(freq_df["Número"], freq_df["Frequência"], color="green")
    ax.set_xlabel("Números")
    ax.set_ylabel("Frequência")
    st.pyplot(fig)

with aba2:
    st.header(t["generate_title"])
    incluir = st.multiselect(t["required_numbers"], list(range(1, 61)))
    excluir = st.multiselect(t["excluded_numbers"], list(range(1, 61)))
    soma_min = st.slider(t["sum_min"], 100, 250, 140)
    soma_max = st.slider(t["sum_max"], 100, 250, 210)
    num_pares = st.slider(t["even_count"], 0, 6, 3)

    col1, col2 = st.columns(2)
    with col1:
        if st.button(t["generate_button"]):
            jogo = gerar_jogo(excluir, incluir, soma_min, soma_max, num_pares)
            if jogo:
                st.success(t["game_result"].format(jogo))
                acertos = verificar_acertos(jogo, sorteios)
                st.info(f"Acertos anteriores: Quadras: {acertos[4]}, Quinas: {acertos[5]}, Senas: {acertos[6]}")
            else:
                st.error(t["no_result"])

    with col2:
        if st.button(t["frequent_game"]):
            jogo_freq = gerar_com_mais_frequentes(freq_df)
            st.success(f"Jogo com mais frequentes: {jogo_freq}")
            acertos = verificar_acertos(jogo_freq, sorteios)
            st.info(f"Acertos anteriores: Quadras: {acertos[4]}, Quinas: {acertos[5]}, Senas: {acertos[6]}")

with aba3:
    st.header("📥 Verificar Jogos do Usuário")
    uploaded_file = st.file_uploader(t["upload_label"], type=["csv"])
    if uploaded_file:
        user_jogos = pd.read_csv(uploaded_file)
        for idx, linha in user_jogos.iterrows():
            jogo = list(linha.dropna().astype(int))
            acertos = verificar_acertos(jogo, sorteios)
            st.write(f"Jogo {idx+1}: {jogo} — Quadras: {acertos[4]}, Quinas: {acertos[5]}, Senas: {acertos[6]}")
