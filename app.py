import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Sistema de Mão de Obra", layout="wide")

PASTA_EFETIVO = "Efetivo"

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

MESES = {
    "01": "Janeiro", "02": "Fevereiro", "03": "Março",
    "04": "Abril", "05": "Maio", "06": "Junho",
    "07": "Julho", "08": "Agosto", "09": "Setembro",
    "10": "Outubro", "11": "Novembro", "12": "Dezembro"
}

# -----------------------------
# LEITURA ACUMULATIVA
# -----------------------------
@st.cache_data
@st.cache_data
def carregar_dados():
    if not os.path.exists(PASTA_EFETIVO):
        st.error(f"Pasta '{PASTA_EFETIVO}' não encontrada.")
        return pd.DataFrame()

    arquivos = [
        f for f in os.listdir(PASTA_EFETIVO)
        if f.lower().endswith((".xlsx", ".xls"))
    ]

    if not arquivos:
        st.error("Nenhum arquivo .xls ou .xlsx encontrado na pasta Efetivo.")
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        try:
            # extrai número do mês (ex: 12.Dezembro - Folha.xls)
            mes_num = arq.split(".")[0]

            caminho = os.path.join(PASTA_EFETIVO, arq)
            df = pd.read_excel(caminho)

            colunas_validas = [c for c in COLUNAS if c in df.columns]
            df = df[colunas_validas].copy()

            df["Mes_Num"] = int(mes_num)
            df["Mes"] = arq.split(".")[1].split(" ")[0]

            dfs.append(df)

        except Exception as e:
            st.warning(f"Erro ao processar {arq}: {e}")

    if not dfs:
        st.error("Arquivos encontrados, mas nenhum pôde ser carregado.")
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True, sort=False)


df = carregar_dados()

# -----------------------------
# FILTRO OBRA
# -----------------------------
st.sidebar.title("Filtros")

obras = sorted(df["Nome da Empresa"].dropna().unique())
obra = st.sidebar.selectbox("Obra", ["Todas"] + obras)

if obra != "Todas":
    df_filtro = df[df["Nome da Empresa"] == obra]
else:
    df_filtro = df.copy()

# -----------------------------
# CONVERSÃO NUMÉRICA
# -----------------------------
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
    else:
        df_filtro[c] = 0

# -----------------------------
# CÁLCULOS
# -----------------------------

COLUNAS_CALCULO = [
    "PRODUÇÃO",
    "REFLEXO S/ PRODUÇÃO",
    "Remuneração Líquida",
    "Adiantamento 2",
    "Hora Extra 70% - Sabado (Qtde)",
    "Hora Extra 70% - Semana (Qtde)",
    "Hora Extra 100% (Qtde)",
    "Repouso Remunerado"
]

for c in COLUNAS_CALCULO:
    if c not in df_filtro.columns:
        df_filtro[c] = 0

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

# -----------------------------
# DASHBOARD
# -----------------------------
st.title("Dashboard de Mão de Obra")

# EFETIVO MENSAL ACUMULATIVO (NÃO FILTRA MÊS)
efetivo_mensal = (
    df.groupby(["Mes_Num", "Mes", "TIPO"])["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
    .sort_values("Mes_Num")
)

fig_efetivo = px.bar(
    efetivo_mensal,
    x="Mes",
    y="Quantidade",
    color="TIPO",
    barmode="group",
    title="Efetivo Mensal Acumulativo - Diretos x Indiretos"
)

st.plotly_chart(fig_efetivo, use_container_width=True)

# PIZZA SEXO
sexo = (
    df_filtro.groupby("Sexo")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_sexo = px.pie(sexo, names="Sexo", values="Quantidade", title="Distribuição por Sexo")
st.plotly_chart(fig_sexo, use_container_width=True)

# PIZZA TIPO
tipo = (
    df_filtro.groupby("TIPO")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_tipo = px.pie(tipo, names="TIPO", values="Quantidade", title="Diretos x Indiretos")
st.plotly_chart(fig_tipo, use_container_width=True)

# PESO PRODUÇÃO
peso_prod = (
    df_filtro.groupby("Nome da Empresa")["Peso Produção"]
    .mean()
    .reset_index()
)

fig_prod = px.line(
    peso_prod,
    x="Nome da Empresa",
    y="Peso Produção",
    markers=True,
    title="Peso Produção por Obra"
)

st.plotly_chart(fig_prod, use_container_width=True)

# PESO HORA EXTRA
peso_he = (
    df_filtro.groupby("Nome da Empresa")["Peso Hora Extra"]
    .mean()
    .reset_index()
)

fig_he = px.line(
    peso_he,
    x="Nome da Empresa",
    y="Peso Hora Extra",
    markers=True,
    title="Peso Hora Extra por Obra"
)

st.plotly_chart(fig_he, use_container_width=True)
