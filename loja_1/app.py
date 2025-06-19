import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="📊 Loja Dashboard", layout="wide")

# --- Dados e Setup ---
@st.cache_data
def carregar_dados():
    # CORREÇÃO APLICADA AQUI: Adicionado o caminho da subpasta 'loja_1/'
    df = pd.read_csv("loja_1/dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"])
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["ano_mes"] = df["order_purchase_timestamp"].dt.to_period("M").astype(str)
    df["dia_da_semana"] = df["order_purchase_timestamp"].dt.day_name()
    return df

try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

data_min = df_total["order_purchase_timestamp"].min().date()
data_max = df_total["order_purchase_timestamp"].max().date()
start_date, end_date = st.sidebar.slider("Selecione o período:", min_value=data_min, max_value=data_max, value=(data_min, data_max))
df = df_total[
    (df_total["order_purchase_timestamp"].dt.date >= start_date) &
    (df_total["order_purchase_timestamp"].dt.date <= end_date)
]

# --- Sidebar Navegação ---
pagina = st.sidebar.radio("Navegue pelas seções:", [
    "Visão Geral", 
    "Meus Produtos", 
    "Análise de Logística", 
    "Região Norte/Nordeste", 
    "ZentsBot 🤖"
])

# --- Visão Geral ---
if pagina == "Visão Geral":
    st.title("📈 Visão Geral da Loja")
    faturamento_total = df['payment_value'].sum()
    pedidos_totais = df['order_id'].nunique()
    ticket_medio = faturamento_total / pedidos_totais if pedidos_totais > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
    col2.metric("Total de Pedidos", f"{pedidos_totais}")
    col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Faturamento Mensal")
        fig1 = px.bar(df.groupby("ano_mes")["payment_value"].sum().reset_index(), x="ano_mes", y="payment_value")
        st.plotly_chart(fig1, use_container_width=True)
    with col_b:
        st.subheader("Faturamento por Dia da Semana")
        ordem_dias = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        dias_map = {"Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta", "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo"}
        df_dia = df.groupby("dia_da_semana")["payment_value"].sum().reindex(ordem_dias).reset_index()
        df_dia["dia_da_semana"] = df_dia["dia_da_semana"].map(dias_map)
        fig2 = px.bar(df_dia, x="dia_da_semana", y="payment_value")
        st.plotly_chart(fig2, use_container_width=True)

# --- Meus Produtos ---
elif pagina == "Meus Produtos":
    st.title("📦 Análise de Produtos")
    df_prod = df.dropna(subset=['product_category_name_english'])
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top 5 Categorias (Faturamento)")
        top_faturamento = df_prod.groupby('product_category_name_english')['payment_value'].sum().nlargest(5).reset_index()
        fig = px.bar(top_faturamento, x='payment_value', y='product_category_name_english', orientation='h', text='payment_value')
        fig.update_traces(texttemplate='R$ %{text:,.2f}', textposition='outside')
        fig.update_layout(yaxis_title="Categoria", xaxis_title="Faturamento")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Top 5 Categorias (Unidades Vendidas)")
        top_unidades = df_prod['product_category_name_english'].value_counts().nlargest(5).reset_index()
        fig2 = px.bar(top_unidades, x='count', y='product_category_name_english', orientation='h', text='count')
        fig2.update_traces(textposition='outside')
        fig2.update_layout(yaxis_title="Categoria", xaxis_title="Unidades Vendidas")
        st.plotly_chart(fig2, use_container_width=True)

# --- Análise de Logística ---
elif pagina == "Análise de Logística":
    st.title("🚚 Análise de Logística")
    col1, col2 = st.columns(2)
    col1.metric("Tempo Médio de Entrega", f"{df['tempo_entrega'].mean():.1f} dias")
    col2.metric("Frete Médio", f"R$ {df['freight_value'].mean():,.2f}")

# --- Região Norte/Nordeste ---
elif pagina == "Região Norte/Nordeste":
    st.title("📦 Logística por Região - Norte e Nordeste")
    norte = ["AM", "RR", "AP", "PA", "TO", "RO", "AC"]
    nordeste = ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"]
    df_log = df[df["customer_state"].isin(norte + nordeste)]

    st.subheader("Entregas por Estado")
    fig1 = px.bar(df_log["customer_state"].value_counts().reset_index(), x="customer_state", y="count", orientation='v')
    st.plotly_chart(fig1, use_container_width=True)

    st.subheader("Tempo Médio de Entrega por Estado")
    fig2 = px.bar(df_log.groupby("customer_state")["tempo_entrega"].mean().reset_index(), x="tempo_entrega", y="customer_state", orientation='h')
    st.plotly_chart(fig2, use_container_width=True)

# --- ZentsBot ---
elif pagina == "ZentsBot 🤖":
    st.title("🤖 ZentsBot - Seu assistente de análise")

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
                if df_reg.empty:
                    resposta = f"Não encontrei dados para a região {regiao.capitalize()} no período selecionado."
                    break

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