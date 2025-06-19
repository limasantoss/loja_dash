import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_js_eval import streamlit_js_eval

st.set_page_config(page_title="🤖 ZentsBot", layout="centered")
st.title("🤖 ZentsBot - Seu assistente de análise -  o perido nao ta funcionando corrigir dps")

# A detecção de tela e o carregamento dos dados continuam iguais.
screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key='SCR_WIDTH') or 769
is_mobile = screen_width < 768

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

# --- LÓGICA DO FILTRO DE DATA (REESCRITA PARA CORREÇÃO) ---

# 1. Define os limites máximos de data do dataset
data_min_geral = df_total["order_purchase_timestamp"].min().date()
data_max_geral = df_total["order_purchase_timestamp"].max().date()

# 2. Inicializa as datas do Bot apenas uma vez.
#    Se é a primeira vez, ele pega o valor da outra página ('date_range').
#    Se não houver, usa o período completo.
if 'bot_start_date' not in st.session_state:
    if 'date_range' in st.session_state:
        st.session_state.bot_start_date, st.session_state.bot_end_date = st.session_state.date_range
    else:
        st.session_state.bot_start_date = data_min_geral
        st.session_state.bot_end_date = data_max_geral

# 3. Cria o seletor de data, agora ligado diretamente ao estado da sessão do Bot.
with st.expander("Mudar período da análise do Bot"):
    col1, col2 = st.columns(2)
    col1.date_input("Início do período", key='bot_start_date')
    col2.date_input("Fim do período", key='bot_end_date')

# 4. Filtra o DataFrame usando as datas do estado de sessão do Bot, que agora são independentes.
df = df_total[
    (df_total["order_purchase_timestamp"].dt.date >= st.session_state.bot_start_date) &
    (df_total["order_purchase_timestamp"].dt.date <= st.session_state.bot_end_date)
]

st.info(f"Análise entre **{st.session_state.bot_start_date.strftime('%d/%m/%Y')}** e **{st.session_state.bot_end_date.strftime('%d/%m/%Y')}**", icon="📅")


# --- O RESTANTE DO CÓDIGO CONTINUA IGUAL ---

# Lógica dos botões de perguntas rápidas
PREGUNTAS_RAPIDAS = [
    "Qual o faturamento total?",
    "Quantos pedidos foram feitos?",
    "Qual o tempo médio de entrega?",
    "Qual a nota média dos pedidos?"
]

def set_pergunta(pergunta):
    st.session_state.pergunta_atual = pergunta

if 'pergunta_atual' not in st.session_state:
    st.session_state.pergunta_atual = ""

if is_mobile:
    st.subheader("Perguntas Rápidas")
    col_a, col_b = st.columns(2)
    with col_a:
        st.button(PREGUNTAS_RAPIDAS[0], on_click=set_pergunta, args=(PREGUNTAS_RAPIDAS[0],), use_container_width=True)
        st.button(PREGUNTAS_RAPIDAS[1], on_click=set_pergunta, args=(PREGUNTAS_RAPIDAS[1],), use_container_width=True)
    with col_b:
        st.button(PREGUNTAS_RAPIDAS[2], on_click=set_pergunta, args=(PREGUNTAS_RAPIDAS[2],), use_container_width=True)
        st.button(PREGUNTAS_RAPIDAS[3], on_click=set_pergunta, args=(PREGUNTAS_RAPIDAS[3],), use_container_width=True)

# Definição de regiões
REGIOES = {
    "norte": ["AM", "RR", "AP", "PA", "TO", "RO", "AC"],
    "nordeste": ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"],
    "sudeste": ["SP", "RJ", "MG", "ES"],
    "sul": ["PR", "SC", "RS"],
    "centro-oeste": ["MT", "MS", "GO", "DF"]
}

# Interface do bot
pergunta = st.text_input("Digite sua pergunta sobre os dados:", key="pergunta_atual")

if pergunta:
    pergunta_lower = pergunta.lower()
    resposta = "🤖 Ainda estou aprendendo como responder a isso."

    # Lógica de respostas... (sem alterações)
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
        if df.empty:
            resposta = "Não encontrei dados para o período selecionado."
        elif "faturamento" in pergunta_lower or ("vendas" in pergunta_lower and "total" in pergunta_lower):
            faturamento = df['payment_value'].sum()
            resposta = f"💰 O faturamento total no período foi de **R$ {faturamento:,.2f}**."
        elif "entrega" in pergunta_lower and "tempo" in pergunta_lower:
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