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


# Nome do arquivo de template da CAPA do relatório de Ultrassom
CAPA_US_TEMPLATE_NAME = "CAPA_US_TEMPLATE.docx"


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
        # Se vier string, mantém, mas garante DATA_INSP_EXTENSO vazio
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

    # Monta mapping de {{CHAVE}} -> valor
    mapping: dict[str, str] = {}
    for k, v in dados_limpos.items():
        # Fotos não entram como texto
        if k.startswith("FOTO_"):
            continue
        placeholder = "{{" + k + "}}"
        mapping[placeholder] = "" if v is None else str(v)

    # Também mapeia {{CONCLUSAO}} explicitamente (por garantia)
    mapping["{{CONCLUSAO}}"] = conclusao

    return mapping


def generate_ultrassom_report(dados: dict, template_path: str, output_dir: str) -> str:
    """
    Gera o relatório de Ultrassom (US) com CAPA + LAUDO em um único arquivo .docx.

    - CAPA: CAPA_US_TEMPLATE.docx
    - LAUDO: template_path (US_TEMPLATE.docx)
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template do laudo não encontrado: {template_path}")

    # Garante diretório de saída
    os.makedirs(output_dir, exist_ok=True)

    numrel = str(dados.get("NUMRELATORIO", "")).strip()
    if not numrel:
        raise ValueError("O campo NUMRELATORIO é obrigatório.")

    # Mapping base para placeholders (cliente, peça, datas, etc.)
    mapping = _montar_mapping(dados)

    # ---------------------------------------------------
    # 1) Monta CAPA (se template existir)
    # ---------------------------------------------------
    base_dir = os.path.dirname(template_path)
    capa_path = os.path.join(base_dir, CAPA_US_TEMPLATE_NAME)

    doc_capa = None
    if os.path.exists(capa_path):
        doc_capa = Document(capa_path)
        replace_placeholders(doc_capa, mapping)

    # ---------------------------------------------------
    # 2) Monta LAUDO (US_TEMPLATE)
    # ---------------------------------------------------
    doc_laudo = Document(template_path)
    replace_placeholders(doc_laudo, mapping)

    # Inserção das fotos no laudo
    foto1 = dados.get("FOTO_1")
    if foto1:
        inserir_foto_por_placeholder(doc_laudo, "{{FOTO_1}}", foto1, height_cm=10.0)

    foto2 = dados.get("FOTO_2")
    if foto2:
        inserir_foto_por_placeholder(doc_laudo, "{{FOTO_2}}", foto2, height_cm=4.0)

    foto3 = dados.get("FOTO_3")
    if foto3:
        inserir_foto_por_placeholder(doc_laudo, "{{FOTO_3}}", foto3, height_cm=4.0)

    # ---------------------------------------------------
    # 3) Junta CAPA + LAUDO em um único documento
    # ---------------------------------------------------
    if doc_capa is not None:
        composer = Composer(doc_capa)
        composer.append(doc_laudo)
        doc_final = doc_capa
    else:
        # Se não houver template de capa, usa apenas o laudo (comportamento antigo)
        doc_final = doc_laudo

    file_name = f"Relatório {numrel}-US.docx"
    output_path = os.path.join(output_dir, file_name)

    if doc_capa is not None:
        composer.save(output_path)
    else:
        doc_final.save(output_path)

    return output_path
