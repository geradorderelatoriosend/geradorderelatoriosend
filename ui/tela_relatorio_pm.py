import os
import json
from datetime import date, datetime

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QHBoxLayout, QFileDialog, QLabel, QDateEdit
)

from database import get_session
from models import Cliente, TipoRelatorio, EntradaRelatorio
from reports_pm import generate_pm_report
from config_relatorios import get_output_dir


class RelatorioPMDialog(QDialog):
    """
    Tela para gerar Relatório de Partículas Magnéticas (PM),
    alinhada ao PM_TEMPLATE.docx (sem Foto 3).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Relatório de Partículas Magnéticas (PM) - RL Metais")
        self.resize(650, 620)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        # -------- Cliente --------
        self.cb_cliente = QComboBox()
        self._carregar_clientes()

        # -------- Campos gerais --------
        self.ed_numrel = QLineEdit()
        self.ed_peca = QLineEdit()
        self.ed_num_desenho = QLineEdit()
        self.ed_quantidade = QLineEdit()
        self.ed_local_insp = QLineEdit()

        self.dt_data_insp = QDateEdit()
        self.dt_data_insp.setCalendarPopup(True)
        self.dt_data_insp.setDate(QDate.currentDate())

        # -------- Campos específicos do template --------
        self.ed_fab_particula = QLineEdit()   # FAB_PARTICULA
        self.ed_val_particula = QLineEdit()   # VAL_PARTICULA
        self.ed_lote_particula = QLineEdit()  # LOTE_PARTICULA

        self.ed_temperatura = QLineEdit()     # TEMPERATURA
        self.ed_cond_superficial = QLineEdit()  # COND_SUPERFICIAL

        # -------- Fotos (somente FOTO_1 e FOTO_2) --------
        self.lbl_foto1 = QLabel("Nenhum arquivo selecionado")
        self.lbl_foto2 = QLabel("Nenhum arquivo selecionado")
        self.btn_foto1 = QPushButton("Selecionar Foto 1 (Capa)")
        self.btn_foto2 = QPushButton("Selecionar Foto 2")
        self.btn_foto1.clicked.connect(self._selecionar_foto1)
        self.btn_foto2.clicked.connect(self._selecionar_foto2)

        # -------- Monta formulário --------
        form.addRow("Cliente (herda dados de empresa):", self.cb_cliente)
        form.addRow("Número do Relatório *", self.ed_numrel)
        form.addRow("Peça Inspecionada", self.ed_peca)
        form.addRow("Nº Desenho / OP", self.ed_num_desenho)
        form.addRow("Quantidade", self.ed_quantidade)
        form.addRow("Local da Inspeção", self.ed_local_insp)
        form.addRow("Data da Inspeção", self.dt_data_insp)

        form.addRow("Data de Fabricação da Partícula", self.ed_fab_particula)
        form.addRow("Data de Validade da Partícula", self.ed_val_particula)
        form.addRow("Lote da Partícula", self.ed_lote_particula)

        form.addRow("Temperatura", self.ed_temperatura)
        form.addRow("Condição da Superfície", self.ed_cond_superficial)

        form.addRow(self.btn_foto1, self.lbl_foto1)
        form.addRow(self.btn_foto2, self.lbl_foto2)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Gerar Relatório")
        btn_cancel = QPushButton("Fechar")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        layout.addLayout(btns)

        # Estado interno das fotos
        self._foto1_path = None
        self._foto2_path = None

    # ---------------------- Utilitários ----------------------

    def _carregar_clientes(self):
        self.cb_cliente.clear()
        self.cb_cliente.addItem("Selecione um cliente...", None)
        session = get_session()
        try:
            clientes = session.query(Cliente).order_by(Cliente.razao_social.asc()).all()
            for c in clientes:
                self.cb_cliente.addItem(c.razao_social, c.id)
        finally:
            session.close()

    def _selecionar_foto1(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto 1", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto1_path = path
            self.lbl_foto1.setText(path)

    def _selecionar_foto2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto 2", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto2_path = path
            self.lbl_foto2.setText(path)

    def _preparar_para_json(self, dados: dict) -> dict:
        convertido = {}
        for k, v in dados.items():
            if isinstance(v, (date, datetime)):
                convertido[k] = v.isoformat()
            else:
                convertido[k] = v
        return convertido

    # ---------------------- Clique em "Gerar Relatório" ----------------------

    def _on_ok(self):
        numrel = self.ed_numrel.text().strip()
        if not numrel:
            QMessageBox.warning(self, "Atenção", "Número do Relatório é obrigatório.")
            return

        cliente_id = self.cb_cliente.currentData()
        if cliente_id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um cliente para herdar os dados.")
            return

        # Data da inspeção
        data_qdate = self.dt_data_insp.date()
        data_py = date(data_qdate.year(), data_qdate.month(), data_qdate.day())

        dados = {
            "NUMRELATORIO": numrel,
            "PECA_INSP": self.ed_peca.text().strip(),
            "NUM_DESENHO": self.ed_num_desenho.text().strip(),
            "QUANTIDADE": self.ed_quantidade.text().strip(),
            "LOCAL_INSP": self.ed_local_insp.text().strip(),
            "DATA_INSP": data_py,
            "FAB_PARTICULA": self.ed_fab_particula.text().strip(),
            "VAL_PARTICULA": self.ed_val_particula.text().strip(),
            "LOTE_PARTICULA": self.ed_lote_particula.text().strip(),
            "TEMPERATURA": self.ed_temperatura.text().strip(),
            "COND_SUPERFICIAL": self.ed_cond_superficial.text().strip(),
            "FOTO_1": self._foto1_path,
            "FOTO_2": self._foto2_path,
        }

        session = get_session()
        try:
            # Tipo de relatório PM (cria se não existir)
            tipo = (
                session.query(TipoRelatorio)
                .filter_by(nome="Partículas Magnéticas - PM")
                .first()
            )
            if not tipo:
                from models import TipoRelatorio as TipoRelatorioModel
                tipo = TipoRelatorioModel(
                    nome="Partículas Magnéticas - PM",
                    descricao="Relatório de Partículas Magnéticas",
                    schema_json="{}",   # campo NOT NULL
                    template_path="templates/PM_TEMPLATE.docx",
                )
                session.add(tipo)
                session.commit()

            cliente = session.get(Cliente, cliente_id)
            if not cliente:
                QMessageBox.critical(self, "Erro", "Cliente selecionado não encontrado no banco.")
                return

            # Endereço formatado
            endereco_txt = ""
            if cliente.rua:
                endereco_txt = cliente.rua
                if cliente.numero:
                    endereco_txt += f", {cliente.numero}"

            merged_dados = dict(dados)
            merged_dados.update({
                "EMPRESA": cliente.razao_social or "",
                "ENDEREÇO": endereco_txt,
                "BAIRRO": cliente.bairro or "",
                "CIDADE": cliente.cidade or "",
                "ESTADO": cliente.uf or "",
                "CEP": cliente.cep or "",
                "CONTATO": cliente.contato or "",
                "DDD": cliente.ddd or "",
                "FONE": cliente.telefone or "",
                "EMAIL": cliente.email or "",
            })

            base_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.abspath(os.path.join(base_dir, "..", tipo.template_path))

            output_dir = get_output_dir()

            caminho_arquivo = generate_pm_report(merged_dados, template_path, output_dir)

            entrada = EntradaRelatorio(
                cliente_id=cliente.id,
                tipo_relatorio_id=tipo.id,
                relatorio_num=merged_dados.get("NUMRELATORIO"),
                titulo_personalizado=f"Relatório {merged_dados.get('NUMRELATORIO')}-PM",
                dados_json=json.dumps(
                    self._preparar_para_json(merged_dados),
                    ensure_ascii=False,
                    indent=2,
                ),
                criado_em=datetime.now(),
                caminho_arquivo_gerado=caminho_arquivo,
            )

            session.add(entrada)
            session.commit()

            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório de PM gerado em:\n{caminho_arquivo}",
            )
            # Mantém a janela aberta
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório de PM:\n{e}")
        finally:
            session.close()
