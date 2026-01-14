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

# ======================================================
# LEITURA DOS ARQUIVOS
# ======================================================
@st.cache_data
def carregar_dados():
    dfs = []

    for arq in os.listdir(PASTA_EFETIVO):
        if arq.lower().endswith((".xls", ".xlsx")):
            try:
                mes_num = int(arq.split(".")[0])
            except:
                continue

            mes_nome = MESES.get(mes_num, "Desconhecido")

            df = pd.read_excel(os.path.join(PASTA_EFETIVO, arq))
            df["Mes_Num"] = mes_num
            df["Mes"] = mes_nome

            dfs.append(df)

    if not dfs:
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True, sort=False)


df = carregar_dados()

if df.empty:
    st.error("Nenhum arquivo válido encontrado na pasta Efetivo.")
    st.stop()

# ======================================================
# BLINDAGEM DE COLUNAS
# ======================================================
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
    df[c] = df[c].fillna("Não Informado").astype(str)

for c in COLUNAS_NUMERICAS:
    if c not in df.columns:
        df[c] = 0
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# ======================================================
# FILTROS
# ======================================================
st.sidebar.title("Filtros")

obras = sorted(df["Nome da Empresa"].dropna().astype(str).unique())
obra_sel = st.sidebar.selectbox("Obra", ["Todas"] + obras)

meses_df = (
    df[["Mes_Num", "Mes"]]
    .drop_duplicates()
    .sort_values("Mes_Num")
)

meses_sel = st.sidebar.multiselect(
    "Mês",
    meses_df["Mes"].tolist(),
    default=meses_df["Mes"].tolist()
)

df_filtro = df.copy()

if obra_sel != "Todas":
    df_filtro = df_filtro[df_filtro["Nome da Empresa"] == obra_sel]

df_filtro = df_filtro[df_filtro["Mes"].isin(meses_sel)]

# ======================================================
# CÁLCULOS FINANCEIROS
# ======================================================
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

# ======================================================
# DASHBOARD
# ======================================================
st.title("Dashboard de Mão de Obra")

# ------------------------------------------------------
# EFETIVO MENSAL (ACUMULATIVO – SEM FILTRO DE MÊS)
# ------------------------------------------------------
efetivo_mensal = (
    df.groupby(["Mes_Num", "Mes", "TIPO"])["Nome do funcionário"]
    .nunique()
    .reset_index(name="Efetivo")
    .sort_values("Mes_Num")
)

fig_efetivo = px.bar(
    efetivo_mensal,
    x="Mes",
    y="Efetivo",
    color="TIPO",
    barmode="group",
    title="Efetivo Mensal – Diretos x Indiretos"
)

st.plotly_chart(fig_efetivo, use_container_width=True)

# ------------------------------------------------------
# SEXO
# ------------------------------------------------------
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

st.plotly_chart(fig_sexo, use_container_width=True)

# ------------------------------------------------------
# DIRETO x INDIRETO
# ------------------------------------------------------
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

# ------------------------------------------------------
# PESO POR OBRA
# ------------------------------------------------------
peso_obra = (
    df_filtro.groupby("Nome da Empresa")[["Peso Produção", "Peso Hora Extra"]]
    .mean()
    .reset_index()
)

fig_peso = px.line(
    peso_obra,
    x="Nome da Empresa",
    y=["Peso Produção", "Peso Hora Extra"],
    markers=True,
    title="Peso de Produção e Hora Extra por Obra"
)

st.plotly_chart(fig_peso, use_container_width=True)
