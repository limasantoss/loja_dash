import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📦 Logística por Região", layout="wide")
st.title("📦 Logística por Região - Norte e Nordeste")

@st.cache_data
def carregar_dados():
    # CORREÇÃO FINAL: O caminho foi ajustado para a raiz do projeto.
    df = pd.read_csv(
        "dataset_olist_final_limpo.csv",
        parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    )
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["ano_mes"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    return df

try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

# Lógica para ler o filtro de data compartilhado (esta parte já estava correta)
data_min_geral = df_total["order_purchase_timestamp"].min().date()
data_max_geral = df_total["order_purchase_timestamp"].max().date()

if 'date_range' in st.session_state:
    start_date, end_date = st.session_state.date_range
else:
    # Define um valor padrão caso o usuário acesse esta página diretamente
    start_date, end_date = data_min_geral, data_max_geral

# Filtrar o DataFrame pelas datas selecionadas na sessão
df_filtrado = df_total[
    (df_total["order_purchase_timestamp"].dt.date >= start_date) &
    (df_total["order_purchase_timestamp"].dt.date <= end_date)
]

# Mostrar o período selecionado
st.info(f"Análise entre **{start_date.strftime('%d/%m/%Y')}** e **{end_date.strftime('%d/%m/%Y')}**", icon="📅")

# Filtro por regiões
norte = ["AM", "RR", "AP", "PA", "TO", "RO", "AC"]
nordeste = ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"]
df_log = df_filtrado[df_filtrado["customer_state"].isin(norte + nordeste)].copy()

if df_log.empty:
    st.warning("Não há dados para as regiões Norte e Nordeste no período selecionado.")
    st.stop()

# Gráficos
st.markdown("### Entregas por Estado")
entregas_estado = df_log["customer_state"].value_counts().reset_index()
entregas_estado.columns = ["Estado", "Pedidos"]
fig1 = px.bar(entregas_estado, x="Pedidos", y="Estado", orientation='h')
fig1.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### Tempo Médio de Entrega por Estado")
tempo_estado = df_log.groupby("customer_state")["tempo_entrega"].mean().sort_values().reset_index()
fig2 = px.bar(tempo_estado, x="tempo_entrega", y="customer_state", orientation='h', title="Tempo Médio de Entrega")
fig2.update_layout(xaxis_title="Dias", yaxis_title="Estado", yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig2, use_container_width=True)

st.markdown("### Frete Médio por Estado")
frete_estado = df_log.groupby("customer_state")["freight_value"].mean().sort_values().reset_index()
fig3 = px.bar(frete_estado, x="freight_value", y="customer_state", orientation='h', title="Frete Médio por Estado")
fig3.update_layout(xaxis_title="Valor (R$)", yaxis_title="Estado", yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig3, use_container_width=True)