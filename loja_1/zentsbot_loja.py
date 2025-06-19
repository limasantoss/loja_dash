import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="🤖 ZentsBot", layout="centered")
st.title("🤖 ZentsBot - Seu assistente de análise")

@st.cache_data
def carregar_dados():
    df = pd.read_csv("dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"])
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    return df

try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

data_min = df_total["order_purchase_timestamp"].min().date()
data_max = df_total["order_purchase_timestamp"].max().date()
if 'date_range' in st.session_state:
    start_date, end_date = st.session_state.date_range
else:
    start_date, end_date = data_min, data_max

df = df_total[
    (df_total["order_purchase_timestamp"].dt.date >= start_date) &
    (df_total["order_purchase_timestamp"].dt.date <= end_date)
]

st.info(f"Análise entre **{start_date.strftime('%d/%m/%Y')}** e **{end_date.strftime('%d/%m/%Y')}**", icon="📅")

REGIOES = {
    "norte": ["AM", "RR", "AP", "PA", "TO", "RO", "AC"],
    "nordeste": ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"],
    "sudeste": ["SP", "RJ", "MG", "ES"],
    "sul": ["PR", "SC", "RS"],
    "centro-oeste": ["MT", "MS", "GO", "DF"]
}

pergunta = st.text_input("Digite sua pergunta sobre os dados:")

if pergunta:
    pergunta_lower = pergunta.lower()
    resposta = "🤖 Ainda estou aprendendo como responder a isso."

    for regiao, estados in REGIOES.items():
        if regiao in pergunta_lower:
            df_reg = df[df["customer_state"].isin(estados)]
            if "entrega" in pergunta_lower and "tempo" in pergunta_lower:
                resposta = f"📦 Tempo médio de entrega na região {regiao.capitalize()}: **{df_reg['tempo_entrega'].mean():.1f} dias**"
            elif "frete" in pergunta_lower:
                resposta = f"🚚 Frete médio na região {regiao.capitalize()}: **R$ {df_reg['freight_value'].mean():.2f}**"
            elif "pedidos" in pergunta_lower or "vendas" in pergunta_lower:
                resposta = f"🛒 Total de pedidos na região {regiao.capitalize()}: **{len(df_reg):,}**"
            elif "atraso" in pergunta_lower:
                atrasos = df_reg["order_delivered_customer_date"] > df_reg["order_estimated_delivery_date"]
                pct = atrasos.mean() * 100
                resposta = f"⏰ Percentual de pedidos com atraso na região {regiao.capitalize()}: **{pct:.1f}%**"
            break

    if resposta.startswith("🤖"):
        if "entrega" in pergunta_lower and "tempo" in pergunta_lower:
            resposta = f"📦 Tempo médio de entrega: **{df['tempo_entrega'].mean():.1f} dias**"
        elif "frete" in pergunta_lower:
            resposta = f"🚚 Frete médio: **R$ {df['freight_value'].mean():.2f}**"
        elif "pedido" in pergunta_lower or "vendas" in pergunta_lower:
            resposta = f"🛒 Total de pedidos: **{len(df):,}**"
        elif "nota média" in pergunta_lower or "review" in pergunta_lower:
            resposta = f"⭐ Nota média dos pedidos: **{df['review_score'].mean():.2f}**"
        elif "cliente" in pergunta_lower and "único" in pergunta_lower:
            resposta = f"👤 Clientes únicos: **{df['customer_id'].nunique():,}**"

    st.success(resposta)
