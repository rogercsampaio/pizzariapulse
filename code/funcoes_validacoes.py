# Funções responsáveis por validações de dados, como CPF, telefone, e-mail, etc.
# Será usada antes dos dados serem inseridos no banco de dados para garantir a integridade e validade das informações.
import re
from datetime import datetime
import requests
from validate_docbr import CPF
import phonenumbers
from phonenumbers import NumberParseException
from loguru import logger
from email_validator import validate_email, EmailNotValidError
from deep_translator import GoogleTranslator


def validar_cpf(cpf_validar_txt: str) -> bool:
    cpf_validar_txt_normalizado = re.sub(r"\D", "", cpf_validar_txt)  # Remove caracteres não numéricos
    cpf = CPF()
    # Valida se o CPF é matematicamente válido
    if cpf.validate(cpf_validar_txt_normalizado):
        logger.info(f"CPF '{cpf_validar_txt_normalizado}' validado com sucesso.")
        return True,f""
    else:
        logger.warning(f"CPF inválido: '{cpf_validar_txt_normalizado}'")
        return False,f"CPF inválido: '{cpf_validar_txt_normalizado}'"



# Formato esperado: DDD + NUMERO 61998124512. O +55 é adicionado caso nao tenha.

def validar_telefone(numero_str: str) -> tuple:
    """
    Valida número de telefone no formato brasileiro.
    
    Args:
        numero_str: String com o número (ex: (11)99812-1110, 11998121110, +5511998121110)
    
    Returns:
        tuple: (bool, str) - (válido, mensagem_erro)
    """
    # Remove caracteres não numéricos
    telefone_normalizado = re.sub(r"\D", "", numero_str)
    
    # Verifica se tem pelo menos 10 dígitos (DDD + número)
    if len(telefone_normalizado) < 10:
        logger.warning(f"Telefone muito curto: '{numero_str}'")
        return False, f"Telefone inválido: deve ter pelo menos 10 dígitos (DDD + número). Ex: 11998121110"
    
    # Verifica se o número já tem o código do país (+55)
    # Se o número normalizado tiver 13 dígitos, começa com 55 (código do Brasil)
    if len(telefone_normalizado) == 13 and telefone_normalizado.startswith('55'):
        numero_completo = f"+{telefone_normalizado}"
    else:
        # Adiciona +55 para o Brasil
        numero_completo = f"+55{telefone_normalizado}"
    
    try:
        parsed_number = phonenumbers.parse(numero_completo, None)
        
        if phonenumbers.is_valid_number(parsed_number):
            logger.info(f"Telefone '{numero_str}' validado com sucesso.")
            return True, ""
        else:
            logger.warning(f"Telefone inválido: '{numero_str}'")
            return False, f"Telefone inválido: '{numero_str}'"
            
    except NumberParseException as e:
        logger.warning(f"Formato de número de telefone inválido: '{numero_str}' - {str(e)}")
        return False, f"Formato de número de telefone inválido: '{numero_str}'. Use o formato correto, ex: (11)99812-1110"



def validar_data_nascimento(data_str: str) -> bool:
    try:
        # Tenta converter a string no formato DD/MM/AAAA
        data_nasc = datetime.strptime(data_str, "%d/%m/%Y")

        # Valida se não está no futuro
        if data_nasc > datetime.now():
            logger.warning(f"Data de nascimento no futuro: '{data_str}'")
            return False, f"Data de nascimento no futuro: '{data_str}'"

        # Valida uma idade máxima razoável (ex: 120 anos)
        if datetime.now().year - data_nasc.year > 120:
            logger.warning(f"Data de nascimento excede o limite razoável (120 anos): '{data_str}'")
            return False, f"Data de nascimento excede o limite razoável (120 anos): '{data_str}'"

        logger.info(f"Data de nascimento '{data_str}' validada com sucesso.")
        return True, f""
    except ValueError:
        logger.warning(f"Formato ou valor de data de nascimento inválido: '{data_str}' (Esperado: DD/MM/AAAA)")
        return False, f"Formato ou valor de data de nascimento inválido: '{data_str}' (Esperado: DD/MM/AAAA)"


def validar_e_buscar_cep(cep):
    """
    Valida o formato do CEP e busca suas informações completas na API do ViaCEP.
    
    Retorna:
        - dict: Dicionário com os dados do endereço se for válido e existir
        - tuple: (False, mensagem_erro) se houver erro ou CEP não encontrado
    """
    # Remove caracteres não numéricos (como hífens ou pontos)
    cep_limpo = re.sub(r"\D", "", str(cep))

    # 1. Validação básica de tamanho (deve ter exatamente 8 dígitos)
    if len(cep_limpo) != 8:
        logger.warning(f"CEP '{cep}' é inválido. Deve conter exatamente 8 dígitos.")
        return False, f"CEP inválido: '{cep}' deve conter exatamente 8 dígitos."

    # 2. Consulta à API do ViaCEP para validar existência e buscar os dados
    url = f"https://viacep.com.br/ws/{cep_limpo}/json/"

    try:
        resposta = requests.get(url, timeout=5)
        if resposta.status_code == 200:
            dados = resposta.json()

            # O ViaCEP retorna a chave 'erro' quando o CEP tem 8 dígitos mas não existe
            if "erro" in dados:
                logger.warning(f"O CEP '{cep_limpo}' não foi encontrado na base do ViaCEP.")
                return False, f"O CEP '{cep_limpo}' não foi encontrado. Verifique e tente novamente."

            logger.info(f"CEP '{dados.get('cep')}' validado e encontrado com sucesso.")
            
            # Retorna o dicionário completo com todas as informações do endereço
            return {
                "cep": dados.get("cep"),
                "logradouro": dados.get("logradouro"),
                "complemento": dados.get("complemento"),
                "bairro": dados.get("bairro"),
                "localidade": dados.get("localidade"),
                "uf": dados.get("uf"),
                "ibge": dados.get("ibge"),
                "ddd": dados.get("ddd")
            }
        else:
            logger.error(f"Erro ao acessar o serviço ViaCEP. Status Code: {resposta.status_code}")
            return False, f"Erro ao acessar o serviço ViaCEP. Status Code: {resposta.status_code}"
            
    except requests.RequestException as e:
        logger.error(f"Erro de conexão ao buscar o CEP '{cep_limpo}': {e}")
        return False, f"Erro de conexão ao buscar o CEP '{cep_limpo}'. Tente novamente mais tarde."
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar o CEP '{cep_limpo}': {e}")
        return False, f"Erro inesperado ao buscar o CEP: {str(e)}"


def validar_nome(nome) -> bool:
    """
    Valida se uma string representa um nome completo de pessoa válido.
    """
    if not isinstance(nome, str):
        logger.warning("O nome fornecido não é do tipo texto/string.")
        return False, "O nome fornecido não é do tipo texto/string."

    # Remove espaços excedentes nas extremidades
    nome_tratado = nome.strip()

    if not nome_tratado:
        logger.warning("O campo de nome está vazio.")
        return False, "O campo de nome está vazio."

    # Normaliza múltiplos espaços internos para apenas um espaço entre as palavras
    nome_tratado = re.sub(r'\s+', ' ', nome_tratado)

    # Divide o nome em palavras individuais para análise de estrutura
    partes = nome_tratado.split(' ')

    # Um nome de pessoa válido deve conter pelo menos duas partes (nome e sobrenome)
    if len(partes) < 2:
        logger.warning(f"Nome incompleto: '{nome_tratado}'. É necessário informar nome e sobrenome.")
        return False, f"Nome incompleto: '{nome_tratado}'. É necessário informar nome e sobrenome."

    # Verifica o comprimento mínimo
    if len(nome_tratado) < 3:
        logger.warning(f"Nome muito curto: '{nome_tratado}'")
        return False, f"Nome muito curto: '{nome_tratado}'"

    # Expressão Regular abrangente para nomes em português
    padrao_nome = re.compile(r"^[A-Za-zÀ-ÖØ-öø-ÿ]+([ '-][A-Za-zÀ-ÖØ-öø-ÿ]+)*$")

    if not padrao_nome.match(nome_tratado):
        logger.warning(f"Nome contém caracteres ou símbolos inválidos: '{nome_tratado}'")
        return False, f"Nome contém caracteres ou símbolos inválidos: '{nome_tratado}'"

    # Validação adicional contra padrões óbvios de testes ou entradas falsas
    for parte in partes:
        if len(parte) < 2 and parte.lower() not in ['de', 'da', 'do', 'das', 'dos', 'e']:
            logger.warning(f"A palavra '{parte}' no nome '{nome_tratado}' é muito curta.")
            return False, f"A palavra '{parte}' no nome '{nome_tratado}' é muito curta."
            
        # Evita sequências de mesma letra repetidas mais de 3 vezes seguidas
        if re.search(r'(.)\1{3,}', parte.lower()):
            logger.warning(f"O nome '{nome_tratado}' contém repetições excessivas de caracteres.")
            return False, f"O nome '{nome_tratado}' contém repetições excessivas de caracteres."

    logger.info(f"Nome '{nome_tratado}' validado com sucesso.")
    return True, f""


def validar_sexo(sexo) -> bool:
    """
    Valida se o sexo informado é estritamente 'masculino' ou 'feminino'.
    """
    if not isinstance(sexo, str):
        logger.warning("O valor informado para sexo não é do tipo texto.")
        return False, "O valor informado para sexo não é do tipo texto."

    sexo_normalizado = sexo.strip().lower()

    opcoes_validas = {
        "masculino": "Masculino",
        "feminino": "Feminino"
    }

    if sexo_normalizado in opcoes_validas:
        logger.info(f"Sexo '{opcoes_validas[sexo_normalizado]}' validado com sucesso.")
        return True, f""
    else:
        logger.warning(f"Opção de sexo inválida: '{sexo}'. Deve ser 'Masculino' ou 'Feminino'.")
        return False, f"Opção de sexo inválida: '{sexo}'. Deve ser 'Masculino' ou 'Feminino'."
    
# Função simples para traduzir para português
def traduzir_para_pt(texto_em_ingles):
    tradutor = GoogleTranslator(source='auto', target='pt')
    return tradutor.translate(texto_em_ingles)


def validar_email_completo(email):
    """
    Valida formato, domínio e se o email pode receber mensagens.
    Usa a biblioteca email-validator que é a mais completa.
    Retorna: (bool, str, dict) - (válido, mensagem, info)
    """
    excecao_traduzida_pt = ""
    try:
        # Valida o email com verificações completas
        v = validate_email(email, check_deliverability=True)
        
        # Normaliza o email (opcional)
        email_normalizado = v.normalized
        
        return True, f"Email válido: {email_normalizado}", {
            'email': email_normalizado,
            'dominio': v.domain,
            'local_part': v.local_part
        }
        
    except EmailNotValidError as e:
        # Mensagem de erro detalhada
        excecao_traduzida_pt = traduzir_para_pt(str(e))
        return False, excecao_traduzida_pt, None
    

    
def validar_pagamento(tipo_pagamento: str) -> tuple:
    """
    Valida se a forma de pagamento é aceita.
    
    Args:
        tipo_pagamento: String com a forma de pagamento
    
    Returns:
        tuple: (bool, str) - (válido, mensagem_erro)
    """
    tipo_pagamento = tipo_pagamento.lower().strip() if tipo_pagamento else ""
    formas_aceitas = ["cartão de crédito", "cartão de débito", "dinheiro", "pix"]
    
    if not tipo_pagamento:
        return False, "Forma de pagamento não informada."
    
    if tipo_pagamento.lower().strip() not in [f.lower() for f in formas_aceitas]:
        return False, f"Forma de pagamento '{tipo_pagamento}' não é aceita. Use: {', '.join(formas_aceitas)}"
    
    return True, ""
       

# Informações de validção do pedido antes de inserir no banco de dados
def validar_forma_entrega(e_entrega: str) -> tuple:
    """
    Valida se a forma de entrega é válida.
    
    Args:
        e_entrega: String "entrega" ou "retirada"
    
    Returns:
        tuple: (bool, str) - (válido, mensagem_erro)
    """
    if not e_entrega:
        return False, "Forma de entrega não informada."
    
    e_entrega_lower = e_entrega.lower().strip()
    
    if e_entrega_lower not in ["entrega", "retirada"]:
        return False, f"Forma de entrega '{e_entrega}' inválida. Use 'entrega' ou 'retirada'."
    
    return True, ""
    