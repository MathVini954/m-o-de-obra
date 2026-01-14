import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Sistema de Mão de Obra", layout="wide")

PASTA_EFETIVO = "Efetivo"

MESES = {
    1: "Janeiro", 2: "Fevereiro", 3: "Março",
    4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",
    10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ------------------------------------------------
# LEITURA DOS ARQUIVOS
# ------------------------------------------------
@st.cache_data
def carregar_dados():
    dfs = []

    for arq in os.listdir(PASTA_EFETIVO):
        if arq.lower().endswith((".xls", ".xlsx")):
            mes_num = int(arq.split(".")[0])
            mes_nome = MESES.get(mes_num, "Desconhecido")

            df = pd.read_excel(os.path.join(PASTA_EFETIVO, arq))
            df["Mes_Num"] = mes_num
            df["Mes"] = mes_nome

            dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


df = carregar_dados()

# ------------------------------------------------
# BLINDAGEM
# ------------------------------------------------
COLUNAS_TEXTO = [
    "Nome da Empresa",
    "Sexo",
    "Nome do funcionário",
    "TIPO",
    "Mes"
]

COLUNAS_NUMERICAS = [
    "PRODUÇÃO",
    "REFLEXO S/ PRODUÇÃO",
    "Remuneração Líquida",
    "Adiantamento 2",
    "Hora Extra 70% - Sabado (Qtde)",
    "Hora Extra 70% - Semana (Qtde)",
    "Hora Extra 100% (Qtde)",
    "Repouso Remunerado",
    "Mes_Num"
]

for c in COLUNAS_TEXTO:
    if c not in df.columns:
        df[c] = "Não Informado"

for c in COLUNAS_NUMERICAS:
    if c not in df.columns:
        df[c] = 0
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# ------------------------------------------------
# FILTROS
# ------------------------------------------------
st.sidebar.title("Filtros")

obras = sorted(df["Nome da Empresa"].unique())
obra = st.sidebar.selectbox("Obra", ["Todas"] + obras)

meses_disponiveis = (
    df[["Mes_Num", "Mes"]]
    .drop_duplicates()
    .sort_values("Mes_Num")
)

meses_sel = st.sidebar.multiselect(
    "Mês",
    meses_disponiveis["Mes"],
    default=list(meses_disponiveis["Mes"])
)

df_filtro = df.copy()

if obra != "Todas":
    df_filtro = df_filtro[df_filtro["Nome da Empresa"] == obra]

df_filtro = df_filtro[df_filtro["Mes"].isin(meses_sel)]

# ------------------------------------------------
# CÁLCULOS FINANCEIROS
# ------------------------------------------------
base_fin = df_filtro["Remuneração Líquida"] - df_filtro["Adiantamento 2"]
base_fin = base_fin.replace(0, pd.NA)

df_filtro["Peso Produção"] = (
    df_filtro["PRODUÇÃO"] + df_filtro["REFLEXO S/ PRODUÇÃO"]
) / base_fin

df_filtro["Peso Hora Extra"] = (
    df_filtro["Hora Extra 70% - Sabado (Qtde)"]
    + df_filtro["Hora Extra 70% - Semana (Qtde)"]
    + df_filtro["Hora Extra 100% (Qtde)"]
    + df_filtro["Repouso Remunerado"]
) / base_fin

# ------------------------------------------------
# DASHBOARD
# ------------------------------------------------
st.title("Dashboard de Mão de Obra")

# 🔹 EFETIVO MENSAL (QUANTIDADE)
efetivo = (
    df.groupby(["Mes_Num", "Mes", "TIPO"])["Nome do funcionário"]
    .nunique()
    .reset_index(name="Efetivo")
    .sort_values("Mes_Num")
)

fig_efetivo = px.bar(
    efetivo,
    x="Mes",
    y="Efetivo",
    color="TIPO",
    barmode="group",
    title="Efetivo Mensal – Diretos x Indiretos"
)

st.plotly_chart(fig_efetivo, use_container_width=True)

# 🔹 PRODUÇÃO TOTAL (VALOR)
prod = (
    df_filtro.groupby("Mes")["PRODUÇÃO"]
    .sum()
    .reset_index()
)

fig_prod = px.bar(prod, x="Mes", y="PRODUÇÃO", title="Produção Total")
st.plotly_chart(fig_prod, use_container_width=True)

# 🔹 HORA EXTRA TOTAL (VALOR)
he = (
    df_filtro.groupby("Mes")[
        [
            "Hora Extra 70% - Sabado (Qtde)",
            "Hora Extra 70% - Semana (Qtde)",
            "Hora Extra 100% (Qtde)",
            "Repouso Remunerado"
        ]
    ].sum()
    .sum(axis=1)
    .reset_index(name="Total HE")
)

fig_he = px.bar(he, x="Mes", y="Total HE", title="Total de Horas Extras")
st.plotly_chart(fig_he, use_container_width=True)

# 🔹 PESOS
peso = (
    df_filtro.groupby("Mes")[["Peso Produção", "Peso Hora Extra"]]
    .mean()
    .reset_index()
)

fig_peso = px.line(
    peso,
    x="Mes",
    y=["Peso Produção", "Peso Hora Extra"],
    markers=True,
    title="Peso Produção x Hora Extra"
)

st.plotly_chart(fig_peso, use_container_width=True)
