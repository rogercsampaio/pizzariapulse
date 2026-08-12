import streamlit as st
import pandas as pd
from code.funcoes_bd import listar_todos_clientes_enderecos
from loguru import logger 

logger.info("Renderizando página de clientes")

def formatar_cpf(cpf):
    """Formata CPF: 032.477.521-02"""
    if not cpf:
        return "N/A"
    
    cpf_limpo = ''.join(filter(str.isdigit, str(cpf)))
    
    if len(cpf_limpo) == 11:
        return f"{cpf_limpo[:3]}.{cpf_limpo[3:6]}.{cpf_limpo[6:9]}-{cpf_limpo[9:]}"
    return cpf

def formatar_telefone(telefone):
    """Formata telefone: (61) 99812-1121"""
    if not telefone:
        return "N/A"
    
    telefone_limpo = ''.join(filter(str.isdigit, str(telefone)))
    
    if len(telefone_limpo) == 11:  # Celular com DDD + 9 dígitos
        return f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
    elif len(telefone_limpo) == 10:  # Fixo com DDD + 8 dígitos
        return f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
    elif len(telefone_limpo) == 9:  # Celular sem DDD
        return f"{telefone_limpo[:5]}-{telefone_limpo[5:]}"
    elif len(telefone_limpo) == 8:  # Fixo sem DDD
        return f"{telefone_limpo[:4]}-{telefone_limpo[4:]}"
    return telefone

def formatar_cep(cep):
    """Formata CEP: 72025-650"""
    if not cep:
        return "N/A"
    
    cep_limpo = ''.join(filter(str.isdigit, str(cep)))
    
    if len(cep_limpo) == 8:
        return f"{cep_limpo[:5]}-{cep_limpo[5:]}"
    return cep

def formatar_data(data):
    """Formata data: 11/10/2001"""
    if not data:
        return "N/A"
    
    try:
        from datetime import datetime
        if isinstance(data, str):
            dt = datetime.strptime(data, "%Y-%m-%d")
        else:
            dt = data
        return dt.strftime("%d/%m/%Y")
    except:
        return data

def render_clientes_page():
    st.header("👥 Gerenciamento de Clientes")
    st.caption("Consulte a lista de todos os clientes cadastrados no sistema.")

    # Busca a lista de clientes com endereços no banco de dados
    clientes = listar_todos_clientes_enderecos()

    if not clientes:
        st.info("Nenhum cliente cadastrado no momento.")
        return

    # Converte a lista de dicionários em um DataFrame do pandas
    df_clientes = pd.DataFrame(clientes)

    if df_clientes.empty:
        st.info("Nenhum cliente cadastrado no momento.")
        return

    # Extrai dados do endereço para colunas separadas
    if "endereco" in df_clientes.columns:
        df_clientes["rua"] = df_clientes["endereco"].apply(lambda x: x.get("rua", "N/A") if x else "N/A")
        df_clientes["numero"] = df_clientes["endereco"].apply(lambda x: x.get("numero", "N/A") if x else "N/A")
        df_clientes["bairro"] = df_clientes["endereco"].apply(lambda x: x.get("bairro", "N/A") if x else "N/A")
        df_clientes["cidade"] = df_clientes["endereco"].apply(lambda x: x.get("cidade", "N/A") if x else "N/A")
        df_clientes["cep"] = df_clientes["endereco"].apply(lambda x: formatar_cep(x.get("cep")) if x else "N/A")
        df_clientes["complemento"] = df_clientes["endereco"].apply(lambda x: x.get("complemento", "N/A") if x and x.get("complemento") else "Sem complemento")
        df_clientes["id_endereco"] = df_clientes["endereco"].apply(lambda x: x.get("id_endereco") if x else None)

    # Aplica formatação aos dados
    if "cpf" in df_clientes.columns:
        df_clientes["cpf"] = df_clientes["cpf"].apply(formatar_cpf)
    
    if "telefone" in df_clientes.columns:
        df_clientes["telefone"] = df_clientes["telefone"].apply(formatar_telefone)
    
    if "data_nascimento" in df_clientes.columns:
        df_clientes["data_nascimento"] = df_clientes["data_nascimento"].apply(formatar_data)
    
    if "data_cadastro" in df_clientes.columns:
        df_clientes["data_cadastro"] = pd.to_datetime(df_clientes["data_cadastro"]).dt.strftime("%d/%m/%Y %H:%M")

    # Métricas no topo
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Clientes", len(df_clientes))
    with col2:
        masculino = len(df_clientes[df_clientes["sexo"] == "Masculino"]) if "sexo" in df_clientes.columns else 0
        st.metric("👨 Masculino", masculino)
    with col3:
        feminino = len(df_clientes[df_clientes["sexo"] == "Feminino"]) if "sexo" in df_clientes.columns else 0
        st.metric("👩 Feminino", feminino)

    st.divider()

    # Filtros
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        termo_busca = st.text_input("🔍 Buscar cliente por Nome ou CPF:", "")
    
    with col_filtro2:
        # Filtro por sexo
        sexo_options = ["Todos", "Masculino", "Feminino"]
        sexo_filtro = st.selectbox("⚥ Filtrar por Sexo:", sexo_options)

    # Aplica filtros
    df_filtrado = df_clientes.copy()
    
    # Filtro por nome/CPF
    if termo_busca:
        termo_busca_lower = termo_busca.lower()
        df_filtrado = df_filtrado[
            df_filtrado["nome_completo"].str.lower().str.contains(termo_busca_lower, na=False) |
            df_filtrado["cpf"].str.contains(termo_busca, na=False)
        ]
    
    # Filtro por sexo
    if sexo_filtro != "Todos" and "sexo" in df_filtrado.columns:
        df_filtrado = df_filtrado[df_filtrado["sexo"] == sexo_filtro]

    # Exibição da tabela interativa
    st.subheader(f"📋 Lista de Clientes ({len(df_filtrado)})")
    
    # Seleciona as colunas para exibir na tabela
    colunas_exibir = ["id_cliente", "nome_completo", "cpf", "telefone", "sexo", "cidade", "data_cadastro"]
    colunas_exibir = [col for col in colunas_exibir if col in df_filtrado.columns]
    
    df_tabela = df_filtrado[colunas_exibir].copy()
    
    # Renomeia colunas para exibição
    mapeamento = {
        "id_cliente": "ID",
        "nome_completo": "Nome Completo",
        "cpf": "CPF",
        "telefone": "Telefone",
        "sexo": "Sexo",
        "cidade": "Cidade",
        "data_cadastro": "Data Cadastro"
    }
    df_tabela = df_tabela.rename(columns=mapeamento)

    # Configuração das colunas
    column_config = {
        "ID": st.column_config.NumberColumn("ID", format="%d", width="small"),
        "Nome Completo": st.column_config.TextColumn("Nome Completo", width="large"),
        "CPF": st.column_config.TextColumn("CPF", width="medium"),
        "Telefone": st.column_config.TextColumn("Telefone", width="medium"),
        "Sexo": st.column_config.TextColumn("Sexo", width="small"),
        "Cidade": st.column_config.TextColumn("Cidade", width="medium"),
        "Data Cadastro": st.column_config.TextColumn("Data Cadastro", width="medium"),
    }

    # Adiciona a coluna de seleção
    event = st.dataframe(
        df_tabela,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
        selection_mode="single-row",
        on_select="rerun"
    )

    # Exibe detalhes do cliente selecionado
    if event.selection and event.selection.rows:
        selected_idx = event.selection.rows[0]
        if selected_idx < len(df_filtrado):
            cliente_selecionado = df_filtrado.iloc[selected_idx]
            
            st.divider()
            st.subheader(f"📄 Detalhes do Cliente: {cliente_selecionado['nome_completo']}")
            
            # Organiza os detalhes em colunas
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**👤 Dados Pessoais**")
                st.write(f"**ID:** {cliente_selecionado['id_cliente']}")
                st.write(f"**Nome:** {cliente_selecionado['nome_completo']}")
                st.write(f"**CPF:** {cliente_selecionado['cpf']}")
                st.write(f"**Data Nascimento:** {cliente_selecionado['data_nascimento']}")
                st.write(f"**Email:** {cliente_selecionado.get('email', 'N/A')}")
                st.write(f"**Telefone:** {cliente_selecionado['telefone']}")
                st.write(f"**Sexo:** {cliente_selecionado['sexo']}")
            
            with col2:
                st.markdown("**📍 Endereço**")
                st.write(f"**Rua:** {cliente_selecionado.get('rua', 'N/A')}")
                st.write(f"**Número:** {cliente_selecionado.get('numero', 'N/A')}")
                st.write(f"**Bairro:** {cliente_selecionado.get('bairro', 'N/A')}")
                st.write(f"**Cidade:** {cliente_selecionado.get('cidade', 'N/A')}")
                st.write(f"**CEP:** {cliente_selecionado.get('cep', 'N/A')}")
                st.write(f"**Complemento:** {cliente_selecionado.get('complemento', 'N/A')}")
                st.write(f"**ID Endereço:** {cliente_selecionado.get('id_endereco', 'N/A')}")
            
            st.caption(f"📅 Cadastrado em: {cliente_selecionado['data_cadastro']}")

if __name__ == "__main__":
    render_clientes_page()