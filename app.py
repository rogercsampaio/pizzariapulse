import os
import sys
from abas.analytics import render_analytics_page
import streamlit as st
from loguru import logger
from code.logger_config import setup_logs_once

# ----------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA (DEVE SER A PRIMEIRA CHAMADA STREAMLIT)
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="PizzariaPulse.",
    page_icon="🍕",
    layout="wide",
)

# ----------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGS EM ARQUIVO (logs/pizzaria.log)
# ----------------------------------------------------------------------
# Configura os logs UMA ÚNICA VEZ no início do app
logger = setup_logs_once()

# Restante do código...
logger.info("Aplicação iniciada")

# ----------------------------------------------------------------------
# LAZY LOADING - FUNÇÕES PARA CARREGAR OS MÓDULOS SOB DEMANDA
# ----------------------------------------------------------------------
def get_render_chat_page():
    """Carrega o módulo chatbot apenas quando necessário."""
    from abas.chatbot import render_chat_page
    return render_chat_page

def get_render_cardapio_page():
    """Carrega o módulo cardapio apenas quando necessário."""
    from abas.cardapio import render_cardapio_page
    return render_cardapio_page

def get_render_pedidos_page():
    """Carrega o módulo pedidos apenas quando necessário."""
    from abas.pedidos import render_pedidos_page
    return render_pedidos_page

def get_render_clientes_page():
    """Carrega o módulo clientes apenas quando necessário."""
    from abas.clientes import render_clientes_page
    return render_clientes_page

def get_render_analytics_page():
    """Carrega o módulo analytics apenas quando necessário."""
    from abas.analytics import render_analytics_page
    return render_analytics_page

# ----------------------------------------------------------------------
# CRIAÇÃO DAS ABAS NA INTERFACE
# ----------------------------------------------------------------------
aba_chat, aba_cardapio, aba_pedidos, aba_clientes, aba_analytics = st.tabs(
    ["💬 Atendimento (Chat)", "📋 Cardápio", "📦 Pedidos Realizados", "👥 Clientes", "📊 Analytics"]
)

# ----------------------------------------------------------------------
# ABA 1: CHATBOT
# ----------------------------------------------------------------------
with aba_chat:
    render_chat = get_render_chat_page()
    render_chat()

# ----------------------------------------------------------------------
# ABA 2: CARDÁPIO (Visão rápida extra)
# ----------------------------------------------------------------------
with aba_cardapio:
    render_cardapio = get_render_cardapio_page()
    render_cardapio()

# ----------------------------------------------------------------------
# ABA 3: PEDIDOS (Visão rápida de histórico)
# ----------------------------------------------------------------------
with aba_pedidos:
    render_pedidos = get_render_pedidos_page()
    render_pedidos()

# ----------------------------------------------------------------------
# ABA 4: CLIENTES (Visão rápida de gerenciamento)
# ----------------------------------------------------------------------
with aba_clientes:
    render_clientes = get_render_clientes_page()
    render_clientes()

# ----------------------------------------------------------------------
# ABA 5: ANALYTICS (Visão rápida de análise de dados)
# ----------------------------------------------------------------------
with aba_analytics:
    render_analytics = get_render_analytics_page()
    render_analytics()
