import os
import sys
import pandas as pd
import streamlit as st
from loguru import logger
from code.funcoes_bd import listar_pedidos

# ----------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGS (Direcionado para a pasta logs/)
# ----------------------------------------------------------------------
logger.info("Renderizando página de pedidos")

def render_pedidos_page():
    """Renderiza a página de Histórico de Pedidos e Vendas do sistema."""
    logger.info("Renderizando a página de Pedidos Realizados.")

   
    st.header("📦 Histórico de Pedidos Realizados")
    st.write("Acompanhe o status e os detalhes de cada venda registrada.")

    # Busca os pedidos do banco de dados
    try:
        pedidos = listar_pedidos()
        logger.info(f"Pedidos carregados: {len(pedidos) if pedidos else 0}")
    except Exception as e:
        logger.error(f"Erro ao carregar pedidos: {e}")
        st.error("Erro ao carregar pedidos. Tente novamente mais tarde.")
        return

    if not pedidos:
        logger.warning("Nenhum pedido encontrado na consulta ao banco de dados.")
        st.info("Nenhum pedido registrado até o momento.")
        return

    # ------------------------------------------------------------------
    # MÉTRICAS EXECUTIVAS / DASHBOARD RÁPIDO
    # ------------------------------------------------------------------
    total_pedidos = len(pedidos)
    faturamento_total = sum(p.get("valor_total", 0) for p in pedidos)
    ticket_medio = faturamento_total / total_pedidos if total_pedidos > 0 else 0.0


    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total de Pedidos", total_pedidos)
    with col2:
        st.metric("Faturamento Total", f"R$ {faturamento_total:,.2f}")
    with col3:
        st.metric("Ticket Médio", f"R$ {ticket_medio:.2f}")
  

    st.divider()

    # ------------------------------------------------------------------
    # FILTROS
    # ------------------------------------------------------------------
    col_busca, col_status = st.columns([2, 1])

    with col_busca:
        termo_busca = st.text_input(
            "🔍 Buscar por ID do Pedido ou Cliente:",
            placeholder="Ex: 1, 10, cliente...",
        )

    with col_status:
        # Extrai todos os status existentes nos pedidos para montar o filtro
        todos_status = sorted(list(set(p.get("estado", "Desconhecido") for p in pedidos)))
        status_selecionado = st.selectbox(
            "Filtrar por Estado:",
            options=["Todos"] + todos_status,
        )

    # Aplicação dos Filtros
    pedidos_filtrados = pedidos

    if status_selecionado != "Todos":
        pedidos_filtrados = [
            p for p in pedidos_filtrados if p.get("estado") == status_selecionado
        ]

    if termo_busca:
        logger.info(f"Filtro de busca em pedidos aplicado: '{termo_busca}'")
        termo_lower = termo_busca.lower()
        pedidos_filtrados = [
            p
            for p in pedidos_filtrados
            if termo_lower in str(p.get("id_pedido", ""))
            or termo_lower in str(p.get("id_cliente", "")).lower()
        ]

    st.subheader(f"📋 Pedidos ({len(pedidos_filtrados)})")

    if not pedidos_filtrados:
        st.warning("Nenhum pedido atende aos filtros selecionados.")
        return

    # ------------------------------------------------------------------
    # LISTAGEM DETALHADA DOS PEDIDOS
    # ------------------------------------------------------------------
    for p in pedidos_filtrados:
       
        # Formata a data
        data_pedido = p.get("data_hora_pedido", "Data não disponível")
        if data_pedido and data_pedido != "Data não disponível":
            try:
                # Tenta formatar a data
                from datetime import datetime
                if isinstance(data_pedido, str):
                    dt = datetime.fromisoformat(data_pedido.replace(' ', 'T'))
                    data_formatada = dt.strftime("%d/%m/%Y %H:%M")
                else:
                    data_formatada = data_pedido
            except:
                data_formatada = data_pedido
        else:
            data_formatada = data_pedido

        titulo_expander = (
            f"📦 Pedido #{p.get('id_pedido', 'N/A')} | "
            f"Cliente: {p.get('id_cliente', 'N/A')} | "
            f"Total: R$ {p.get('valor_total', 0):.2f} | "
            f"📅 {data_formatada}"
        )

        with st.expander(titulo_expander, expanded=False):
            c1, c2 = st.columns(2)  # ✅ REDUZIDO para 2 colunas (removeu e_entrega)
            with c1:
                st.write(f"**ID do Pedido:** #{p.get('id_pedido', 'N/A')}")
                st.write(f"**Cliente ID:** {p.get('id_cliente', 'N/A')}")
            with c2:
                st.write(f"**Forma de Pagamento:** {p.get('tipo_pagamento', 'N/A')}")
                st.write(f"**Data/Hora:** {data_formatada}")  # ✅ MOVIDO para cá

            st.markdown("#### 🍕 Itens do Pedido")

            itens = p.get("itens", [])
            if itens:
                # Converte os itens do pedido em um DataFrame limpo para exibição
                df_itens = pd.DataFrame(itens)
                
                # Verifica se as colunas existem
                colunas_necessarias = ["produto", "quantidade", "preco_unitario", "subtotal"]
                colunas_existentes = [col for col in colunas_necessarias if col in df_itens.columns]
                
                if colunas_existentes:
                    df_itens = df_itens.rename(
                        columns={
                            "produto": "Produto",
                            "quantidade": "Qtd",
                            "preco_unitario": "Preço Unit. (R$)",
                            "subtotal": "Subtotal (R$)",
                        }
                    )

                    st.dataframe(
                        df_itens[["Produto", "Qtd", "Preço Unit. (R$)", "Subtotal (R$)"]],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "Preço Unit. (R$)": st.column_config.NumberColumn(
                                format="R$ %.2f"
                            ),
                            "Subtotal (R$)": st.column_config.NumberColumn(
                                format="R$ %.2f"
                            ),
                        },
                    )
                    
                    # Mostra o total do pedido
                    st.markdown(f"**Total do Pedido:** R$ {p.get('valor_total', 0):.2f}")
                else:
                    st.caption("Estrutura dos itens não reconhecida.")
            else:
                st.caption("Nenhum item vinculado a este pedido.")

    # ------------------------------------------------------------------
    # BOTÃO PARA RECARREGAR
    # ------------------------------------------------------------------
    if st.button("🔄 Recarregar Pedidos"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    render_pedidos_page()