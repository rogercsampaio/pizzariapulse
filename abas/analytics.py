import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Importação das funções do banco de dados
from code.funcoes_bd import (
    obter_metricas_gerais_vendas,
    obter_historico_vendas_por_data,
    obter_vendas_por_produto,
    listar_pedidos,
    obter_top_clientes
)

def render_analytics_page():
    st.title("📊 Painel de Analytics & Vendas")
    st.markdown("Acompanhe o desempenho das vendas, faturamento total, produtos mais vendidos e meios de pagamento.")

    # ------------------------------------------------------------------
    # CARDS DE MÉTRICAS
    # ------------------------------------------------------------------
    metricas = obter_metricas_gerais_vendas()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="📦 Total de Produtos Vendidos (Qtd)",
            value=f"{metricas.get('total_itens_vendidos', 0):,}"
        )

    with col2:
        st.metric(
            label="💵 Faturamento Total",
            value=f"R$ {metricas.get('faturamento_total', 0.0):,.2f}"
        )

    with col3:
        st.metric(
            label="🎯 Ticket Médio por Cliente/Pedido",
            value=f"R$ {metricas.get('ticket_medio', 0.0):,.2f}"
        )

    st.divider()

    # ------------------------------------------------------------------
    # GRÁFICOS: HISTÓRICO EM ÁREA E PERCENTUAL POR FORMA DE PAGAMENTO
    # ------------------------------------------------------------------
    historico = obter_historico_vendas_por_data()

    if historico:
        df_historico = pd.DataFrame(historico)
        df_historico['data_hora_pedido'] = pd.to_datetime(df_historico['data_hora_pedido'])

        col_g1, col_g2 = st.columns([6, 4])

        with col_g1:
            st.subheader("📈 Histórico de Vendas (Evolução Temporal)")
            # Gráfico de linha preenchida por baixo (px.area)
            fig_historico = px.area(
                df_historico,
                x='data_hora_pedido',
                y='valor_total',
                markers=True,
                title="Evolução do Faturamento ao Longo do Tempo",
                labels={'data_hora_pedido': 'Data e Hora', 'valor_total': 'Valor do Pedido (R$)'},
                hover_data=['id_pedido', 'tipo_pagamento']
            )
            fig_historico.update_traces(
                line_color="#2E7D32",
                fillcolor="rgba(46, 125, 50, 0.2)"
            )
            st.plotly_chart(fig_historico, use_container_width=True)

        with col_g2:
            st.subheader("💳 Vendas por Forma de Pagamento")
            # Agrupamento e cálculo percentual por tipo_pagamento
            df_pagamento = df_historico.groupby('tipo_pagamento')['valor_total'].sum().reset_index()

            fig_pizza = px.pie(
                df_pagamento,
                names='tipo_pagamento',
                values='valor_total',
                title="Percentual de Faturamento por Tipo de Pagamento",
                hole=0.4,  # Estilo rosca
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pizza.update_traces(
                textinfo='percent+label',
                hoverinfo='label+value+percent'
            )
            st.plotly_chart(fig_pizza, use_container_width=True)

    else:
        st.info("Nenhum pedido registrado para exibir os gráficos.")

    st.divider()

    # ------------------------------------------------------------------
    # GRÁFICO DE BARRAS: VALOR DE VENDAS POR PRODUTO E QUANTIDADE
    # ------------------------------------------------------------------
    st.subheader("📊 Vendas por Produto (Valor e Quantidade)")
    vendas_prod = obter_vendas_por_produto()

    if vendas_prod:
        df_vendas_prod = pd.DataFrame(vendas_prod)

        fig_barras = go.Figure()

        # Barra 1: Valor Total em R$
        fig_barras.add_trace(
            go.Bar(
                x=df_vendas_prod['produto'],
                y=df_vendas_prod['valor_total'],
                name='Valor Total (R$)',
                marker_color='#1976D2',
                text=[f"R$ {v:,.2f}" for v in df_vendas_prod['valor_total']],
                textposition='auto'
            )
        )

        # Barra 2: Quantidade Vendida
        fig_barras.add_trace(
            go.Bar(
                x=df_vendas_prod['produto'],
                y=df_vendas_prod['quantidade_total'],
                name='Quantidade Vendida',
                marker_color='#FF9800',
                text=df_vendas_prod['quantidade_total'],
                textposition='auto'
            )
        )

        fig_barras.update_layout(
            barmode='group',
            title='Comparativo: Valor Total Faturado vs Quantidade Vendida por Produto',
            xaxis_title='Produto',
            yaxis_title='Valores',
            legend_title='Métrica'
        )

        st.plotly_chart(fig_barras, use_container_width=True)
    else:
        st.info("Nenhum dado de venda por produto disponível.")

    st.divider()

    # ------------------------------------------------------------------
    # TABELAS (TABELA DE VENDAS E TOP CLIENTES)
    # ------------------------------------------------------------------
    col_tab1, col_tab2 = st.columns([6, 4])

    with col_tab1:
        st.subheader("📋 Tabela Geral de Vendas")
        pedidos = listar_pedidos()

        if pedidos:
            df_pedidos = pd.DataFrame(pedidos)

            # Garantir conversão de estruturas aninhadas em texto para evitar [object Object]
            for col in df_pedidos.columns:
                df_pedidos[col] = df_pedidos[col].apply(
                    lambda val: str(val) if isinstance(val, (dict, list)) else val
                )

            colunas_map = {
                'id_pedido': 'ID Pedido',
                'id_cliente': 'ID Cliente',
                'nome_cliente': 'Cliente',
                'data_hora_pedido': 'Data/Hora',
                'valor_total': 'Valor Total (R$)',
                'tipo_pagamento': 'Pagamento',
                'nome_produto': 'Produto',
                'quantidade': 'Qtd',
                'preco_unitario_momento': 'Preço Unit. (R$)',
                'itens': 'Itens'
            }

            cols_existentes = {k: v for k, v in colunas_map.items() if k in df_pedidos.columns}
            df_exibicao = df_pedidos.rename(columns=cols_existentes)

            if 'Valor Total (R$)' in df_exibicao.columns:
                df_exibicao['Valor Total (R$)'] = df_exibicao['Valor Total (R$)'].apply(
                    lambda x: f"R$ {float(x):,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else str(x)
                )

            st.dataframe(
                df_exibicao,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum pedido encontrado.")

    with col_tab2:
        st.subheader("🏆 Clientes que Mais Compraram")
        top_clientes = obter_top_clientes(limit=10)

        if top_clientes:
            df_top_clientes = pd.DataFrame(top_clientes)

            df_top_exibicao = df_top_clientes.rename(columns={
                'nome_completo': 'Nome do Cliente',
                'total_pedidos': 'Qtd. Pedidos',
                'total_gasto': 'Total Gasto (R$)'
            })[['Nome do Cliente', 'Qtd. Pedidos', 'Total Gasto (R$)']]

            df_top_exibicao['Total Gasto (R$)'] = df_top_exibicao['Total Gasto (R$)'].apply(
                lambda x: f"R$ {float(x):,.2f}" if pd.notnull(x) else "R$ 0,00"
            )

            st.dataframe(
                df_top_exibicao,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhum cliente cadastrado com compras efetuadas.")


if __name__ == "__main__":
    st.set_page_config(page_title="Analytics", layout="wide")
    render_analytics_page()