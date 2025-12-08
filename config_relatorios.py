import os
import json

# Pasta base do projeto (onde está este arquivo)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config_relatorios.json")

# Pasta padrão (se o usuário não configurar outra)
DEFAULT_OUTPUT_DIR = os.path.join(BASE_DIR, "output")


def _carregar_config() -> dict:
    """Lê o arquivo de configuração (se existir) e devolve como dict."""
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        # Se der erro ao ler (arquivo corrompido, etc.), ignora e volta vazio
        return {}


def get_output_dir() -> str:
    """
    Retorna a pasta padrão onde os relatórios serão salvos.
    Se não houver configuração, usa a pasta 'output' na raiz do projeto.
    Garante que a pasta exista.
    """
    cfg = _carregar_config()
    path = cfg.get("output_dir") or DEFAULT_OUTPUT_DIR

    # Se for caminho relativo, converte para absoluto em relação à BASE_DIR
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(BASE_DIR, path))

    os.makedirs(path, exist_ok=True)
    return path


def set_output_dir(path: str) -> None:
    """
    Define a pasta padrão para salvar os relatórios e grava no arquivo de config.
    """
    if not path:
        return

    # Normaliza o caminho
    path = os.path.abspath(path)

    cfg = _carregar_config()
    cfg["output_dir"] = path

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

from datetime import date
import os
import shutil
from reports_combo import generate_end_combo_report

def gerar_relatorio_principal(caminho_final: str) -> str:
    """
    Função usada pela API Flask no Render.
    Gera um relatório END simples e copia para `caminho_final`
    """

    # Dados mínimos só pra passar nos templates
    hoje = date.today()
    numrel = hoje.strftime("%Y%m%d")

    dados = {
        "NUMRELATORIO": numrel,
        "DATA_INSP": hoje,
        "PECA_INSP": "Item Teste",
        "NUM_DESENHO": "",
        "QUANTIDADE": "",
        "LOCAL_INSP": "",
        "EMPRESA": "Teste Render",
        "ENDEREÇO": "",
        "BAIRRO": "",
        "CIDADE": "",
        "ESTADO": "",
        "CEP": "",
        "CONTATO": "",
        "DDD": "",
        "FONE": "",
        "EMAIL": "",
    }

    # só com LP para evitar erro
    incluir_lp = True
    incluir_pm = False
    incluir_us = False

    docx_path, _ = generate_end_combo_report(
        dados_comuns=dados,
        incluir_lp=incluir_lp,
        incluir_pm=incluir_pm,
        incluir_us=incluir_us,
        dados_lp=None,
        dados_pm=None,
        dados_us=None,
        foto_capa=None,
    )

    os.makedirs(os.path.dirname(caminho_final), exist_ok=True)
    shutil.copy2(docx_path, caminho_final)

    return caminho_final
