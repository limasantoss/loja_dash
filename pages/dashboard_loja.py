import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

st.set_page_config(layout="wide", page_title="Portal do Vendedor", page_icon="🏪")

st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .stApp {
            background-color: #0E1117;
            color: #FAFAFA;
            font-family: 'Segoe UI', sans-serif;
        }
    </style>
""", unsafe_allow_html=True)

SELLER_ID_ESCOLHIDO = "4a3ca9315b744ce9f8e9374361493884"

@st.cache_data
def carregar_dados_vendedor(seller_id):
    df_total = pd.read_csv("dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date"])
    df_seller = df_total[df_total['seller_id'] == seller_id].copy()

    try:
        df_seller['order_purchase_timestamp'] = df_seller['order_purchase_timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        df_seller['order_delivered_customer_date'] = df_seller['order_delivered_customer_date'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    except TypeError:
        df_seller['order_purchase_timestamp'] = df_seller['order_purchase_timestamp'].dt.tz_convert('America/Sao_Paulo')
        df_seller['order_delivered_customer_date'] = df_seller['order_delivered_customer_date'].dt.tz_convert('America/Sao_Paulo')

    df_seller.dropna(subset=['order_delivered_customer_date', 'order_purchase_timestamp'], inplace=True)
    df_seller["tempo_entrega"] = (df_seller["order_delivered_customer_date"] - df_seller["order_purchase_timestamp"]).dt.days
    df_seller["ano_mes"] = df_seller["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df_seller["dia_da_semana"] = df_seller["order_purchase_timestamp"].dt.day_name()
    return df_seller

def get_periodo_anterior(data_inicio_atual, data_fim_atual):
    duracao = (data_fim_atual - data_inicio_atual) + timedelta(days=1)
    fim_anterior = data_inicio_atual - timedelta(days=1)
    inicio_anterior = fim_anterior - duracao + timedelta(days=1)
    return inicio_anterior, fim_anterior

# Load data
try:
    df_loja = carregar_dados_vendedor(SELLER_ID_ESCOLHIDO)
    if df_loja.empty:
        st.error(f"Nenhum dado encontrado para o vendedor com ID: {SELLER_ID_ESCOLHIDO}.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo de dados: {e}")
    st.stop()

st.sidebar.title("Portal do Vendedor")
st.sidebar.markdown("**Loja em análise:**")
st.sidebar.code(SELLER_ID_ESCOLHIDO)
st.sidebar.markdown("---")
data_min_loja = df_loja["order_purchase_timestamp"].min().date()
data_max_loja = df_loja["order_purchase_timestamp"].max().date()
date_range = st.sidebar.slider("Selecione o período:", min_value=data_min_loja, max_value=data_max_loja, value=(data_min_loja, data_max_loja))
st.sidebar.markdown("---")
selecao = st.sidebar.radio("Navegue pelas seções:", ["Visão Geral", "Meus Produtos", "Análise de Logística"])

start_date, end_date = date_range
df_filtrado = df_loja[(df_loja["order_purchase_timestamp"].dt.date >= start_date) & (df_loja["order_purchase_timestamp"].dt.date <= end_date)]

# Visão Geral
if selecao == "Visão Geral":
    st.title("📈 Visão Geral da Loja")
    st.markdown(f"Analisando de **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**.")
    st.markdown("---")

    if not df_filtrado.empty:
        faturamento_total = df_filtrado['payment_value'].sum()
        pedidos_totais = df_filtrado['order_id'].nunique()
        ticket_medio = faturamento_total / pedidos_totais if pedidos_totais > 0 else 0
        nota_media = df_filtrado['review_score'].mean()

        col1, col2, col3 = st.columns(3)
        col1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
        col2.metric("Total de Pedidos", f"{pedidos_totais}")
        col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        st.markdown("---")

        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Faturamento Mensal")
            faturamento_mes = df_filtrado.groupby("ano_mes")['payment_value'].sum().reset_index()
            fig = px.bar(faturamento_mes, x="ano_mes", y="payment_value", text='payment_value')
            st.plotly_chart(fig, use_container_width=True)

        with col_graf2:
            st.subheader("Faturamento por Dia da Semana")
            dias_ordem = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dias_map = {"Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta", "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo"}
            faturamento_dia = df_filtrado.groupby("dia_da_semana")['payment_value'].sum().reindex(dias_ordem).reset_index()
            faturamento_dia['dia_da_semana'] = faturamento_dia['dia_da_semana'].map(dias_map)
            fig2 = px.bar(faturamento_dia, x="dia_da_semana", y="payment_value")
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("Não há dados para o período selecionado.")
