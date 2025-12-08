import os
from datetime import date

from docx import Document
from docxcompose.composer import Composer

from utils_docx import (
    replace_placeholders,
    inserir_foto_por_placeholder,
    format_date_br,
    date_por_extenso,
)

# possíveis nomes de template de capa para US, na mesma pasta do US_TEMPLATE.docx
CAPA_TEMPLATE_CANDIDATES = [
    "CAPA_US_TEMPLATE.docx",
    "CAPA_US.docx",
    "CAPA_TEMPLATE.docx",
    "CAPA.docx",
]


def _montar_mapping(dados: dict) -> dict:
    """
    Monta o dicionário de placeholders -> valores em string,
    incluindo tratamento de datas e conclusão automática.
    """
    dados_limpos = dict(dados)

    # Trata data de inspeção
    data_insp = dados_limpos.get("DATA_INSP")
    if isinstance(data_insp, date):
        dados_limpos["DATA_INSP"] = format_date_br(data_insp)
        dados_limpos["DATA_INSP_EXTENSO"] = date_por_extenso(data_insp)
    elif data_insp:
        dados_limpos["DATA_INSP"] = str(data_insp)
        dados_limpos["DATA_INSP_EXTENSO"] = ""
    else:
        dados_limpos["DATA_INSP"] = ""
        dados_limpos["DATA_INSP_EXTENSO"] = ""

    # Conclusão automática
    laudo = dados_limpos.get("LAUDO")
    laudo_ext = dados_limpos.get("LAUDO_EXTENSO") or ""

    if laudo == "A":
        conclusao = (
            "CONCLUSÃO: Não Foram evidenciadas indicações relevantes, "
            f"estando o ensaio {laudo_ext} segundo o critério de aceitação da norma acima"
        )
    else:
        conclusao = (
            "CONCLUSÃO: Foram evidenciadas indicações relevantes, "
            f"estando o ensaio {laudo_ext} segundo o critério de aceitação da norma acima"
        )

    dados_limpos["CONCLUSAO"] = conclusao

    mapping: dict[str, str] = {}
    for k, v in dados_limpos.items():
        # Fotos não entram como texto
        if k.startswith("FOTO_"):
            continue
        placeholder = "{{" + k + "}}"
        mapping[placeholder] = "" if v is None else str(v)

    mapping["{{CONCLUSAO}}"] = conclusao

    return mapping


def _carregar_capa(template_path: str, mapping: dict):
    """
    Tenta carregar um template de capa na mesma pasta do template principal,
    usando a lista CAPA_TEMPLATE_CANDIDATES. Se não encontrar, retorna None.
    """
    base_dir = os.path.dirname(template_path)

    for nome in CAPA_TEMPLATE_CANDIDATES:
        caminho = os.path.join(base_dir, nome)
        if os.path.exists(caminho):
            doc_capa = Document(caminho)
            replace_placeholders(doc_capa, mapping)
            return doc_capa

    return None


def generate_ultrassom_report(dados: dict, template_path: str, output_dir: str) -> str:
    """
    Gera o relatório de Ultrassom (US) com CAPA + LAUDO em um único arquivo .docx,
    se existir template de capa. Caso contrário, gera somente o laudo (comportamento antigo).
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    # Garante diretório de saída
    os.makedirs(output_dir, exist_ok=True)

    numrel = str(dados.get("NUMRELATORIO", "")).strip()
    if not numrel:
        raise ValueError("O campo NUMRELATORIO é obrigatório.")

    # monta mapping com datas e conclusão
    mapping = _montar_mapping(dados)

    # ---------------------- CAPA (opcional) ----------------------
    doc_capa = _carregar_capa(template_path, mapping)

    # ---------------------- LAUDO (US_TEMPLATE) -------------------
    doc_laudo = Document(template_path)
    replace_placeholders(doc_laudo, mapping)

    # Inserção das fotos com tamanhos adequados
    foto1 = dados.get("FOTO_1")
    if foto1:
        inserir_foto_por_placeholder(doc_laudo, "{{FOTO_1}}", foto1, height_cm=10.0)

    foto2 = dados.get("FOTO_2")
    if foto2:
        inserir_foto_por_placeholder(doc_laudo, "{{FOTO_2}}", foto2, height_cm=4.0)

    foto3 = dados.get("FOTO_3")
    if foto3:
        inserir_foto_por_placeholder(doc_laudo, "{{FOTO_3}}", foto3, height_cm=4.0)

    # ---------------------- JUNÇÃO CAPA + LAUDO -------------------
    file_name = f"Relatório {numrel}-US.docx"
    output_path = os.path.join(output_dir, file_name)

    if doc_capa is not None:
        composer = Composer(doc_capa)
        composer.append(doc_laudo)
        composer.save(output_path)
    else:
        doc_laudo.save(output_path)

    return output_path
