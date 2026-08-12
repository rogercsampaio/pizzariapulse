# 🍕 PizzaPulse — Sistema Inteligente para Pizzarias com Assistente Autônomo de IA

> **PizzaPulse** é uma plataforma completa de gestão e atendimento inteligente para pizzarias, impulsionada por um **Assistente Autônomo de IA**. O sistema automatiza o fluxo de atendimento ao cliente via Chatbot e centraliza a operação do estabelecimento em um painel administrativo moderno e analítico.

---

## 📌 Sobre o Projeto

O **PizzaPulse** foi desenvolvido para resolver gargalos operacionais no atendimento de delivery e salão, eliminando filas de espera e otimizando a captação de pedidos. Através de um agente de Inteligência Artificial autônomo, o cliente realiza todo o seu atendimento de forma fluida e natural, enquanto o gestor acompanha métricas estratégicas em tempo real.

---

## 🚀 Funcionalidades Principais

### 🤖 1. Assistente Autônomo de IA (Chatbot Inteligente)
O coração da aplicação. Diferente de chatbots tradicionais baseados em árvores engessadas de decisão, a IA autônoma do **PizzaPulse** é capaz de:
* **Cadastrar Clientes:** Identifica e registra novos clientes de forma conversacional durante a interação.
* **Exibir Cardápio Interativo:** Apresenta produtos, sabores, tamanhos e adicionais dinamicamente.
* **Realizar Pedidos Fim a Fim:** Processa as escolhas do cliente, calcula o valor total, valida a forma de pagamento e insere o pedido diretamente no banco de dados.

### 📊 2. Painel de Analytics & Vendas
Painel executivo construído com **Streamlit, Pandas e Plotly** para tomada de decisão baseada em dados:
* **Métricas em Tempo Real:** Faturamento Total, Total de Produtos Vendidos e Ticket Médio por Cliente.
* **Gráfico de Evolução:** Histórico temporal do faturamento com gráfico de área preenchida.
* **Meios de Pagamento:** Distribuição percentual do faturamento por forma de pagamento (Pix, Cartão, Dinheiro).
* **Rankings e Desempenho:** Produtos mais vendidos (Valor vs. Quantidade) e Top 10 Clientes que mais consumiram.
* **Tabela Geral de Vendas:** Consulta detalhada de histórico de pedidos.

### 👥 3. Gestão e Listagem de Clientes
* Visualização da base de clientes cadastrados pelo sistema/chatbot.
* Histórico de consumo individual e dados de contato.

### 🍕 4. Gestão do Cardápio
* Módulo para listagem e consulta dos produtos, preços e categorias disponíveis na pizzaria.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python
* **Interface Administrativa:** Streamlit
* **Análise e Visualização de Dados:** Pandas, Plotly Express & Graph Objects
* **Banco de Dados:** SQLite
* **Inteligência Artificial:** Agente/Assistente Autônomo de IA integrado via API (LangChain / OpenAI / LLM)

---

## 📂 Estrutura do Projeto

```text
pizzaria/
├── abas/
│   ├── analytics.py        # Módulo de dashboards e métricas de vendas
│   ├── chatbot.py          # Interface do assistente autônomo de IA
│   ├── clientes.py         # Módulo de listagem e gestão de clientes
│   └── cardapio.py         # Módulo de visualização do cardápio
├── code/
│   └── funcoes_bd.py       # Consultas, agregadores e conexões SQLite
├── app.py                  # Aplicação principal (Streamlit Multipage)
├── pizzaria.db             # Banco de dados SQLite
└── README.md               # Documentação do projeto