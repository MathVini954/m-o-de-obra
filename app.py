import streamlit as st
import pandas as pd
import os
import plotly.express as px

st.set_page_config(page_title="Sistema de Mão de Obra", layout="wide")

PASTA_EFETIVO = "Efetivo"

COLUNAS_BASE = [
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
    1: "Janeiro", 2: "Fevereiro", 3: "Março",
    4: "Abril", 5: "Maio", 6: "Junho",
    7: "Julho", 8: "Agosto", 9: "Setembro",
    10: "Outubro", 11: "Novembro", 12: "Dezembro"
}

# ------------------------------------------------
# LEITURA ACUMULATIVA (XLS e XLSX)
# ------------------------------------------------
@st.cache_data
def carregar_dados():
    if not os.path.exists(PASTA_EFETIVO):
        st.error(f"Pasta '{PASTA_EFETIVO}' não encontrada.")
        return pd.DataFrame()

    arquivos = [
        f for f in os.listdir(PASTA_EFETIVO)
        if f.lower().endswith((".xls", ".xlsx"))
    ]

    if not arquivos:
        st.error("Nenhum arquivo .xls ou .xlsx encontrado na pasta Efetivo.")
        return pd.DataFrame()

    dfs = []

    for arq in arquivos:
        try:
            mes_num = int(arq.split(".")[0])
            mes_nome = MESES.get(mes_num, "Desconhecido")

            caminho = os.path.join(PASTA_EFETIVO, arq)
            df = pd.read_excel(caminho)

            # mantém apenas colunas conhecidas
            colunas_validas = [c for c in COLUNAS_BASE if c in df.columns]
            df = df[colunas_validas].copy()

            df["Mes_Num"] = mes_num
            df["Mes"] = mes_nome

            dfs.append(df)

        except Exception as e:
            st.warning(f"Erro ao processar {arq}: {e}")

    if not dfs:
        st.error("Arquivos encontrados, mas nenhum pôde ser carregado.")
        return pd.DataFrame()

    return pd.concat(dfs, ignore_index=True, sort=False)


df = carregar_dados()

# ------------------------------------------------
# BLINDAGEM DE COLUNAS (ANTES DE QUALQUER USO)
# ------------------------------------------------
COLUNAS_OBRIGATORIAS = [
    "Nome da Empresa",
    "Sexo",
    "Nome do funcionário",
    "TIPO",
    "Mes",
    "Mes_Num",
    "PRODUÇÃO",
    "REFLEXO S/ PRODUÇÃO",
    "Remuneração Líquida",
    "Adiantamento 2",
    "Hora Extra 70% - Sabado (Qtde)",
    "Hora Extra 70% - Semana (Qtde)",
    "Hora Extra 100% (Qtde)",
    "Repouso Remunerado"
]

for c in COLUNAS_OBRIGATORIAS:
    if c not in df.columns:
        if c in ["Mes", "TIPO", "Sexo", "Nome da Empresa", "Nome do funcionário"]:
            df[c] = "Não Informado"
        else:
            df[c] = 0

# ------------------------------------------------
# CONVERSÃO NUMÉRICA
# ------------------------------------------------
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

for c in COLUNAS_NUMERICAS:
    df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

# ------------------------------------------------
# FILTRO OBRA
# ------------------------------------------------
st.sidebar.title("Filtros")

obras = sorted(df["Nome da Empresa"].unique())
obra = st.sidebar.selectbox("Obra", ["Todas"] + obras)

if obra != "Todas":
    df_filtro = df[df["Nome da Empresa"] == obra].copy()
else:
    df_filtro = df.copy()

# ------------------------------------------------
# CÁLCULOS
# ------------------------------------------------
denominador = df_filtro["Remuneração Líquida"] - df_filtro["Adiantamento 2"]
denominador = denominador.replace(0, pd.NA)

df_filtro["Peso Produção"] = (
    (df_filtro["PRODUÇÃO"] + df_filtro["REFLEXO S/ PRODUÇÃO"]) / denominador
)

df_filtro["Peso Hora Extra"] = (
    (
        df_filtro["Hora Extra 70% - Sabado (Qtde)"]
        + df_filtro["Hora Extra 70% - Semana (Qtde)"]
        + df_filtro["Hora Extra 100% (Qtde)"]
        + df_filtro["Repouso Remunerado"]
    ) / denominador
)

# ------------------------------------------------
# DASHBOARD
# ------------------------------------------------
st.title("Dashboard de Mão de Obra")

# 1️⃣ EFETIVO MENSAL ACUMULATIVO (NÃO FILTRA MÊS)
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

# 2️⃣ PIZZA SEXO
sexo = (
    df_filtro.groupby("Sexo")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_sexo = px.pie(sexo, names="Sexo", values="Quantidade", title="Distribuição por Sexo")
st.plotly_chart(fig_sexo, use_container_width=True)

# 3️⃣ PIZZA DIRETO x INDIRETO
tipo = (
    df_filtro.groupby("TIPO")["Nome do funcionário"]
    .nunique()
    .reset_index(name="Quantidade")
)

fig_tipo = px.pie(tipo, names="TIPO", values="Quantidade", title="Diretos x Indiretos")
st.plotly_chart(fig_tipo, use_container_width=True)

# 4️⃣ PESO PRODUÇÃO POR OBRA
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

# 5️⃣ PESO HORA EXTRA POR OBRA
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
