# code/logger_config.py
# Configuração centralizada de logs para toda a aplicação

import os
import sys
from loguru import logger

# ----------------------------------------------------------------------
# CONFIGURAÇÃO DE LOGS (UNIFICADA)
# ----------------------------------------------------------------------

def configurar_logs():
    """
    Configura os logs uma única vez para toda a aplicação.
    Deve ser chamada no início do aplicativo (ex: no arquivo principal).
    """
    # Remove handlers padrão para evitar duplicidade
    logger.remove()

    # Adiciona saída no terminal
    logger.add(
        sys.stderr,
        level="INFO",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
    )

    # Cria pasta de logs se não existir
    PASTA_LOGS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "logs"))
    os.makedirs(PASTA_LOGS, exist_ok=True)

    CAMINHO_ARQUIVO_LOG = os.path.join(PASTA_LOGS, "pizzaria.log")

    # Adiciona saída em arquivo
    logger.add(
        CAMINHO_ARQUIVO_LOG,
        rotation="5 MB",
        retention="10 days",
        level="INFO",
        encoding="utf-8",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    )

    logger.info("✅ Sistema de logs configurado com sucesso!")


# Função para obter o logger já configurado
def get_logger():
    """
    Retorna o logger configurado.
    """
    return logger


# Flag para garantir que a configuração seja feita apenas uma vez
_LOGS_CONFIGURADO = False

def setup_logs_once():
    """
    Configura os logs apenas uma vez, mesmo se chamado múltiplas vezes.
    """
    global _LOGS_CONFIGURADO
    if not _LOGS_CONFIGURADO:
        configurar_logs()
        _LOGS_CONFIGURADO = True
    return logger