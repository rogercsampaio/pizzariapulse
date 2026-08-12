import os
import sys
import pandas as pd
import streamlit as st
from loguru import logger
from code.funcoes_bd import listar_produtos
from pathlib import Path
from PIL import Image

# ----------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGS
# ----------------------------------------------------------------------
logger.info("Renderizando página de cardápio")

# ----------------------------------------------------------------------
# CONFIGURAÇÃO
# ----------------------------------------------------------------------
RAIZ_PROJETO = Path(__file__).parent.parent
PASTA_IMAGENS = RAIZ_PROJETO / "imagens"

# ============================================================
# 🔧 CONFIGURAÇÃO: MOSTRAR IMAGENS?
# ============================================================
MOSTRAR_IMAGENS = True

# Imagem padrão
IMAGEM_PADRAO = "https://placehold.co/300x200/png?text=Sem+Foto"

# Dimensões padronizadas para miniaturas
LARGURA_IMG = 300
ALTURA_IMG = 200

# ----------------------------------------------------------------------
# FUNÇÕES COM CACHE
# ----------------------------------------------------------------------
@st.cache_data(ttl=300)
def carregar_produtos_com_cache():
    """Carrega os produtos do banco de dados com cache."""
    logger.info("Carregando produtos do banco de dados (cache miss).")
    produtos = listar_produtos()
    
    if not produtos:
        logger.warning("Nenhum produto encontrado no banco de dados.")
        return pd.DataFrame()
    
    df = pd.DataFrame(
        produtos,
        columns=["id_produto", "foto_produto_caminho", "nome", "descricao", "preco"]
    )
    
    df = df.rename(
        columns={
            "id_produto": "ID",
            "foto_produto_caminho": "Foto",
            "nome": "Produto",
            "preco": "Preço (R$)",
            "descricao": "Descrição",
        }
    )
    
    return df


@st.cache_data
def get_metricas(df_produtos):
    """Calcula métricas do cardápio com cache."""
    total = len(df_produtos)
    preco_medio = df_produtos["Preço (R$)"].mean() if total > 0 else 0
    preco_max = df_produtos["Preço (R$)"].max() if total > 0 else 0
    return total, preco_medio, preco_max


# ----------------------------------------------------------------------
# FUNÇÕES DE IMAGEM
# ----------------------------------------------------------------------
def resolver_caminho_imagem(caminho_foto: str) -> str:
    """Resolve o caminho da imagem."""
    if not caminho_foto or not isinstance(caminho_foto, str):
        return IMAGEM_PADRAO

    if caminho_foto.startswith("http://") or caminho_foto.startswith("https://"):
        return caminho_foto

    caminho_limpo = caminho_foto.lstrip("/\\")
    caminho_absoluto = RAIZ_PROJETO / caminho_limpo

    if caminho_absoluto.exists():
        return str(caminho_absoluto)

    nome_arquivo = Path(caminho_limpo).name
    caminho_alternativo = PASTA_IMAGENS / nome_arquivo
    
    if caminho_alternativo.exists():
        return str(caminho_alternativo)

    return IMAGEM_PADRAO


@st.cache_data
def carregar_e_padronizar_imagem(caminho, largura=LARGURA_IMG, altura=ALTURA_IMG):
    """Carrega e padroniza imagem como miniatura."""
    try:
        if isinstance(caminho, str) and (caminho.startswith("http://") or caminho.startswith("https://")):
            return caminho

        img = Image.open(caminho)
        
        # Mantém a proporção e redimensiona para miniatura
        img.thumbnail((largura, altura), Image.Resampling.LANCZOS)
        
        # Cria uma imagem com fundo branco do tamanho exato
        img_final = Image.new('RGB', (largura, altura), (255, 255, 255))
        
        # Centraliza a imagem no fundo branco
        x = (largura - img.width) // 2
        y = (altura - img.height) // 2
        img_final.paste(img, (x, y))
        
        return img_final
    except Exception as e:
        logger.error(f"Erro ao processar imagem: {e}")
        return IMAGEM_PADRAO


# ----------------------------------------------------------------------
# RENDERIZAÇÃO DA PÁGINA
# ----------------------------------------------------------------------
def render_cardapio_page():
    """Renderiza a página de Cardápio."""
    logger.info("Renderizando a página de Cardápio.")

    if not MOSTRAR_IMAGENS:
        st.info("ℹ️ **Modo rápido ativado** - Imagens desabilitadas.")

    st.header("📋 Cardápio Cadastrado")
    st.write("Consulte os produtos disponíveis no banco de dados em tempo real.")

    # ------------------------------------------------------------------
    # CARREGA DADOS COM CACHE
    # ------------------------------------------------------------------
    df_produtos = carregar_produtos_com_cache()
    
    if df_produtos.empty:
        st.warning("Nenhum produto encontrado no banco de dados.")
        return

    # ------------------------------------------------------------------
    # MÉTRICAS
    # ------------------------------------------------------------------
    total, preco_medio, preco_max = get_metricas(df_produtos)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Produtos", total)
    with col2:
        st.metric("Preço Médio", f"R$ {preco_medio:.2f}")
    with col3:
        st.metric("Maior Valor", f"R$ {preco_max:.2f}")

    st.divider()

    # ------------------------------------------------------------------
    # FILTRO
    # ------------------------------------------------------------------
    termo_busca = st.text_input(
        "🔍 Buscar produto pelo nome:",
        placeholder="Ex: Calabr, Muçarela, Coca-Cola...",
    )

    if termo_busca:
        df_exibicao = df_produtos[
            df_produtos["Produto"].str.contains(termo_busca, case=False, na=False)
        ]
    else:
        df_exibicao = df_produtos

    if df_exibicao.empty:
        st.info("Nenhum produto atende aos critérios da busca.")
        return

    # ------------------------------------------------------------------
    # MODO DE VISUALIZAÇÃO
    # ------------------------------------------------------------------
    modo_visao = st.radio(
        "Modo de exibição:",
        options=["🍕 Cartões do Cardápio", "📊 Tabela de Dados"],
        horizontal=True,
    )

    if modo_visao == "📊 Tabela de Dados":
        colunas = ["ID", "Produto", "Preço (R$)", "Descrição"]
        if MOSTRAR_IMAGENS:
            # Adiciona uma coluna com a imagem em miniatura
            df_exibicao["Miniatura"] = df_exibicao["Foto"].apply(resolver_caminho_imagem)
            colunas.insert(1, "Miniatura")
        
        st.dataframe(
            df_exibicao[colunas],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Preço (R$)": st.column_config.NumberColumn(
                    "Preço (R$)", format="R$ %.2f"
                ),
                "Miniatura": st.column_config.ImageColumn(
                    "Foto", width="small"
                ),
            } if MOSTRAR_IMAGENS else {}
        )
    
    else:
        # Modo Cartões - GRADE DE PRODUTOS
        # Define quantas colunas por linha (ajustável)
        colunas_por_linha = 3
        cols = st.columns(colunas_por_linha)
        
        for idx, row in df_exibicao.reset_index(drop=True).iterrows():
            with cols[idx % colunas_por_linha]:
                with st.container(border=True):
                    
                    # ============================================================
                    # IMAGEM COMO MINIATURA
                    # ============================================================
                    if MOSTRAR_IMAGENS:
                        try:
                            foto = resolver_caminho_imagem(row["Foto"])
                            
                            # Carrega e padroniza como miniatura
                            img_padronizada = carregar_e_padronizar_imagem(foto)
                            
                            if isinstance(img_padronizada, str):
                                st.image(img_padronizada, use_container_width=True)
                            else:
                                # Exibe a imagem com tamanho fixo
                                st.image(img_padronizada, use_container_width=True)
                                
                        except Exception as e:
                            logger.error(f"Erro ao exibir imagem: {e}")
                            st.image(IMAGEM_PADRAO, use_container_width=True)
                    else:
                        st.markdown("🍕")
                    
                    # ============================================================
                    # INFORMAÇÕES DO PRODUTO
                    # ============================================================
                    st.subheader(f"{row['Produto']}")
                    st.markdown(f"**Preço:** `R$ {row['Preço (R$)']:.2f}`")
                    st.caption(f"📝 {row['Descrição']}")
                    
                    # Botão de adicionar (opcional)
                    #if st.button(f"➕ Adicionar", key=f"add_{row['ID']}"):
                    #    st.toast(f"✅ {row['Produto']} adicionado!", icon="🍕")
    
    # ------------------------------------------------------------------
    # BOTÃO PARA RECARREGAR
    # ------------------------------------------------------------------
    if st.button("🔄 Recarregar Cardápio"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    render_cardapio_page()