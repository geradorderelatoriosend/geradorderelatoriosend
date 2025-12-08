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
from reports_ultrassom import generate_ultrassom_report
from config_relatorios import get_output_dir


class RelatorioUltrassomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Relatório de Ultrassom (US) - RL Metais")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        form = QFormLayout()

        # Combobox de clientes
        self.cb_cliente = QComboBox()
        self._carregar_clientes()

        # Campos específicos do relatório (sem dados de empresa/endereço)
        self.ed_numrel = QLineEdit()
        self.ed_peca = QLineEdit()
        self.ed_num_desenho = QLineEdit()
        self.ed_quantidade = QLineEdit()
        self.ed_local_insp = QLineEdit()

        self.dt_data_insp = QDateEdit()
        self.dt_data_insp.setCalendarPopup(True)
        self.dt_data_insp.setDate(QDate.currentDate())

        self.ed_material = QLineEdit()
        self.ed_cond_superficial = QLineEdit()
        self.ed_regiao_insp = QLineEdit()
        self.ed_espessura = QLineEdit()

        # Fotos
        self.lbl_foto1 = QLabel("Nenhum arquivo selecionado")
        self.lbl_foto2 = QLabel("Nenhum arquivo selecionado")
        self.lbl_foto3 = QLabel("Nenhum arquivo selecionado")
        self.btn_foto1 = QPushButton("Selecionar Foto 1 (Capa)")
        self.btn_foto2 = QPushButton("Selecionar Foto 2")
        self.btn_foto3 = QPushButton("Selecionar Foto 3")
        self.btn_foto1.clicked.connect(self._selecionar_foto1)
        self.btn_foto2.clicked.connect(self._selecionar_foto2)
        self.btn_foto3.clicked.connect(self._selecionar_foto3)

        # Montagem do formulário
        form.addRow("Cliente (herda dados de empresa):", self.cb_cliente)
        form.addRow("Número do Relatório *", self.ed_numrel)
        form.addRow("Peça Ensaiada", self.ed_peca)
        form.addRow("Nº Ordem Produção", self.ed_num_desenho)
        form.addRow("Quantidade", self.ed_quantidade)
        form.addRow("Local do Ensaio", self.ed_local_insp)
        form.addRow("Data do Ensaio", self.dt_data_insp)
        form.addRow("Material", self.ed_material)
        form.addRow("Condição da Superfície", self.ed_cond_superficial)
        form.addRow("Região Inspecionada", self.ed_regiao_insp)
        form.addRow("Espessura", self.ed_espessura)

        form.addRow(self.btn_foto1, self.lbl_foto1)
        form.addRow(self.btn_foto2, self.lbl_foto2)
        form.addRow(self.btn_foto3, self.lbl_foto3)

        layout.addLayout(form)

        btns = QHBoxLayout()
        btn_ok = QPushButton("Gerar Relatório")
        btn_cancel = QPushButton("Fechar")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        layout.addLayout(btns)

        # Estado interno
        self._foto1_path = None
        self._foto2_path = None
        self._foto3_path = None

    # ---------------------------------------------------------
    # Utilitários internos
    # ---------------------------------------------------------
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

    def _selecionar_foto3(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto 3", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto3_path = path
            self.lbl_foto3.setText(path)

    def _preparar_para_json(self, dados: dict) -> dict:
        """Converte date/datetime para string antes do json.dumps."""
        convertido = {}
        for k, v in dados.items():
            if isinstance(v, (date, datetime)):
                convertido[k] = v.isoformat()
            else:
                convertido[k] = v
        return convertido

    # ---------------------------------------------------------
    # Clique em "Gerar Relatório"
    # ---------------------------------------------------------
    def _on_ok(self):
        numrel = self.ed_numrel.text().strip()
        if not numrel:
            QMessageBox.warning(self, "Atenção", "Número do Relatório é obrigatório.")
            return

        cliente_id = self.cb_cliente.currentData()
        if cliente_id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um cliente para herdar os dados.")
            return

        # Monta data do ensaio
        data_qdate = self.dt_data_insp.date()
        data_py = date(data_qdate.year(), data_qdate.month(), data_qdate.day())

        # Dados básicos (sem cliente ainda)
        dados = {
            "NUMRELATORIO": numrel,
            "PECA_INSP": self.ed_peca.text().strip(),
            "NUM_DESENHO": self.ed_num_desenho.text().strip(),
            "QUANTIDADE": self.ed_quantidade.text().strip(),
            "LOCAL_INSP": self.ed_local_insp.text().strip(),
            "DATA_INSP": data_py,
            "MATERIAL": self.ed_material.text().strip(),
            "COND_SUPERFICIAL": self.ed_cond_superficial.text().strip(),
            "REGIAO_INSP": self.ed_regiao_insp.text().strip(),
            "ESPESSURA": self.ed_espessura.text().strip(),
            "FOTO_1": self._foto1_path,
            "FOTO_2": self._foto2_path,
            "FOTO_3": self._foto3_path,
        }

        session = get_session()
        try:
            # Tipo de relatório
            tipo = session.query(TipoRelatorio).filter_by(nome="Ultrassom - US").first()
            if not tipo:
                QMessageBox.critical(self, "Erro", "Tipo de relatório 'Ultrassom - US' não encontrado.")
                return

            # Cliente
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

            # Mescla dados com placeholders de cliente
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

            # Caminhos
            base_dir = os.path.dirname(os.path.abspath(__file__))
            template_path = os.path.abspath(os.path.join(base_dir, "..", tipo.template_path))

            # 🔹 Agora usa a pasta configurada
            output_dir = get_output_dir()

            # Gera o relatório DOCX
            caminho_arquivo = generate_ultrassom_report(merged_dados, template_path, output_dir)

            # Grava no banco
            entrada = EntradaRelatorio(
                cliente_id=cliente.id,
                tipo_relatorio_id=tipo.id,
                relatorio_num=merged_dados.get("NUMRELATORIO"),
                titulo_personalizado=f"Relatório {merged_dados.get('NUMRELATORIO')}-US",
                dados_json=json.dumps(
                    self._preparar_para_json(merged_dados),
                    ensure_ascii=False,
                    indent=2
                ),
                criado_em=datetime.now(),
                caminho_arquivo_gerado=caminho_arquivo,
            )

            session.add(entrada)
            session.commit()

            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório gerado em:\n{caminho_arquivo}",
            )
            # janela permanece aberta
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório:\n{e}")
        finally:
            session.close()
