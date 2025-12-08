import os
from datetime import date
from docx import Document
from utils_docx import (
    replace_placeholders,
    inserir_foto_por_placeholder,
    format_date_br,
    date_por_extenso,
)

def _montar_mapping(dados: dict) -> dict:
    dados_limpos = dict(dados)

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
        if k.startswith("FOTO_"):
            continue
        placeholder = "{{" + k + "}}"
        mapping[placeholder] = "" if v is None else str(v)

    mapping["{{CONCLUSAO}}"] = conclusao
    return mapping


def generate_ultrassom_report(dados: dict, template_path: str, output_dir: str) -> str:
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template não encontrado: {template_path}")

    os.makedirs(output_dir, exist_ok=True)

    numrel = str(dados.get("NUMRELATORIO", "")).strip()
    if not numrel:
        raise ValueError("O campo NUMRELATORIO é obrigatório.")

    mapping = _montar_mapping(dados)

    doc = Document(template_path)
    replace_placeholders(doc, mapping)

    foto1 = dados.get("FOTO_1")
    if foto1:
        inserir_foto_por_placeholder(doc, "{{FOTO_1}}", foto1, height_cm=10.0)

    foto2 = dados.get("FOTO_2")
    if foto2:
        inserir_foto_por_placeholder(doc, "{{FOTO_2}}", foto2, height_cm=4.0)

    foto3 = dados.get("FOTO_3")
    if foto3:
        inserir_foto_por_placeholder(doc, "{{FOTO_3}}", foto3, height_cm=4.0)

    file_name = f"Relatório {numrel}-US.docx"
    output_path = os.path.join(output_dir, file_name)

    doc.save(output_path)
    return output_path
