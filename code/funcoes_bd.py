# funcoes_bd.py
# Esse script tem por objetivo explorar as funções de manipulação no banco de dados
# tais como, seleção, alteração, exclusão, cadastro das entidades: cliente, endereço,
# pedido, pedido_produto, produto, feedback. O banco de dados será o sqlite3, nativo do próprio python.

import os
import sys
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger
from typing import List, TypedDict, Union, Annotated
from pydantic import Field

from datetime import datetime

# Importes das validações
from code.funcoes_validacoes import (
    validar_cpf,
    validar_telefone,
    validar_data_nascimento,
    validar_e_buscar_cep,
    validar_nome,
    validar_sexo,
    validar_email_completo,
    validar_pagamento,
    validar_forma_entrega
)

logger.info("Configurações de banco de dados carregadas com sucesso.")
DB_NAME = "bases/pizzaria.db"

# ----------------------------------------------------------------------
# FUNÇÕES GERAIS DO BANCO DE DADOS
# ----------------------------------------------------------------------
def conectar() -> Optional[sqlite3.Connection]:
    """Retorna uma conexão com o banco de dados SQLite com suporte a Foreign Keys."""
    try:
        conexao = sqlite3.connect(DB_NAME)
        conexao.execute("PRAGMA foreign_keys = ON;")
        logger.debug(f"Conexão estabelecida com o banco: {DB_NAME}")
        return conexao
    except sqlite3.Error as e:
        logger.error(f"Erro ao conectar ao banco de dados ({DB_NAME}): {e}")
        return None

# ----------------------------------------------------------------------
# ENTIDADE PRODUTO
# ----------------------------------------------------------------------
def listar_produtos_com_imagens() -> List[Dict[str, Any]]:
    """
    Lista todos os produtos disponíveis no cardápio com caminho das imagens resolvido.
    Retorna uma lista de dicionários com os dados dos produtos.
    """
    from pathlib import Path
    from PIL import Image
    import io
    import base64
    
    conexao = conectar()
    if conexao is None:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_produto, foto_produto_caminho, nome, descricao, preco FROM produto")
        produtos = cursor.fetchall()
        
        # Resolve o caminho da imagem e retorna como base64 para exibição
        resultado = []
        raiz_projeto = Path(__file__).parent.parent
        pasta_imagens = raiz_projeto / "imagens"
        
        for p in produtos:
            id_produto, foto_caminho, nome, descricao, preco = p
            
            # Resolve o caminho da imagem
            imagem_base64 = None
            if foto_caminho:
                caminho_limpo = foto_caminho.lstrip("/\\")
                caminho_absoluto = raiz_projeto / caminho_limpo
                
                if not caminho_absoluto.exists():
                    nome_arquivo = Path(caminho_limpo).name
                    caminho_absoluto = pasta_imagens / nome_arquivo
                
                if caminho_absoluto.exists():
                    try:
                        # Abre e redimensiona a imagem
                        img = Image.open(caminho_absoluto)
                        img.thumbnail((100, 100), Image.Resampling.LANCZOS)
                        
                        # Converte para base64 para exibir no chat
                        buffer = io.BytesIO()
                        img.save(buffer, format="PNG")
                        imagem_base64 = base64.b64encode(buffer.getvalue()).decode()
                    except Exception as e:
                        logger.error(f"Erro ao processar imagem {nome}: {e}")
            
            resultado.append({
                "id_produto": id_produto,
                "nome": nome,
                "descricao": descricao,
                "preco": preco,
                "imagem_base64": imagem_base64,
                "foto_caminho": foto_caminho
            })
        
        logger.info(f"Consulta de produtos finalizada: {len(resultado)} produto(s) encontrado(s).")
        return resultado
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao listar produtos no banco de dados: {e}")
        return []
    finally:
        conexao.close()
        
# ----------------------------------------------------------------------
# FUNÇÕES DE ANALYTICS / RELATÓRIOS
# ----------------------------------------------------------------------
def obter_metricas_gerais_vendas() -> Dict[str, Any]:
    """
    Retorna métricas consolidadas:
    1. Total de quantidade de itens vendidos
    2. Faturamento total acumulado
    3. Ticket médio (Valor total / quantidade de pedidos)
    """
    conexao = conectar()
    if not conexao:
        return {"total_itens_vendidos": 0, "faturamento_total": 0.0, "ticket_medio": 0.0, "total_pedidos": 0}

    try:
        cursor = conexao.cursor()
        
        # Total de itens vendidos
        cursor.execute("SELECT COALESCE(SUM(quantidade), 0) FROM pedido_produto;")
        total_itens = cursor.fetchone()[0]

        # Estatísticas sobre a tabela pedido
        cursor.execute("""
            SELECT 
                COUNT(id_pedido) as total_pedidos,
                COALESCE(SUM(valor_total), 0) as faturamento_total,
                COALESCE(AVG(valor_total), 0) as valor_medio
            FROM pedido;
        """)
        row = cursor.fetchone()
        total_pedidos = row[0]
        faturamento_total = row[1]

        ticket_medio = (faturamento_total / total_pedidos) if total_pedidos > 0 else 0.0

        return {
            "total_itens_vendidos": total_itens,
            "faturamento_total": faturamento_total,
            "ticket_medio": ticket_medio,
            "total_pedidos": total_pedidos
        }
    except sqlite3.Error as e:
        logger.error(f"Erro ao obter métricas gerais de vendas: {e}")
        return {"total_itens_vendidos": 0, "faturamento_total": 0.0, "ticket_medio": 0.0, "total_pedidos": 0}
    finally:
        conexao.close()

def obter_historico_vendas_por_data() -> List[Dict[str, Any]]:
    """Retorna o histórico de valor total e tipo de pagamento dos pedidos por data."""
    conexao = conectar()
    if not conexao:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id_pedido, data_hora_pedido, valor_total, tipo_pagamento
            FROM pedido
            ORDER BY data_hora_pedido ASC;
        """)
        linhas = cursor.fetchall()
        return [
            {
                "id_pedido": r[0],
                "data_hora_pedido": r[1],
                "valor_total": r[2],
                "tipo_pagamento": r[3]
            }
            for r in linhas
        ]
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar histórico de vendas: {e}")
        return []
    finally:
        conexao.close()

def obter_vendas_por_produto() -> List[Dict[str, Any]]:
    """Retorna o valor total vendido e quantidade vendida agrupado por produto."""
    conexao = conectar()
    if not conexao:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT 
                p.nome AS produto,
                SUM(pp.quantidade) AS quantidade_total,
                SUM(pp.quantidade * pp.preco_unitario_momento) AS valor_total
            FROM pedido_produto pp
            JOIN produto p ON pp.id_produto = p.id_produto
            GROUP BY p.id_produto, p.nome
            ORDER BY quantidade_total DESC;
        """)
        linhas = cursor.fetchall()
        return [
            {
                "produto": r[0],
                "quantidade_total": r[1],
                "valor_total": r[2]
            }
            for r in linhas
        ]
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar vendas por produto: {e}")
        return []
    finally:
        conexao.close()


def obter_top_clientes(limit: int = 10) -> List[Dict[str, Any]]:
    """Retorna os clientes que mais gastaram/compraram no estabelecimento."""
    conexao = conectar()
    if not conexao:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT 
                c.id_cliente,
                c.nome_completo,
                c.cpf,
                COUNT(p.id_pedido) AS total_pedidos,
                COALESCE(SUM(p.valor_total), 0) AS total_gasto
            FROM cliente c
            INNER JOIN pedido p ON c.id_cliente = p.id_cliente
            GROUP BY c.id_cliente, c.nome_completo, c.cpf
            ORDER BY total_gasto DESC
            LIMIT ?;
        """, (limit,))
        linhas = cursor.fetchall()
        return [
            {
                "id_cliente": r[0],
                "nome_completo": r[1],
                "cpf": r[2],
                "total_pedidos": r[3],
                "total_gasto": r[4]
            }
            for r in linhas
        ]
    except sqlite3.Error as e:
        logger.error(f"Erro ao buscar top clientes: {e}")
        return []
    finally:
        conexao.close()

# ----------------------------------------------------------------------
# ENTIDADE CLIENTE & ENDEREÇO
# ----------------------------------------------------------------------
def verificar_cliente_existe(id_cliente: int) -> tuple:
    """
    Verifica se já existe um cliente cadastrado com o ID informado.
    Retorna: (bool, str) - (existe, mensagem_erro)
    """
    conexao = conectar()
    if conexao is None:
        msg_erro = "Não foi possível conectar ao banco para verificar o cliente."
        logger.error(msg_erro)
        return False, msg_erro

    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_cliente FROM cliente WHERE id_cliente = ?", (id_cliente,))
        resultado = cursor.fetchone()
        
        if resultado:
            return True, ""
        else:
            return False, f"Cliente com ID {id_cliente} não encontrado."
            
    except sqlite3.Error as e:
        msg_erro = f"Erro ao verificar cliente: {str(e)}"
        logger.error(msg_erro)
        return False, msg_erro
    finally:
        conexao.close()

# Essa função parte do princípio que os dados estão corretos, pois já foram validados antes de chamar a função. A validação é feita na função cadastrar_cliente_completo.
def inserir_cliente(
    cpf: str,
    nome_completo: str,
    data_nascimento: Optional[str] = None,
    email: Optional[str] = None,
    telefone: Optional[str] = None,
    sexo: Optional[str] = None,
    data_cadastro: Optional[str] = None
) -> Dict[str, Any]:
    """
    Insere um novo cliente no banco de dados SQLite.
    Se data_cadastro for omitida, utiliza a data/hora atual no formato ISO.
    """
    conn = conectar()
    if not conn:
        return {"status": "erro", "mensagem": "Falha na conexão com o banco de dados."}

    if not data_cadastro:
        data_cadastro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sql = """
        INSERT INTO cliente (cpf, nome_completo, data_nascimento, email, telefone, sexo, data_cadastro)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """

    try:
        cursor = conn.cursor()
        cursor.execute(sql, (cpf, nome_completo, data_nascimento, email, telefone, sexo, data_cadastro))
        conn.commit()

        id_gerado = cursor.lastrowid
        logger.info(f"Cliente '{nome_completo}' (ID: {id_gerado}) cadastrado com sucesso em {data_cadastro}.")

        return {
            "status": "sucesso",
            "id_cliente": id_gerado,
            "data_cadastro": data_cadastro,
            "mensagem": "Cliente inserido com sucesso."
        }

    except sqlite3.IntegrityError as e:
        conn.rollback()
        logger.warning(f"Erro de integridade ao inserir cliente (CPF: {cpf}): {e}")
        return {
            "status": "erro",
            "mensagem": f"Não foi possível cadastrar o cliente. O CPF {cpf} já está registrado."
        }

    except sqlite3.Error as e:
        conn.rollback()
        logger.error(f"Erro ao inserir cliente no banco de dados: {e}")
        return {
            "status": "erro",
            "mensagem": f"Erro interno no banco de dados: {str(e)}"
        }

    finally:
        conn.close()


def inserir_endereco(id_cliente: int, rua: str, numero: int, bairro: str, cidade: str, cep: str, complemento: Optional[str] = None) -> bool:
    """Cadastra o endereço vinculado a um cliente (Relação 1:1)."""
    status_cliente_existente, msg_erro_existencia_cliente = verificar_cliente_existe(id_cliente)
    if not status_cliente_existente:
        logger.warning(f"{msg_erro_existencia_cliente} Endereço não pode ser cadastrado.")
        return False

    conexao = conectar()
    if conexao is None:
        logger.error("Não foi possível conectar ao banco de dados.")
        return False

    try:
        with conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                INSERT INTO endereco (id_cliente, rua, numero, bairro, cidade, cep, complemento)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_cliente, rua, numero, bairro, cidade, cep, complemento))
            logger.info(f"Endereço vinculado com sucesso ao cliente ID {id_cliente}.")
            return True
    except sqlite3.Error as e:
        logger.error(f"Erro ao inserir endereço: {e}")
        return False
    finally:
        conexao.close()

# Cadastro completo do pedido(validação de dados), antes de inserir no BD
def cadastrar_cliente_completo(
    cpf: str,
    nome_completo: str,
    data_nascimento: str = None,
    email: str = None,
    telefone: str = None,
    sexo: str = None,
    cep: str = None,
    numero: str = None,
    complemento: str = None
) -> dict:
    """Valida todos os dados do cliente e cadastra suas informações pessoais e endereço."""
    erros = []

    # Validações
    valido, msg_erro = validar_nome(nome_completo)
    if not valido: 
        erros.append(msg_erro)

    valido, msg_erro = validar_cpf(cpf)
    if not valido: 
        erros.append(msg_erro)

    if data_nascimento:
        valido, msg_erro = validar_data_nascimento(data_nascimento)
        if not valido: 
            erros.append(msg_erro)

    if telefone:
        valido, msg_erro = validar_telefone(telefone)
        if not valido: 
            erros.append(msg_erro)

    if sexo:
        valido, msg_erro = validar_sexo(sexo)
        if not valido: 
            erros.append(msg_erro)
        
    # Validação de email
    if email:
        valido, msg_erro = validar_email_completo(email)
        if not valido:
            erros.append(msg_erro)
    
    # Validação de endereço (CEP e número)
    endereco_encontrado = None
    if cep:
        resultado_cep = validar_e_buscar_cep(cep)
        
        # Verifica se o retorno é um dicionário (sucesso) ou tupla (erro)
        if isinstance(resultado_cep, dict):
            endereco_encontrado = resultado_cep
            if not numero:
                erros.append("O número do endereço é obrigatório quando o CEP é fornecido.")
        else:
            # É uma tupla (False, mensagem_erro)
            _, msg_erro = resultado_cep
            erros.append(msg_erro)

    if erros:
        return {
            "status": "erro_validacao",
            "mensagem": "Não foi possível concluir o cadastro devido a dados incorretos ou ausentes.",
            "erros": erros
        }

    try:
        res_cliente = inserir_cliente(
            cpf=cpf,
            nome_completo=nome_completo,
            data_nascimento=data_nascimento,
            email=email,
            telefone=telefone,
            sexo=sexo
        )

        if res_cliente.get("status") != "sucesso":
            return res_cliente

        id_cliente = res_cliente.get("id_cliente")
        retorno = {
            "status": "sucesso",
            "id_cliente": id_cliente,
            "data_cadastro": res_cliente.get("data_cadastro"),
            "mensagem": "Cliente cadastrado com sucesso!"
        }

        if id_cliente and endereco_encontrado:
            rua = endereco_encontrado.get("logradouro", "")
            bairro = endereco_encontrado.get("bairro", "")
            cidade = endereco_encontrado.get("localidade", "")

            sucesso_endereco = inserir_endereco(
                id_cliente=id_cliente,
                rua=rua,
                numero=int(numero),
                bairro=bairro,
                cidade=cidade,
                cep=cep,
                complemento=complemento
            )

            if sucesso_endereco:
                retorno["endereco"] = {
                    "rua": rua, 
                    "numero": numero, 
                    "bairro": bairro,
                    "cidade": cidade, 
                    "cep": cep, 
                    "complemento": complemento
                }
                retorno["mensagem"] += " Endereço vinculado com sucesso!"
            else:
                retorno["aviso_endereco"] = "Cliente cadastrado, mas ocorreu uma falha ao gravar o endereço."

        return retorno

    except Exception as e:
        logger.error(f"Erro no cadastro completo do cliente: {e}")
        return {
            "status": "erro_banco",
            "mensagem": f"Erro interno ao salvar no banco de dados: {str(e)}"
        }

# Lista todos os clientes que possuem endereços vinculados (INNER JOIN).
def listar_todos_clientes_enderecos() -> List[Dict[str, Any]]:
    """Lista todos os clientes que possuem endereço cadastrado (INNER JOIN)."""
    conexao = conectar()
    if conexao is None:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT 
                c.id_cliente,
                c.cpf,
                c.nome_completo,
                c.data_nascimento,
                c.email,
                c.telefone,
                c.sexo,
                c.data_cadastro,
                e.id_endereco,
                e.rua,
                e.numero,
                e.bairro,
                e.cidade,
                e.cep,
                e.complemento
            FROM cliente c
            INNER JOIN endereco e ON c.id_cliente = e.id_cliente
            ORDER BY c.id_cliente DESC
        """)
        
        linhas = cursor.fetchall()
        
        clientes = []
        for row in linhas:
            cliente = {
                "id_cliente": row[0],
                "cpf": row[1],
                "nome_completo": row[2],
                "data_nascimento": row[3],
                "email": row[4],
                "telefone": row[5],
                "sexo": row[6],
                "data_cadastro": row[7],
                "endereco": {
                    "id_endereco": row[8],
                    "rua": row[9],
                    "numero": row[10],
                    "bairro": row[11],
                    "cidade": row[12],
                    "cep": row[13],
                    "complemento": row[14]
                }
            }
            clientes.append(cliente)
        
        logger.info(f"Consulta executada com sucesso: {len(clientes)} cliente(s) com endereço encontrado(s).")
        return clientes
        
    except sqlite3.Error as e:
        logger.error(f"Erro ao listar clientes com endereços: {e}")
        return []
    finally:
        conexao.close()
        
  

def listar_clientes() -> List[Dict[str, Any]]:
    """Lista todos os clientes cadastrados incluindo a data_cadastro."""
    conexao = conectar()
    if conexao is None:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_cliente, nome_completo, cpf, telefone, data_cadastro FROM cliente")
        linhas = cursor.fetchall()
        clientes = [
            {
                "id_cliente": c[0],
                "nome_completo": c[1],
                "cpf": c[2],
                "telefone": c[3],
                "data_cadastro": c[4]
            }
            for c in linhas
        ]
        logger.info(f"Consulta executada com sucesso: {len(clientes)} cliente(s) encontrado(s).")
        return clientes
    except sqlite3.Error as e:
        logger.error(f"Erro ao listar clientes: {e}")
        return []
    finally:
        conexao.close()


# ----------------------------------------------------------------------
# ENTIDADE PRODUTO
# ----------------------------------------------------------------------
def listar_produtos() -> List[tuple]:
    """Lista todos os produtos disponíveis no cardápio."""
    conexao = conectar()
    if conexao is None:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("SELECT id_produto, foto_produto_caminho, nome, descricao, preco FROM produto")
        produtos = cursor.fetchall()
        logger.info(f"Consulta de produtos finalizada: {len(produtos)} produto(s) encontrado(s).")
        return produtos
    except sqlite3.Error as e:
        logger.error(f"Erro ao listar produtos no banco de dados: {e}")
        return []
    finally:
        conexao.close()
from typing import List, Dict, Any

# ======================================================================
# ENTIDADE PEDIDO
# ======================================================================

def cadastrar_pedido_completo(
    id_cliente: int,
    valor_total: float,
    tipo_pagamento: str,
    itens: List[Dict[str, Any]],  # ← Tipo específico para o Gemini
) -> dict:
    """
    Cadastra um pedido completo com validação de dados.
    
    Args:
        id_cliente: ID numérico do cliente no banco (ex: 1)
        valor_total: Valor total do pedido em reais (ex: 59.80)
        tipo_pagamento: Forma de pagamento (ex: 'pix', 'cartao de credito', 'dinheiro')
        itens: Lista de dicionários onde cada dicionário representa um item do pedido.
            Cada item deve ter:
            - id_produto: int - ID do produto no banco (ex: 1, 13, 25)
            - quantidade: int - Quantidade solicitada (ex: 1, 2, 3)
            Exemplo: [{"id_produto": 1, "quantidade": 2}]
    
    Agrupa automaticamente itens duplicados.
    
    ⚠️ REGRA DE TRANSAÇÃO ATÔMICA:
    - Todas as validações são feitas ANTES de chamar criar_pedido
    - Se QUALQUER validação falhar, NENHUM dado é alterado
    - criar_pedido já tem rollback automático em caso de erro
    
    Returns:
        dict com status da operação
    """
    erros = []
    itens_com_preco = []
    valor_calculado = 0.0
    produtos_nao_encontrados = []

    # ============================================================
    # 1. VALIDAÇÕES (TUDO ANTES DE QUALQUER INSERÇÃO)
    # ============================================================
    
    # 1.1 Verifica se o cliente existe
    status_existencia_cli, msg_erro_cli_inexistente = verificar_cliente_existe(id_cliente)
    if not status_existencia_cli:
        erros.append(msg_erro_cli_inexistente)
    
    # 1.2 Valida e enriquece a lista de itens com preços do banco
    if not itens or not isinstance(itens, list):
        erros.append("A lista de itens do pedido não pode estar vazia.")
    else:
        try:
            # Dicionário para AGRUPAR itens por id_produto
            itens_agrupados = {}
            
            for idx, item in enumerate(itens):
                id_produto = item.get("id_produto")
                quantidade = item.get("quantidade", 1)
                
                # Validação: ID do produto
                if not id_produto:
                    erros.append(f"Item #{idx+1}: id_produto é obrigatório")
                    continue
                
                if not isinstance(id_produto, (int, str)) or str(id_produto).strip() == '':
                    erros.append(f"Item #{idx+1}: id_produto inválido ({id_produto})")
                    continue
                
                # Validação: Quantidade
                if not isinstance(quantidade, (int, float)) or quantidade <= 0:
                    erros.append(f"Item #{idx+1}: quantidade inválida ({quantidade})")
                    continue
                
                # AGRUPA: Se o produto já existe, soma a quantidade
                if id_produto in itens_agrupados:
                    itens_agrupados[id_produto]["quantidade"] += quantidade
                    logger.warning(f"⚠️ Produto {id_produto} duplicado, quantidades somadas: +{quantidade}")
                else:
                    itens_agrupados[id_produto] = {
                        "id_produto": id_produto,
                        "quantidade": quantidade
                    }
            
            # Processa os itens agrupados
            for id_produto, item_agrupado in itens_agrupados.items():
                quantidade = item_agrupado["quantidade"]
                
                # BUSCA O PREÇO NO BANCO
                preco_unitario = buscar_preco_produto(id_produto)
                
                if preco_unitario is None:
                    produtos_nao_encontrados.append(str(id_produto))
                    continue
                
                # Validação: Preço deve ser positivo
                if not isinstance(preco_unitario, (int, float)) or preco_unitario < 0:
                    erros.append(f"Produto {id_produto}: preço inválido ({preco_unitario})")
                    continue
                
                # Cria o item enriquecido
                item_com_preco = {
                    "id_produto": id_produto,
                    "quantidade": quantidade,
                    "preco_unitario_momento": preco_unitario
                }
                itens_com_preco.append(item_com_preco)
                
                # Acumula o valor calculado
                subtotal = quantidade * preco_unitario
                valor_calculado += subtotal
                
                logger.debug(
                    f"📝 Produto {id_produto} x{quantidade} = R$ {preco_unitario:.2f} cada "
                    f"(subtotal: R$ {subtotal:.2f})"
                )
            
            # Verifica produtos não encontrados
            if produtos_nao_encontrados:
                erros.append(
                    f"Produto(s) não encontrado(s) ou inativo(s): "
                    f"{', '.join(produtos_nao_encontrados)}"
                )
            
            # Verifica se há itens válidos
            if not itens_com_preco and not erros:
                erros.append("Nenhum item válido foi encontrado para o pedido")
            
            # Compara valor informado com calculado (com arredondamento de precisão de centavos)
            if valor_total > 0 and itens_com_preco:
                valor_calculado = round(valor_calculado, 2)
                valor_total = round(float(valor_total), 2)
                diferenca = abs(valor_calculado - valor_total)
                
                # Margem de tolerância para pequenas divergências de float (5 centavos)
                if diferenca > 0.05:
                    erros.append(
                        f"Valor total informado (R$ {valor_total:.2f}) não confere "
                        f"com o valor calculado (R$ {valor_calculado:.2f}). "
                        f"Diferença: R$ {diferenca:.2f}"
                    )
                    
        except Exception as e:
            erros.append(f"Erro ao processar itens: {str(e)}")
            logger.error(f"❌ Erro ao processar itens: {str(e)}", exc_info=True)
    
    # 1.3 Valida a forma de pagamento
    pagamento_valido, msg_erro_pagamento = validar_pagamento(tipo_pagamento)
    if not pagamento_valido:
        erros.append(msg_erro_pagamento)

    # ============================================================
    # 2. SE HOUVER ERROS, RETORNA SEM ALTERAR NADA
    # ============================================================
    
    if erros:
        logger.error(f"❌ Erros de validação: {erros}")
        return {
            "status": "erro_validacao",
            "mensagem": "Não foi possível concluir o cadastro do pedido devido a dados incorretos ou ausentes.",
            "erros": erros,
            "itens_validos": len(itens_com_preco),
            "total_itens": len(itens) if itens else 0
        }

    # ============================================================
    # 3. TUDO VÁLIDO - CHAMA criar_pedido (COM TRANSAÇÃO ATÔMICA)
    # ============================================================
    
    data_hora_pedido_agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # CHAMA criar_pedido - Ela já tem rollback automático
    resultado = criar_pedido(
        id_cliente=id_cliente,
        valor_total=valor_calculado,
        tipo_pagamento=tipo_pagamento,
        itens=itens_com_preco,
        data_hora_pedido=data_hora_pedido_agora
    )
    
    # ============================================================
    # 4. TRATA O RETORNO DE criar_pedido
    # ============================================================
    
    # Se retornou None (erro de banco ou rollback)
    if resultado is None:
        logger.error("❌ Erro ao criar pedido no banco")
        return {
            "status": "erro_banco",
            "mensagem": "Erro interno ao salvar o pedido no banco de dados. Nenhum dado foi alterado.",
            "rollback_executado": True
        }
    
    # Se retornou um ID (sucesso!)
    id_pedido = resultado
    
    logger.info(f"✅ Pedido #{id_pedido} criado com sucesso! Valor: R$ {valor_calculado:.2f}")
    return {
        "status": "sucesso",
        "id_pedido": id_pedido,
        "mensagem": f"Pedido #{id_pedido} cadastrado com sucesso!",
        "valor_total": valor_calculado,
        "valor_informado": valor_total,
        "quantidade_itens": len(itens_com_preco),
        "itens": itens_com_preco
    }
    


# ============================================================
# FUNÇÃO AUXILIAR - BUSCAR PREÇO
# ============================================================

def buscar_preco_produto(id_produto: int) -> Optional[float]:
    """
    Busca o preço atual do produto no banco de dados.
    
    Args:
        id_produto: ID do produto
        
    Returns:
        float: Preço unitário do produto ou None se não encontrado
    """
    conexao = None
    cursor = None
    
    try:
        # 1. Estabelece conexão com o banco
        conexao = conectar()
        if conexao is None:
            logger.error("❌ Falha na conexão com o banco de dados")
            return None
        
        # 2. Cria o cursor a partir da conexão
        cursor = conexao.cursor()
        
        # 3. Query SQL para buscar o preço do produto
        # SQLITE usa '?' como placeholder
        sql = """
            SELECT preco
            FROM produto 
            WHERE id_produto = ?
        """
        
        cursor.execute(sql, (id_produto,))
        resultado = cursor.fetchone()
        
        if resultado:
            preco = float(resultado[0])
            logger.debug(f"📦 Produto #{id_produto} - Preço: R$ {preco:.2f}")
            return preco
        else:
            logger.warning(f"⚠️ Produto #{id_produto} não encontrado")
            return None
            
    except Exception as e:
        logger.error(f"❌ Erro ao buscar preço do produto {id_produto}: {str(e)}")
        return None
    
    finally:
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()
            
# ----------------------------------------------------------------------
# ENTIDADE PEDIDOS - CRIAÇÃO
# ----------------------------------------------------------------------
def criar_pedido(
    id_cliente: int, 
    valor_total: float, 
    tipo_pagamento: str, 
    itens: List[Dict[str, Any]],
    data_hora_pedido: Optional[str] = None
) -> Optional[int]:
    """
    Cria um pedido e insere seus itens na tabela 'pedido_produto'.
    
    ⚠️ REGRA DE TRANSAÇÃO ATÔMICA:
    - Todos os itens devem ser inseridos com sucesso
    - Se QUALQUER item falhar, TODA a operação é desfeita (rollback)
    - Nada é inserido parcialmente
    
    Args:
        id_cliente: ID do cliente
        valor_total: Valor total do pedido
        tipo_pagamento: Forma de pagamento
        itens: Lista de dicionários com os itens do pedido
        data_hora_pedido: Data/hora do pedido (opcional)
    
    Returns:
        int: ID do pedido criado ou None em caso de erro
    """
    conexao = None
    cursor = None
    id_pedido = None
    
    try:
        # 1. Estabelece conexão
        conexao = conectar()
        if conexao is None:
            logger.error("❌ Falha na conexão com o banco de dados")
            return None
        
        # 2. Define data/hora
        if not data_hora_pedido:
            data_hora_pedido = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 3. Validações básicas
        if not itens:
            logger.error("❌ Lista de itens vazia")
            return None
        
        # 4. Inicia transação
        cursor = conexao.cursor()
        
        # 5. Insere o pedido
        sql_pedido = """
            INSERT INTO pedido (
                id_cliente, 
                data_hora_pedido, 
                valor_total, 
                tipo_pagamento
            )
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(sql_pedido, (id_cliente, data_hora_pedido, valor_total, tipo_pagamento))
        
        # 6. Obtém o ID do pedido gerado
        id_pedido = cursor.lastrowid
        
        if not id_pedido:
            logger.error("❌ Falha ao obter ID do pedido")
            conexao.rollback()
            return None
        
        logger.info(f"📝 Pedido #{id_pedido} criado, processando {len(itens)} item(ns)...")
        
        # 7. Insere todos os itens (com validação individual)
        sql_item = """
            INSERT INTO pedido_produto (
                id_pedido,
                id_produto,
                quantidade,
                preco_unitario_momento
            ) VALUES (?, ?, ?, ?)
        """
        
        erros_itens = []
        itens_processados = 0
        
        for idx, item in enumerate(itens):
            try:
                # Extrai os dados do item
                if hasattr(item, "model_dump"):
                    d = item.model_dump()
                elif hasattr(item, "dict"):
                    d = item.dict()
                elif isinstance(item, dict):
                    d = item
                else:
                    d = dict(item)
                
                # Obtém os valores
                id_produto = d.get("id_produto")
                quantidade = d.get("quantidade", 1)
                preco_unitario = d.get("preco_unitario_momento", 0.0)
                
                # VALIDAÇÃO INDIVIDUAL (falha aqui = rollback total)
                if not id_produto:
                    erros_itens.append(f"Item #{idx+1}: id_produto é obrigatório")
                    continue
                
                if not isinstance(id_produto, (int, str)) or str(id_produto).strip() == '':
                    erros_itens.append(f"Item #{idx+1}: id_produto inválido ({id_produto})")
                    continue
                
                if not isinstance(quantidade, (int, float)) or quantidade <= 0:
                    erros_itens.append(f"Item #{idx+1} (produto {id_produto}): quantidade inválida ({quantidade})")
                    continue
                
                if not isinstance(preco_unitario, (int, float)) or preco_unitario < 0:
                    erros_itens.append(f"Item #{idx+1} (produto {id_produto}): preço inválido ({preco_unitario})")
                    continue
                
                # TENTA INSERIR O ITEM
                cursor.execute(sql_item, (id_pedido, id_produto, quantidade, preco_unitario))
                itens_processados += 1
                logger.debug(f"   ✅ Item #{idx+1}: Produto {id_produto} x{quantidade} = R$ {preco_unitario:.2f}")
                
            except sqlite3.IntegrityError as e:
                # ERRO DE INTEGRIDADE (ex: duplicata) = ROLLBACK TOTAL
                erros_itens.append(f"Item #{idx+1} (produto {id_produto}): violação de integridade - {str(e)}")
                logger.error(f"   ❌ Item #{idx+1} FALHOU: {str(e)}")
                break  # Sai do loop imediatamente
                
            except Exception as e:
                # QUALQUER OUTRO ERRO = ROLLBACK TOTAL
                erros_itens.append(f"Item #{idx+1} (produto {id_produto}): erro inesperado - {str(e)}")
                logger.error(f"   ❌ Item #{idx+1} FALHOU: {str(e)}")
                break  # Sai do loop imediatamente
        
        # 8. Verifica se houve algum erro
        if erros_itens:
            # ALGUM ITEM FALHOU - DESFAZ TUDO (ROLLBACK)
            logger.error(f"❌ {len(erros_itens)} erro(s) encontrado(s) ao processar itens:")
            for erro in erros_itens:
                logger.error(f"   - {erro}")
            
            logger.warning(f"🔄 Desfazendo toda a operação (rollback)...")
            conexao.rollback()
            
            return None
        
        # 9. SUCESSO: Confirma a transação
        conexao.commit()
        
        logger.info(f"✅ Pedido #{id_pedido} criado com sucesso!")
        logger.info(f"   Cliente: {id_cliente}")
        logger.info(f"   Valor total: R$ {valor_total:.2f}")
        logger.info(f"   Itens inseridos: {itens_processados}/{len(itens)}")
        return id_pedido
        
    except sqlite3.IntegrityError as e:
        logger.error(f"❌ Erro de integridade ao criar pedido: {str(e)}")
        if conexao:
            conexao.rollback()
            logger.warning("🔄 Rollback executado - nenhum dado foi alterado")
        return None
        
    except Exception as e:
        logger.error(f"❌ Erro ao criar o pedido: {str(e)}")
        if conexao:
            conexao.rollback()
            logger.warning("🔄 Rollback executado - nenhum dado foi alterado")
        return None
    
    finally:
        if cursor:
            cursor.close()
        if conexao:
            conexao.close()
     
     
# ----------------------------------------------------------------------
# ENTIDADE PEDIDOS - LISTAGEM
# ----------------------------------------------------------------------
def listar_pedidos() -> List[Dict[str, Any]]:
    """
    Consulta o banco de dados e retorna todos os pedidos com seus respectivos itens.
    """
    conexao = conectar()
    if conexao is None:
        return []

    try:
        cursor = conexao.cursor()
        query = """
            SELECT 
                p.id_pedido,
                p.id_cliente,
                p.data_hora_pedido,
                p.valor_total,
                p.tipo_pagamento,
                pr.nome AS nome_produto,
                pp.quantidade,
                pp.preco_unitario_momento
            FROM pedido p
            INNER JOIN pedido_produto pp ON p.id_pedido = pp.id_pedido
            INNER JOIN produto pr ON pp.id_produto = pr.id_produto
            ORDER BY p.id_pedido DESC;
        """
        
        cursor.execute(query)
        linhas = cursor.fetchall()

        pedidos_dict = {}

        for linha in linhas:
            id_ped, id_cli, dt_pedido, val_total, pagamento, prod_nome, qtd, preco_unit = linha

            if id_ped not in pedidos_dict:
                pedidos_dict[id_ped] = {
                    "id_pedido": id_ped,
                    "id_cliente": id_cli,
                    "data_hora_pedido": dt_pedido,
                    "valor_total": float(val_total),
                    "tipo_pagamento": pagamento,
                    "itens": []
                }

            pedidos_dict[id_ped]["itens"].append({
                "produto": prod_nome,
                "quantidade": qtd,
                "preco_unitario": float(preco_unit),
                "subtotal": float(qtd * preco_unit)
            })

        lista_pedidos = list(pedidos_dict.values())
        logger.info(f"Consulta de pedidos finalizada: {len(lista_pedidos)} pedido(s) encontrado(s).")
        return lista_pedidos

    except sqlite3.Error as e:
        logger.error(f"Erro ao listar pedidos do banco: {e}")
        return []
    finally:
        conexao.close()

# ----------------------------------------------------------------------
# ENTIDADE FEEDBACK
# ----------------------------------------------------------------------
def registrar_feedback(
    id_pedido: int,
    nota: int,
    comentario: Optional[str] = None,
    sentimento_associado: Optional[str] = None,
    data_hora_feedback: Optional[str] = None
) -> Optional[int]:
    """Cadastra a avaliação de um pedido concluído."""
    conexao = conectar()
    if conexao is None:
        return None

    if not data_hora_feedback:
        data_hora_feedback = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with conexao:
            cursor = conexao.cursor()
            cursor.execute("""
                INSERT INTO feedback (id_pedido, nota, comentario, data_hora_feedback, sentimento_associado)
                VALUES (?, ?, ?, ?, ?)
            """, (id_pedido, nota, comentario, data_hora_feedback, sentimento_associado))
            
            id_feedback = cursor.lastrowid
            logger.info(f"Feedback #{id_feedback} registrado para o pedido #{id_pedido} com nota {nota}.")
            return id_feedback
    except sqlite3.IntegrityError as e:
        logger.warning(f"O pedido #{id_pedido} já possui um feedback cadastrado: {e}")
        return None
    except sqlite3.Error as e:
        logger.error(f"Erro ao registrar feedback: {e}")
        return None
    finally:
        conexao.close()


def listar_feedbacks() -> List[Dict[str, Any]]:
    """Retorna a lista de feedbacks gravados na base de dados."""
    conexao = conectar()
    if conexao is None:
        return []

    try:
        cursor = conexao.cursor()
        cursor.execute("""
            SELECT id_feedback, id_pedido, nota, comentario, data_hora_feedback, sentimento_associado
            FROM feedback
            ORDER BY data_hora_feedback DESC
        """)
        linhas = cursor.fetchall()
        feedbacks = [
            {
                "id_feedback": f[0],
                "id_pedido": f[1],
                "nota": f[2],
                "comentario": f[3],
                "data_hora_feedback": f[4],
                "sentimento_associado": f[5]
            }
            for f in linhas
        ]
        logger.info(f"Consulta de feedbacks executada: {len(feedbacks)} registro(s) encontrado(s).")
        return feedbacks
    except sqlite3.Error as e:
        logger.error(f"Erro ao listar feedbacks: {e}")
        return []
    finally:
        conexao.close()