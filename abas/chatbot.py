# abas/chatbot.py

import os
import streamlit as st
from loguru import logger
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool

# ANTES (causando erro):
# from langchain.agents import AgentExecutor, create_tool_calling_agent
# ou
# from langchain.agents.agent import AgentExecutor

# DEPOIS (Correto com langchain-classic):
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
# ----------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------
# 1. Busca a API Key priorizando o st.secrets do Streamlit
API_KEY = (
    st.secrets.get("GEMINI_API_KEY") 
    or os.environ.get("GEMINI_API_KEY")
)

if not API_KEY:
    st.error("⚠️ A chave GEMINI_API_KEY não foi encontrada nos segredos nem nas variáveis de ambiente.")
    st.stop()
MODEL_NAME = "gemini-3.1-flash-lite"


# ----------------------------------------------------------------------
# TOOLS (FUNÇÕES DO BANCO DE DADOS)
# ----------------------------------------------------------------------
from code.funcoes_bd import (
    listar_produtos as listar_produtos_bd,
    cadastrar_pedido_completo,
    listar_pedidos as listar_pedidos_bd,
    cadastrar_cliente_completo
)

@tool
def listar_produtos() -> str:
    """Lista os produtos disponíveis no cardápio."""
    return str(listar_produtos_bd())

@tool
def cadastrar_pedido(id_cliente: int, valor_total: float, tipo_pagamento: str, itens: list) -> dict:
    """Cadastra um pedido completo. itens: lista de dicionários com 'id_produto' e 'quantidade'."""
    return cadastrar_pedido_completo(id_cliente, valor_total, tipo_pagamento, itens)

@tool
def listar_pedidos() -> str:
    """Lista todos os pedidos registrados."""
    return str(listar_pedidos_bd())

@tool
def cadastrar_cliente(cpf: str, nome_completo: str, **kwargs) -> dict:
    """Cadastra um novo cliente."""
    return cadastrar_cliente_completo(cpf, nome_completo, **kwargs)

tools = [listar_produtos, cadastrar_pedido, listar_pedidos, cadastrar_cliente]

# ----------------------------------------------------------------------
# PROMPT PARA TOOL CALLING AGENT
# ----------------------------------------------------------------------
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Você é Mario, atendente receptivo e eficiente da Pizzaria Bella Italia.\n\n"
        "Regras Operacionais:\n"
        "1. Quando o cliente informar o produto, quantidade e forma de pagamento, execute a ferramenta 'cadastrar_pedido'.\n"
        "2. NUNCA confirme um pedido sem antes ter chamado a ferramenta 'cadastrar_pedido'.\n"
        "3. Se faltar algum dado para a chamada da função, peça APENAS o que falta.\n"
        "4. Se o cliente não for cadastrado, assuma id_cliente=1 por padrão."
    ),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

# ----------------------------------------------------------------------
# AGENTE
# ----------------------------------------------------------------------
llm = ChatGoogleGenerativeAI(
    model=MODEL_NAME,
    google_api_key=API_KEY,
    temperature=0.1,
)

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5,
)

# ----------------------------------------------------------------------
# FUNÇÃO DE ENVIO
# ----------------------------------------------------------------------
def enviar_mensagem_old(mensagem: str, historico: list) -> str:
    """Envia mensagem e retorna a resposta do agente mantendo o histórico."""
    resultado = agent_executor.invoke({
        "input": mensagem,
        "chat_history": historico,
    })
    return resultado["output"]

def enviar_mensagem(mensagem: str, historico: list) -> str:
    """Envia mensagem e extrai o texto limpo da resposta do agente."""
    resultado = agent_executor.invoke({
        "input": mensagem,
        "chat_history": historico,
    })
    
    output = resultado.get("output", "")
    
    # Caso 1: Saída no formato novo (lista de dicionários/blocos)
    if isinstance(output, list) and len(output) > 0:
        primeiro_item = output[0]
        if isinstance(primeiro_item, dict) and "text" in primeiro_item:
            return primeiro_item["text"]
    
    # Caso 2: Saída tradicional (string simples)
    if isinstance(output, str):
        return output

    # Fallback para outros formatos
    return str(output)

# ----------------------------------------------------------------------
# STREAMLIT UI
# ----------------------------------------------------------------------
def render_chat_page():
    """Renderiza a página do chat."""
    st.header("💬 Atendimento Pizzaria Bella Italia")
    st.caption("Converse com o Mario para fazer seu pedido.")
     # ⚠️ AVISO FIXO - SEMPRE VISÍVEL NO TOPO DA PÁGINA
    st.warning(
        "⚠️ **Esta é uma Inteligência Artificial e pode cometer erros.**\n\n"
        "📋 **Recomendamos:** Revise sempre os dados antes de finalizar.\n"
        "📱 **Atendimento mais rápido:** Entre em contato pelo WhatsApp **(61) 99812-1234**"
    )
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
        st.session_state.id_cliente = 1

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("Digite sua mensagem..."):
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Mario está digitando..."):
                historico = [
                    (msg["role"], msg["content"])
                    for msg in st.session_state.messages[:-1]
                ]
                resposta = enviar_mensagem(user_input, historico)
                st.markdown(resposta)
                st.session_state.messages.append({"role": "assistant", "content": resposta})


if __name__ == "__main__":
    render_chat_page()