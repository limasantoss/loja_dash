import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    layout="wide",
    page_title="Portal do Vendedor",
    page_icon="🏪"
)

# --- ESTILOS CSS (MODO ESCURO) ---
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


# --- ID DO VENDEDOR SELECIONADO ---
SELLER_ID_ESCOLHIDO = "4a3ca9315b744ce9f8e9374361493884"


# --- FUNÇÕES ---
@st.cache_data
def carregar_dados_vendedor(seller_id):
    df_total = pd.read_csv("dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date"])
    df_seller = df_total[df_total['seller_id'] == seller_id].copy()
    
    try:
        df_seller.loc[:, 'order_purchase_timestamp'] = df_seller['order_purchase_timestamp'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
        df_seller.loc[:, 'order_delivered_customer_date'] = df_seller['order_delivered_customer_date'].dt.tz_localize('UTC').dt.tz_convert('America/Sao_Paulo')
    except TypeError:
        df_seller.loc[:, 'order_purchase_timestamp'] = df_seller['order_purchase_timestamp'].dt.tz_convert('America/Sao_Paulo')
        df_seller.loc[:, 'order_delivered_customer_date'] = df_seller['order_delivered_customer_date'].dt.tz_convert('America/Sao_Paulo')
    
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

# A função agora recebe as datas do slider para ser mais precisa
def gerar_resposta_vendedor(pergunta, df_filtrado, df_loja_completa, start_date_selecionada, end_date_selecionada):
    pergunta = pergunta.lower()
    if df_filtrado.empty:
        return "Não encontrei dados para o período selecionado."

    if "faturamento" in pergunta or ("vendas" in pergunta and "dia" not in pergunta):
        faturamento_atual = df_filtrado['payment_value'].sum()
        
        # Usa as datas exatas do slider para calcular o período anterior
        inicio_anterior, fim_anterior = get_periodo_anterior(start_date_selecionada, end_date_selecionada)
        
        df_anterior = df_loja_completa[(df_loja_completa['order_purchase_timestamp'].dt.date >= inicio_anterior) & (df_loja_completa['order_purchase_timestamp'].dt.date <= fim_anterior)]
        faturamento_anterior = df_anterior['payment_value'].sum()
        
        resposta = f"Seu faturamento no período foi de **R$ {faturamento_atual:,.2f}**."
        if faturamento_anterior > 0:
            variacao = ((faturamento_atual - faturamento_anterior) / faturamento_anterior) * 100
            if variacao > 0.1: resposta += f" Isso representa uma **alta de {variacao:.1f}%** em relação ao período anterior."
            elif variacao < -0.1: resposta += f" Isso representa uma **queda de {abs(variacao):.1f}%** em relação ao período anterior."
            else: resposta += " O valor se manteve estável em relação ao período anterior."
        return resposta
    elif "pedidos" in pergunta:
        pedidos_atuais = df_filtrado['order_id'].nunique()
        
        # Usa as datas exatas do slider
        inicio_anterior, fim_anterior = get_periodo_anterior(start_date_selecionada, end_date_selecionada)

        df_anterior = df_loja_completa[(df_loja_completa['order_purchase_timestamp'].dt.date >= inicio_anterior) & (df_loja_completa['order_purchase_timestamp'].dt.date <= fim_anterior)]
        pedidos_anteriores = df_anterior['order_id'].nunique()
        resposta = f"Você teve **{pedidos_atuais}** pedidos no período."
        if pedidos_anteriores > 0:
            variacao = ((pedidos_atuais - pedidos_anteriores) / pedidos_anteriores) * 100
            if variacao > 0.1: resposta += f" **Alta de {variacao:.1f}%** em relação ao período anterior."
            elif variacao < -0.1: resposta += f" **Queda de {abs(variacao):.1f}%** em relação ao período anterior."
        return resposta
    elif "produto mais vendido" in pergunta:
        if not df_filtrado.empty and not df_filtrado['product_category_name_english'].isnull().all():
            top_produto = df_filtrado['product_category_name_english'].value_counts().idxmax()
            return f"🏆 Seu produto mais vendido no período foi **{top_produto}**."
        else: return "Não há vendas de produtos no período para analisar."
    elif "tempo de entrega" in pergunta:
        tempo_medio = df_filtrado['tempo_entrega'].mean()
        return f"🚚 Seu tempo médio de entrega para os pedidos do período é de **{tempo_medio:.1f} dias**."
    else:
        return "❓ Desculpe, não entendi. Tente perguntar sobre `faturamento`, `pedidos`, `produto mais vendido` ou `tempo de entrega`."

# --- CARREGAMENTO E VALIDAÇÃO DOS DADOS ---
try:
    df_loja = carregar_dados_vendedor(SELLER_ID_ESCOLHIDO)
    if df_loja.empty:
        st.error(f"Nenhum dado encontrado para o vendedor com ID: {SELLER_ID_ESCOLHIDO}.")
        st.stop()
except Exception as e:
    st.error(f"Erro ao carregar o arquivo de dados: {e}")
    st.stop()

# --- SIDEBAR COM FILTROS E NAVEGAÇÃO ---
st.sidebar.title("Portal do Vendedor")
st.sidebar.markdown(f"**Loja em análise:**")
st.sidebar.code(f"{SELLER_ID_ESCOLHIDO}")
st.sidebar.markdown("---")
data_min_loja = df_loja["order_purchase_timestamp"].min().date()
data_max_loja = df_loja["order_purchase_timestamp"].max().date()

st.sidebar.slider(
    "Selecione o período:", 
    min_value=data_min_loja, 
    max_value=data_max_loja, 
    value=(data_min_loja, data_max_loja),
    key="date_range"
)

st.sidebar.markdown("---") 

# Adicionando um chatbot na sidebar
st.sidebar.subheader("Converse com seus dados")
pergunta_sidebar = st.sidebar.text_input("Faça uma pergunta sobre o período selecionado:")

# Filtra o dataframe para o chatbot da sidebar com base no slider
start_date_slider, end_date_slider = st.session_state.date_range
df_filtrado_sidebar = df_loja[(df_loja["order_purchase_timestamp"].dt.date >= start_date_slider) & (df_loja["order_purchase_timestamp"].dt.date <= end_date_slider)]

if pergunta_sidebar:
    # Passa as datas do slider ao chamar a função
    resposta_sidebar = gerar_resposta_vendedor(pergunta_sidebar, df_filtrado_sidebar, df_loja, start_date_slider, end_date_slider)
    st.sidebar.success(resposta_sidebar)


# --- NAVEGAÇÃO PRINCIPAL ---
selecao = st.radio("Navegue pelas seções:", ["Visão Geral", "Meus Produtos", "Análise de Logística"], horizontal=True)

# Filtra o dataframe para os gráficos da página principal
start_date, end_date = st.session_state.date_range 
df_filtrado_pagina = df_loja[(df_loja["order_purchase_timestamp"].dt.date >= start_date) & (df_loja["order_purchase_timestamp"].dt.date <= end_date)]

# --- LÓGICA DE EXIBIÇÃO DAS PÁGINAS ---

if selecao == "Visão Geral":
    st.title("📈 Visão Geral da Loja")
    st.markdown(f"Analisando de **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**.")
    st.markdown("---")
    if not df_filtrado_pagina.empty:
        faturamento_total = df_filtrado_pagina['payment_value'].sum()
        pedidos_totais = df_filtrado_pagina['order_id'].nunique()
        ticket_medio = faturamento_total / pedidos_totais if pedidos_totais > 0 else 0
        nota_media = df_filtrado_pagina['review_score'].mean()
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
        col2.metric("Total de Pedidos", f"{pedidos_totais}")
        col3.metric("Ticket Médio", f"R$ {ticket_medio:,.2f}")
        col4.metric("Nota Média", f"{nota_media:.2f} ⭐")
        st.markdown("---")
        
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            st.subheader("Faturamento Mensal")
            faturamento_mes = df_filtrado_pagina.groupby("ano_mes")['payment_value'].sum().reset_index()
            fig = px.bar(faturamento_mes, x="ano_mes", y="payment_value", labels={'payment_value': 'Faturamento (R$)', 'ano_mes': 'Mês'}, text='payment_value')
            fig.update_traces(texttemplate='R$ %{text:,.2s}')
            st.plotly_chart(fig, use_container_width=True)
        with col_graf2:
            st.subheader("Faturamento por Dia da Semana")
            dias_ordem = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            dias_map = {"Monday": "Segunda", "Tuesday": "Terça", "Wednesday": "Quarta", "Thursday": "Quinta", "Friday": "Sexta", "Saturday": "Sábado", "Sunday": "Domingo"}
            faturamento_dia = df_filtrado_pagina.groupby("dia_da_semana")['payment_value'].sum().reindex(dias_ordem).reset_index()
            faturamento_dia['dia_da_semana'] = faturamento_dia['dia_da_semana'].map(dias_map)
            fig2 = px.bar(faturamento_dia, x="dia_da_semana", y="payment_value", labels={'payment_value': 'Faturamento (R$)', 'dia_da_semana': 'Dia da Semana'})
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("---")
        st.subheader("Distribuição Geográfica e de Pagamentos")
        col_mapa, col_pizza = st.columns(2)
        with col_mapa:
            vendas_estado = df_filtrado_pagina['customer_state'].value_counts().reset_index()
            vendas_estado.columns = ['state_code', 'orders']
            fig_mapa = px.choropleth(vendas_estado, geojson="https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson", locations='state_code', featureidkey="properties.sigla", color='orders', color_continuous_scale="Blues", scope="south america", title="Mapa de Pedidos por Estado")
            fig_mapa.update_geos(fitbounds="locations", visible=False)
            st.plotly_chart(fig_mapa, use_container_width=True)
        with col_pizza:
            pagamentos = df_filtrado_pagina['payment_type'].value_counts().reset_index()
            fig_pizza = px.pie(pagamentos, names='payment_type', values='count', title="Distribuição por Tipo de Pagamento", hole=0.4)
            st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.warning("Não há dados para o período selecionado.")

elif selecao == "Meus Produtos":
    st.title("📦 Análise de Produtos")
    st.markdown(f"Analisando de **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**.")
    st.markdown("---")
    df_produtos = df_filtrado_pagina.dropna(subset=['product_category_name_english'])
    if not df_produtos.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Top 5 Produtos por Faturamento")
            top_faturamento = df_produtos.groupby('product_category_name_english')['payment_value'].sum().nlargest(5).sort_values(ascending=True).reset_index()
            fig = px.bar(top_faturamento, x='payment_value', y='product_category_name_english', orientation='h', text='payment_value', labels={'product_category_name_english': 'Categoria'})
            fig.update_traces(texttemplate='R$ %{text:,.2f}')
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.subheader("Top 5 Produtos por Unidades Vendidas")
            top_unidades = df_produtos['product_category_name_english'].value_counts().nlargest(5).sort_values(ascending=True).reset_index()
            fig2 = px.bar(top_unidades, x='count', y='product_category_name_english', orientation='h', text='count', labels={'product_category_name_english': 'Categoria'})
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown("---")
        st.subheader("Análise de Portfólio (Preço vs. Vendas)")
        df_portfolio = df_produtos.groupby('product_category_name_english').agg(preco_medio=('price', 'mean'), unidades_vendidas=('order_id', 'count'), faturamento_total=('payment_value', 'sum')).reset_index()
        fig_portfolio = px.scatter(df_portfolio, x="unidades_vendidas", y="preco_medio", size="faturamento_total", color="product_category_name_english", hover_name="product_category_name_english", labels={'unidades_vendidas': 'Unidades Vendidas', 'preco_medio': 'Preço Médio (R$)'}, title="Portfólio: Preço x Volume x Faturamento")
        st.plotly_chart(fig_portfolio, use_container_width=True)
    else:
        st.warning("Não há dados de produtos no período selecionado.")

elif selecao == "Análise de Logística":
    st.title("🚚 Análise de Logística")
    st.markdown(f"Analisando entregas de **{start_date.strftime('%d/%m/%Y')}** a **{end_date.strftime('%d/%m/%Y')}**.")
    st.markdown("---")
    if not df_filtrado_pagina.empty:
        col1, col2 = st.columns(2)
        col1.metric("Tempo Médio de Entrega", f"{df_filtrado_pagina['tempo_entrega'].mean():.1f} dias")
        col2.metric("Frete Médio", f"R$ {df_filtrado_pagina['freight_value'].mean():,.2f}")
        st.markdown("---")
        st.subheader("Performance Logística por Estado")
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            tempo_estado = df_filtrado_pagina.groupby('customer_state')['tempo_entrega'].mean().sort_values(ascending=False).reset_index()
            fig = px.bar(tempo_estado.head(10), x='tempo_entrega', y='customer_state', orientation='h', title="Top 10 Piores Tempos de Entrega", labels={'customer_state': 'Estado', 'tempo_entrega': 'Dias'})
            fig.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig, use_container_width=True)
        with col_graf2:
            frete_estado = df_filtrado_pagina.groupby('customer_state')['freight_value'].mean().sort_values(ascending=False).reset_index()
            fig2 = px.bar(frete_estado.head(10), x='freight_value', y='customer_state', orientation='h', title="Top 10 Maiores Custos de Frete", labels={'customer_state': 'Estado', 'freight_value': 'Frete (R$)'})
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
        st.markdown("---")
        st.subheader("Consistência e Custo-Benefício")
        col_hist, col_scatter = st.columns(2)
        with col_hist:
            fig_hist = px.histogram(df_filtrado_pagina, x='tempo_entrega', nbins=30, title="Distribuição do Tempo de Entrega")
            st.plotly_chart(fig_hist, use_container_width=True)
        with col_scatter:
            df_scatter = df_filtrado_pagina.groupby('customer_state').agg(tempo_medio=('tempo_entrega', 'mean'), frete_medio=('freight_value', 'mean'), pedidos=('order_id', 'count')).reset_index()
            fig_scatter = px.scatter(df_scatter, x='tempo_medio', y='frete_medio', size='pedidos', color='pedidos', hover_name='customer_state', title="Custo x Tempo por Estado")
            st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Não há dados de logística no período selecionado.")