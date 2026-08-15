import os
import sys
from pathlib import Path

import streamlit as st
from loguru import logger

from code.logger_config import setup_logs_once


# ----------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# DEVE SER A PRIMEIRA CHAMADA STREAMLIT
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="PizzariaPulse",
    page_icon="🍕",
    layout="wide",
)


# ----------------------------------------------------------------------
# CARREGAMENTO DO TEMA CSS
# ----------------------------------------------------------------------
def carregar_css():
    css_path = Path(__file__).parent / "pizzapulse_theme.css"

    if not css_path.exists():
        st.warning("Arquivo pizzapulse_theme.css não encontrado.")
        return

    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    st.markdown(
        f"<style>{css}</style>",
        unsafe_allow_html=True
    )


carregar_css()


# ----------------------------------------------------------------------
# POPUP DE BOAS-VINDAS
# ----------------------------------------------------------------------
@st.dialog("🍕 Bem-vindo ao PizzariaPulse")
def popup_boas_vindas():

    # Caminho da imagem
    imagem_path = (
        Path(__file__).parent
        / "imagens"
        / "pizzaria_pulse_banner.png"
    )

    # Exibe a imagem
    if imagem_path.exists():
        st.image(
            str(imagem_path),
            use_container_width=True
        )
    else:
        st.warning(
            f"Imagem não encontrada: {imagem_path}"
        )

    # Apresentação
    st.subheader(
        "Seu atendimento inteligente para pizzarias"
    )

    st.write(
        "Um Assistente Autônomo de IA para automatizar "
        "o atendimento, otimizar pedidos e acompanhar "
        "os principais indicadores da sua operação."
    )

    st.markdown("---")

    # Principais recursos
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### 🤖 IA Autônoma")
        st.caption(
            "Atendimento inteligente"
        )

    with col2:
        st.markdown("### 📦 Pedidos")
        st.caption(
            "Mais agilidade na operação"
        )

    with col3:
        st.markdown("### 📊 Analytics")
        st.caption(
            "Decisões baseadas em dados"
        )

    st.markdown("")

    # Botão para entrar
    if st.button(
        "🚀 Acessar PizzariaPulse",
        use_container_width=True,
        type="primary"
    ):
        st.session_state.popup_exibido = True
        st.rerun()


# ----------------------------------------------------------------------
# CONTROLE DO POPUP
# APARECE APENAS NA PRIMEIRA ABERTURA DA SESSÃO
# ----------------------------------------------------------------------
if "popup_exibido" not in st.session_state:
    st.session_state.popup_exibido = False
    popup_boas_vindas()


# ----------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGS
# ----------------------------------------------------------------------
logger = setup_logs_once()

logger.info("Aplicação iniciada")


# ----------------------------------------------------------------------
# LAZY LOADING
# ----------------------------------------------------------------------
def get_render_chat_page():
    from abas.chatbot import render_chat_page
    return render_chat_page


def get_render_cardapio_page():
    from abas.cardapio import render_cardapio_page
    return render_cardapio_page


def get_render_pedidos_page():
    from abas.pedidos import render_pedidos_page
    return render_pedidos_page


def get_render_clientes_page():
    from abas.clientes import render_clientes_page
    return render_clientes_page


def get_render_analytics_page():
    from abas.analytics import render_analytics_page
    return render_analytics_page


# ----------------------------------------------------------------------
# ABAS
# ----------------------------------------------------------------------
aba_chat, aba_cardapio, aba_pedidos, aba_clientes, aba_analytics = st.tabs(
    [
        "💬 Atendimento (Chat)",
        "📋 Cardápio",
        "📦 Pedidos Realizados",
        "👥 Clientes",
        "📊 Analytics",
    ]
)


# ----------------------------------------------------------------------
# ABA - CHAT
# ----------------------------------------------------------------------
with aba_chat:
    render_chat = get_render_chat_page()
    render_chat()


# ----------------------------------------------------------------------
# ABA - CARDÁPIO
# ----------------------------------------------------------------------
with aba_cardapio:
    render_cardapio = get_render_cardapio_page()
    render_cardapio()


# ----------------------------------------------------------------------
# ABA - PEDIDOS
# ----------------------------------------------------------------------
with aba_pedidos:
    render_pedidos = get_render_pedidos_page()
    render_pedidos()


# ----------------------------------------------------------------------
# ABA - CLIENTES
# ----------------------------------------------------------------------
with aba_clientes:
    render_clientes = get_render_clientes_page()
    render_clientes()


# ----------------------------------------------------------------------
# ABA - ANALYTICS
# ----------------------------------------------------------------------
with aba_analytics:
    render_analytics = get_render_analytics_page()
    render_analytics()