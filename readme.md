#  Dashboard de Análise da Loja

Dashboard interativo para análise de vendas, clientes e logística de uma loja virtual, desenvolvido em Python com **Streamlit** e **Plotly**.  
Inclui painéis dinâmicos, filtros por período, análises detalhadas e chatbot para respostas rápidas sobre o desempenho da loja.

## Funcionalidades

- **Painel Interativo:** KPIs de vendas, ticket médio, satisfação dos clientes e entregas.
- **Filtros de Período:** Selecione ano, mês ou períodos personalizados.
- **Perguntas Rápidas e Chatbot:** Faça perguntas em linguagem natural para obter insights sobre produtos, faturamento, entregas, etc.
- **Gráficos Dinâmicos:** Barras, linhas e mapas de vendas por estado.
- **Análise de Logística:** Tempos de entrega, estados com maior demora, frete médio e atrasos.
- **Layout Responsivo:** Compatível com desktop e mobile.

## Como rodar o projeto

1. **Clone este repositório:**
    ```bash
    git clone https://github.com/seu-usuario/seu-repo.git
    cd seu-repo
    ```
2. **Instale as dependências:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Adicione o dataset na pasta do projeto:**
    - Nome esperado: `dataset_olist_final_limpo.csv`

4. **Execute o dashboard principal:**
    ```bash
    streamlit run dashboard_loja.py
    ```
    - Para abrir o bot:
      ```bash
      streamlit run loja_bot.py
      ```

5. **Acesse no navegador: * *  
    - [http://localhost:8501](http://localhost:8501)

---


