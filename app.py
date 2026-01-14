import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Sistema de Mão de Obra", layout="wide")

PASTA_EFETIVOS = "data/efetivos"

COLUNAS = [
    "Nome da Empresa",
    "Sexo",
    "Nome do funcionário",
    "Função",
    "TIPO",
    "Hora Extra 70% - Sabado (Qtde)",
    "Hora Extra 70% - Semana (Qtde)",
    "Hora Extra 100% (Qtde)",
    "Repouso Remunerado",
    "PRODUÇÃO",
    "REFLEXO S/ PRODUÇÃO",
    "Remuneração Líquida",
    "Adiantamento 2"
]

# ------------------------------
# LEITURA ACUMULATIVA
# ------------------------------
@st.cache_data
def carregar_dados():
    dfs = []

    for arq in os.listdir(PASTA_EFETIVOS):
        if arq.endswith(".xlsx"):
            caminho = os.path.join(PASTA_EFETIVOS, arq)
            df = pd.read_excel(caminho)

            colunas_validas = [c for c in COLUNAS if c in df.columns]
            df = df[colunas_validas].copy()

            # tenta extrair mês do nome do arquivo (opcional)
            df["Arquivo"] = arq

            dfs.append(df)

    if not dfs:
        return pd.DataFrame(columns=COLUNAS)

    return pd.concat(dfs, ignore_index=True, sort=False)


df = carregar_dados()

# ------------------------------
# FILTRO OBRA
# ------------------------------
st.sidebar.title("Filtros")

obras = sorted(df["Nome da Empresa"].dropna().unique())
obra_selecionada = st.sidebar.selectbox(
    "Obra",
    ["Todas"] + obras
)

if obra_selecionada != "Todas":
    df_filtro = df[df["Nome da Empresa"] == obra_selecionada]
else:
    df_filtro = df.copy()

# ------------------------------
# TRATAMENTO NUMÉRICO
# ------------------------------
num_cols = [
    "Hora Extra 70% - Sabado (Qtde)",
    "Hora Extra 70% - Semana (Qtde)",
    "Hora Extra 100% (Qtde)",
    "Repouso Remunerado",
    "PRODUÇÃO",
    "REFLEXO S/ PRODUÇÃO",
    "Remuneração Líquida",
    "Adiantamento 2"
]

for c in num_cols:
    if c in df_filtro.columns:
        df_filtro[c] = pd.to_numeric(df_filtro[c], errors="coerce").fillna(0)

# ------------------------------
# MÉTRICAS
# ------------------------------
df_filtro["Peso Produção"] = (
    (df_filtro["PRODUÇÃO"] + df_filtro["REFLEXO S/ PRODUÇÃO"]) /
    (df_filtro["Remuneração Líquida"] - df_filtro["Adiantamento 2"])
)

df_filtro["Peso Hora Extra"] = (
    (
        df_filtro["Hora Extra 70% - Sabado (Qtde)"] +
        df_filtro["Hora Extra 70% - Semana (Qtde)"] +
        df_filtro["Hora Extra 100% (Qtde)"] +
        df_filtro["Repouso Remunerado"]
    ) /
    (df_filtro["Remuneração Líquida"] - df_filtro["Adiantamento 2"])
)

# ------------------------------
# LAYOUT
# ------------------------------
st.title("Dashboard de Mão de Obra")

col1, col2 = st.columns(2)

# ------------------------------
# GRÁFICO COLUNA - EFETIVO (ACUMULATIVO)
# ------------------------------
efetivo_tipo = (
    df.groupby("TIPO")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_efetivo = px.bar(
    efetivo_tipo,
    x="TIPO",
    y="Quantidade",
    color="TIPO",
    title="Efetivo Acumulado - Diretos x Indiretos"
)

col1.plotly_chart(fig_efetivo, use_container_width=True)

# ------------------------------
# PIZZA SEXO
# ------------------------------
sexo = (
    df_filtro.groupby("Sexo")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_sexo = px.pie(
    sexo,
    names="Sexo",
    values="Quantidade",
    title="Distribuição por Sexo"
)

col2.plotly_chart(fig_sexo, use_container_width=True)

# ------------------------------
# PIZZA TIPO
# ------------------------------
tipo = (
    df_filtro.groupby("TIPO")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_tipo = px.pie(
    tipo,
    names="TIPO",
    values="Quantidade",
    title="Diretos x Indiretos"
)

st.plotly_chart(fig_tipo, use_container_width=True)

# ------------------------------
# LINHA - PESO PRODUÇÃO
# ------------------------------
peso_prod = (
    df_filtro.groupby("Nome da Empresa")["Peso Produção"]
    .mean()
    .reset_index()
)

fig_peso_prod = px.line(
    peso_prod,
    x="Nome da Empresa",
    y="Peso Produção",
    markers=True,
    title="Peso Produção por Obra"
)

st.plotly_chart(fig_peso_prod, use_container_width=True)

# ------------------------------
# LINHA - PESO HORA EXTRA
# ------------------------------
peso_he = (
    df_filtro.groupby("Nome da Empresa")["Peso Hora Extra"]
    .mean()
    .reset_index()
)

fig_peso_he = px.line(
    peso_he,
    x="Nome da Empresa",
    y="Peso Hora Extra",
    markers=True,
    title="Peso Hora Extra por Obra"
)

st.plotly_chart(fig_peso_he, use_container_width=True)
