import streamlit as st
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from streamlit_js_eval import streamlit_js_eval
import re

st.set_page_config(
    page_title="", 
    page_icon="", #removi os icone da empresa 
    layout="centered"
)

#obs : ja coloquei para o streamlit força as cores dele msmo -> arquivo:streamlit ->config.toml
st.markdown("""
    <style>
        
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: #FF6F17;'>🤖 Botdash  :)</h1>", unsafe_allow_html=True)

screen_width = streamlit_js_eval(js_expressions='window.innerWidth', key='SCR_WIDTH') or 769
is_mobile = screen_width < 768

@st.cache_data
def carregar_dados():
    df = pd.read_csv("dataset_olist_final_limpo.csv", parse_dates=["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"])
    df["tempo_entrega"] = (df["order_delivered_customer_date"] - df["order_purchase_timestamp"]).dt.days
    df["dia_da_semana"] = df["order_purchase_timestamp"].dt.day_name()
    return df

# --- FUNÇÕES DE APOIO ---
def get_periodo_anterior(data_inicio_atual, data_fim_atual):
    duracao = (data_fim_atual - data_inicio_atual)
    fim_anterior = data_inicio_atual - timedelta(days=1)
    inicio_anterior = fim_anterior - duracao
    return inicio_anterior, fim_anterior

def calcular_metricas(df_periodo):
    if df_periodo.empty:
        return {'faturamento': 0, 'pedidos': 0}
    faturamento = df_periodo['payment_value'].sum()
    pedidos = df_periodo['order_id'].nunique()
    return {'faturamento': faturamento, 'pedidos': pedidos}

def extrair_periodo_da_pergunta(pergunta):
    meses_map = {'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4, 'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12}
    padrao = r'(' + '|'.join(meses_map.keys()) + r') de (\d{4})'
    match = re.search(padrao, pergunta.lower())
    if match:
        nome_mes, ano = match.groups()
        mes_num = meses_map[nome_mes]
        start_date = date(int(ano), mes_num, 1)
        end_date = start_date + relativedelta(months=1) - timedelta(days=1)
        return start_date, end_date
    return None, None

# --- LÓGICA PRINCIPAL ---
try:
    df_total = carregar_dados()
except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
    st.stop()

st.markdown("---")

st.markdown("<h3 style='color: #FF6F17;'>Selecione o Período para Análise</h3>", unsafe_allow_html=True)

anos_disponiveis = sorted(df_total['order_purchase_timestamp'].dt.year.unique(), reverse=True)
meses_map_selectbox = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}
opcoes_mes = ["Ano Inteiro"] + list(meses_map_selectbox.values())
col1, col2 = st.columns(2)
ano_selecionado = col1.selectbox("Ano:", options=anos_disponiveis)
mes_selecionado_nome = col2.selectbox("Mês:", options=opcoes_mes)

if mes_selecionado_nome == "Ano Inteiro":
    start_date_contexto, end_date_contexto = date(ano_selecionado, 1, 1), date(ano_selecionado, 12, 31)
else:
    mes_num = list(meses_map_selectbox.keys())[list(meses_map_selectbox.values()).index(mes_selecionado_nome)]
    start_date_contexto = date(ano_selecionado, mes_num, 1)
    end_date_contexto = start_date_contexto + relativedelta(months=1) - relativedelta(days=1)

df_contexto = df_total[(df_total["order_purchase_timestamp"].dt.date >= start_date_contexto) & (df_total["order_purchase_timestamp"].dt.date <= end_date_contexto)]
st.info(f"Contexto de análise: **{start_date_contexto.strftime('%d/%m/%Y')}** a **{end_date_contexto.strftime('%d/%m/%Y')}**", icon="📅")
st.markdown("---")

PREGUNTAS_RAPIDAS = ["Me dê um resumo do período", "Qual meu produto mais vendido?", "Meus clientes estão satisfeitos?", "Qual o ticket médio?", "Qual dia da semana vende mais?", "Qual estado tem a entrega mais demorada?"]
def set_pergunta(pergunta):
    st.session_state.pergunta_atual = pergunta
if 'pergunta_atual' not in st.session_state: st.session_state.pergunta_atual = ""

if is_mobile:

    st.markdown("<h3 style='color: #FF6F17;'>Perguntas Rápidas</h3>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, pergunta_rapida in enumerate(PREGUNTAS_RAPIDAS):
        col_atual = cols[i % 2]
        col_atual.button(pergunta_rapida, on_click=set_pergunta, args=(pergunta_rapida,), use_container_width=True)

REGIOES = {"norte": ["AM", "RR", "AP", "PA", "TO", "RO", "AC"], "nordeste": ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"], "sudeste": ["SP", "RJ", "MG", "ES"], "sul": ["PR", "SC", "RS"], "centro-oeste": ["MT", "MS", "GO", "DF"]}
pergunta = st.text_input("Digite sua pergunta sobre os dados ou peça um 'resumo':", key="pergunta_atual")

if pergunta:
    pergunta_lower = pergunta.lower()
    
    texto_ajuda = """
    **Tente perguntar sobre:**
    * `Resumo` do período
    * `Faturamento`, `Pedidos` ou `Ticket Médio`
    * `Produto mais vendido`
    * `Dia da semana` com mais vendas
    * `Satisfação dos clientes` (nota média)
    * `Entregas` (tempo médio ou estado com maior demora)

    *Você também pode especificar um **mês e ano** na pergunta (ex: faturamento em maio de 2018).*
    """
    resposta = f"🤖 Desculpe, não entendi.\n\n{texto_ajuda}"
    
    start_date_pergunta, end_date_pergunta = extrair_periodo_da_pergunta(pergunta_lower)
    
    df_pergunta = df_contexto
    start_date_analise = start_date_contexto
    end_date_analise = end_date_contexto
    
    if start_date_pergunta:
        df_pergunta = df_total[(df_total["order_purchase_timestamp"].dt.date >= start_date_pergunta) & (df_total["order_purchase_timestamp"].dt.date <= end_date_pergunta)]
        start_date_analise, end_date_analise = start_date_pergunta, end_date_pergunta
        st.info(f"Análise específica para **{start_date_pergunta.strftime('%B de %Y')}**", icon="🔎")

    if "resumo" in pergunta_lower:
        if df_pergunta.empty:
            resposta = "Não há dados no período para gerar um resumo."
        else:
            metricas_atuais = calcular_metricas(df_pergunta)
            inicio_anterior, fim_anterior = get_periodo_anterior(start_date_analise, end_date_analise)
            df_anterior = df_total[(df_total["order_purchase_timestamp"].dt.date >= inicio_anterior) & (df_total["order_purchase_timestamp"].dt.date <= fim_anterior)]
            metricas_anteriores = calcular_metricas(df_anterior)

            variacao_fat = ((metricas_atuais['faturamento'] - metricas_anteriores['faturamento']) / metricas_anteriores['faturamento'] * 100) if metricas_anteriores['faturamento'] > 0 else 0
            variacao_ped = ((metricas_atuais['pedidos'] - metricas_anteriores['pedidos']) / metricas_anteriores['pedidos'] * 100) if metricas_anteriores['pedidos'] > 0 else 0
            
            produto_campeao = df_pergunta['product_category_name_english'].mode()[0] if not df_pergunta['product_category_name_english'].dropna().empty else "N/A"
            ponto_atencao = df_pergunta.groupby('customer_state')['tempo_entrega'].mean().nlargest(1)
            
            if not ponto_atencao.empty:
                estado_atencao, tempo_atencao = ponto_atencao.index[0], ponto_atencao.values[0]
                texto_atencao = f"* **Ponto de Atenção:** O maior tempo de entrega foi para o estado de **{estado_atencao}**, com média de **{tempo_atencao:.1f} dias**."
            else:
                texto_atencao = ""

            resposta = f"""
            **🤖 Resumo do Período ({start_date_analise.strftime('%d/%m/%y')} a {end_date_analise.strftime('%d/%m/%y')})**

            * **Faturamento:** R$ {metricas_atuais['faturamento']:,.2f} ({variacao_fat:+.1f}% vs. período anterior)
            * **Pedidos:** {metricas_atuais['pedidos']} ({variacao_ped:+.1f}% vs. período anterior)
            * **Produto Campeão:** Categoria "{produto_campeao.replace("_", " ").title()}"
            {texto_atencao}
            """
    elif df_pergunta.empty:
        resposta = "Não encontrei dados para o período selecionado."
    elif "produto mais vendido" in pergunta_lower:
        if not df_pergunta.empty and not df_pergunta['product_category_name_english'].isnull().all():
            top_produto = df_pergunta['product_category_name_english'].value_counts().idxmax()
            resposta = f"🏆 Seu produto mais vendido no período foi **{top_produto.replace('_', ' ').title()}**."
        else:
            resposta = "Não há vendas de produtos no período para analisar."
    elif "ticket médio" in pergunta_lower:
         faturamento = df_pergunta['payment_value'].sum()
         pedidos = df_pergunta['order_id'].nunique()
         ticket_medio = faturamento / pedidos if pedidos > 0 else 0
         resposta = f"O ticket médio por pedido no período foi de **R$ {ticket_medio:,.2f}**."
    elif "dia da semana" in pergunta_lower and "vende mais" in pergunta_lower:
         dias_map = {"Monday": "Segunda-feira", "Tuesday": "Terça-feira", "Wednesday": "Quarta-feira", "Thursday": "Quinta-feira", "Friday": "Sexta-feira", "Saturday": "Sábado", "Sunday": "Domingo"}
         faturamento_dia = df_pergunta.groupby('dia_da_semana')['payment_value'].sum()
         if not faturamento_dia.empty:
             dia_campeao = faturamento_dia.idxmax()
             resposta = f"O dia da semana com maior faturamento foi **{dias_map.get(dia_campeao, dia_campeao)}**."
         else:
             resposta = "Não há dados suficientes para determinar o melhor dia da semana."
    elif "entrega mais demorada" in pergunta_lower:
         ponto_atencao = df_pergunta.groupby('customer_state')['tempo_entrega'].mean().nlargest(1)
         if not ponto_atencao.empty:
             estado, tempo = ponto_atencao.index[0], ponto_atencao.values[0]
             resposta = f"O estado com a maior média de tempo de entrega é **{estado}**, com **{tempo:.1f} dias**."
         else:
             resposta = "Não há dados de entrega para analisar."
    elif "satisfeitos" in pergunta_lower or "nota média" in pergunta_lower:
        nota_media = df_pergunta['review_score'].mean()
        comentario = "É uma ótima nota!" if nota_media > 4 else "É uma boa nota, mas há espaço para melhorar." if nota_media > 3 else "Ponto de atenção! A satisfação pode ser melhorada."
        resposta = f"⭐ A nota média de satisfação dos seus clientes é **{nota_media:.2f} de 5**. {comentario}"
    elif "pedidos" in pergunta_lower:
         resposta = f"🛒 Foram feitos **{df_pergunta['order_id'].nunique():,}** pedidos no período."
    elif "faturamento" in pergunta_lower:
        faturamento = df_pergunta['payment_value'].sum()
        resposta = f"💰 O faturamento total no período foi de **R$ {faturamento:,.2f}**."

    st.success(resposta)