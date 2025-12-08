import os
import json
from datetime import date, datetime

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox,
    QPushButton, QMessageBox, QHBoxLayout, QFileDialog, QLabel,
    QDateEdit, QCheckBox, QGroupBox, QScrollArea, QWidget
)

from database import get_session
from models import Cliente, TipoRelatorio, EntradaRelatorio
from config_relatorios import get_output_dir
from reports_combo import generate_end_combo_report


class RelatorioEndDialog(QDialog):
    """
    Tela unificada para geração de relatórios END (LP / PM / US)
    em um único arquivo, com CAPA + relatórios selecionados.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Novo Relatório END (LP / PM / US) - RL Metais")
        self.resize(900, 750)

        # Estados internos para caminhos das fotos
        self._foto_capa_path = None
        self._foto_lp_2 = None
        self._foto_lp_3 = None
        self._foto_pm_2 = None
        self._foto_us_2 = None
        self._foto_us_3 = None

        # ================= LAYOUT PRINCIPAL =================
        main_layout = QVBoxLayout(self)

        # --------- Área rolável ---------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setAlignment(Qt.AlignTop)

        # ====================================================
        # 1) DADOS COMUNS
        # ====================================================
        form_comum = QFormLayout()

        self.cb_cliente = QComboBox()
        self._carregar_clientes()

        self.ed_numrel = QLineEdit()
        self.ed_peca = QLineEdit()
        self.ed_num_desenho = QLineEdit()
        self.ed_quantidade = QLineEdit()
        self.ed_local_insp = QLineEdit()

        self.dt_data_insp = QDateEdit()
        self.dt_data_insp.setCalendarPopup(True)
        self.dt_data_insp.setDate(QDate.currentDate())

        self.lbl_foto_capa = QLabel("Nenhum arquivo selecionado")
        self.btn_foto_capa = QPushButton("Selecionar Foto da Capa")
        self.btn_foto_capa.clicked.connect(self._selecionar_foto_capa)

        form_comum.addRow("Cliente (herda dados de empresa):", self.cb_cliente)
        form_comum.addRow("Número do Relatório *", self.ed_numrel)
        form_comum.addRow("Peça Inspecionada", self.ed_peca)
        form_comum.addRow("Nº Desenho / OP", self.ed_num_desenho)
        form_comum.addRow("Quantidade", self.ed_quantidade)
        form_comum.addRow("Local da Inspeção", self.ed_local_insp)
        form_comum.addRow("Data da Inspeção", self.dt_data_insp)
        form_comum.addRow(self.btn_foto_capa, self.lbl_foto_capa)

        content_layout.addLayout(form_comum)

        # ====================================================
        # 2) CHECKBOXES DOS ENSAIOS
        # ====================================================
        chk_layout = QHBoxLayout()
        self.chk_lp = QCheckBox("Incluir Líquido Penetrante (LP)")
        self.chk_pm = QCheckBox("Incluir Partículas Magnéticas (PM)")
        self.chk_us = QCheckBox("Incluir Ultrassom (US)")
        chk_layout.addWidget(self.chk_lp)
        chk_layout.addWidget(self.chk_pm)
        chk_layout.addWidget(self.chk_us)

        content_layout.addLayout(chk_layout)

        self.chk_lp.toggled.connect(self._toggle_lp)
        self.chk_pm.toggled.connect(self._toggle_pm)
        self.chk_us.toggled.connect(self._toggle_us)

        # ====================================================
        # 3) SEÇÃO LP
        # ====================================================
        self.grp_lp = QGroupBox("Dados do Ensaio de Líquido Penetrante (LP)")
        form_lp = QFormLayout(self.grp_lp)

        self.ed_local_insp_lp = QLineEdit()
        self.ed_fab_pen = QLineEdit()
        self.ed_val_pen = QLineEdit()
        self.ed_lote_pen = QLineEdit()
        self.ed_fab_rev = QLineEdit()
        self.ed_val_rev = QLineEdit()
        self.ed_lote_rev = QLineEdit()
        self.ed_temperatura_lp = QLineEdit()
        self.ed_cond_superficial_lp = QLineEdit()

        self.cbo_laudo_lp = QComboBox()
        self.cbo_laudo_lp.addItem("Aprovado (A)", "A")
        self.cbo_laudo_lp.addItem("Reprovado (R)", "R")
        self.cbo_laudo_lp.currentIndexChanged.connect(self._update_campos_reprovado_lp)

        self.ed_tipo_desc_lp = QLineEdit()
        self.ed_loc_desc_lp = QLineEdit()
        self.ed_dim_desc_lp = QLineEdit()

        self.lbl_foto_lp2 = QLabel("Nenhum arquivo selecionado")
        self.lbl_foto_lp3 = QLabel("Nenhum arquivo selecionado")
        self.btn_foto_lp2 = QPushButton("Selecionar Foto LP 2")
        self.btn_foto_lp3 = QPushButton("Selecionar Foto LP 3")
        self.btn_foto_lp2.clicked.connect(self._selecionar_foto_lp2)
        self.btn_foto_lp3.clicked.connect(self._selecionar_foto_lp3)

        form_lp.addRow("Local da Inspeção (LP)", self.ed_local_insp_lp)
        form_lp.addRow("Penetrante - Data de Fabricação", self.ed_fab_pen)
        form_lp.addRow("Penetrante - Validade", self.ed_val_pen)
        form_lp.addRow("Penetrante - Lote", self.ed_lote_pen)
        form_lp.addRow("Revelador - Data de Fabricação", self.ed_fab_rev)
        form_lp.addRow("Revelador - Validade", self.ed_val_rev)
        form_lp.addRow("Revelador - Lote", self.ed_lote_rev)
        form_lp.addRow("Temperatura (LP)", self.ed_temperatura_lp)
        form_lp.addRow("Condição da Superfície (LP)", self.ed_cond_superficial_lp)

        form_lp.addRow("Laudo LP (A/R)", self.cbo_laudo_lp)
        form_lp.addRow("Tipo de Descontinuidade (se R)", self.ed_tipo_desc_lp)
        form_lp.addRow("Localização (mm) (se R)", self.ed_loc_desc_lp)
        form_lp.addRow("Dimensão (mm) (se R)", self.ed_dim_desc_lp)

        form_lp.addRow(self.btn_foto_lp2, self.lbl_foto_lp2)
        form_lp.addRow(self.btn_foto_lp3, self.lbl_foto_lp3)

        content_layout.addWidget(self.grp_lp)

        # ====================================================
        # 4) SEÇÃO PM
        # ====================================================
        self.grp_pm = QGroupBox("Dados do Ensaio de Partículas Magnéticas (PM)")
        form_pm = QFormLayout(self.grp_pm)

        self.ed_local_insp_pm = QLineEdit()
        self.ed_fab_particula = QLineEdit()
        self.ed_val_particula = QLineEdit()
        self.ed_lote_particula = QLineEdit()
        self.ed_temperatura_pm = QLineEdit()
        self.ed_cond_superficial_pm = QLineEdit()

        self.cbo_laudo_pm = QComboBox()
        self.cbo_laudo_pm.addItem("Aprovado (A)", "A")
        self.cbo_laudo_pm.addItem("Reprovado (R)", "R")
        self.cbo_laudo_pm.currentIndexChanged.connect(self._update_campos_reprovado_pm)

        self.ed_tipo_desc_pm = QLineEdit()
        self.ed_loc_desc_pm = QLineEdit()
        self.ed_dim_desc_pm = QLineEdit()

        self.lbl_foto_pm2 = QLabel("Nenhum arquivo selecionado")
        self.btn_foto_pm2 = QPushButton("Selecionar Foto PM 2")
        self.btn_foto_pm2.clicked.connect(self._selecionar_foto_pm2)

        form_pm.addRow("Local da Inspeção (PM)", self.ed_local_insp_pm)
        form_pm.addRow("Data de Fabricação da Partícula", self.ed_fab_particula)
        form_pm.addRow("Data de Validade da Partícula", self.ed_val_particula)
        form_pm.addRow("Lote da Partícula", self.ed_lote_particula)
        form_pm.addRow("Temperatura (PM)", self.ed_temperatura_pm)
        form_pm.addRow("Condição da Superfície (PM)", self.ed_cond_superficial_pm)

        form_pm.addRow("Laudo PM (A/R)", self.cbo_laudo_pm)
        form_pm.addRow("Tipo de Descontinuidade (se R)", self.ed_tipo_desc_pm)
        form_pm.addRow("Localização (mm) (se R)", self.ed_loc_desc_pm)
        form_pm.addRow("Dimensão (mm) (se R)", self.ed_dim_desc_pm)

        form_pm.addRow(self.btn_foto_pm2, self.lbl_foto_pm2)

        content_layout.addWidget(self.grp_pm)

        # ====================================================
        # 5) SEÇÃO US
        # ====================================================
        self.grp_us = QGroupBox("Dados do Ensaio de Ultrassom (US)")
        form_us = QFormLayout(self.grp_us)

        self.ed_local_insp_us = QLineEdit()
        self.ed_material_us = QLineEdit()
        self.ed_cond_superficial_us = QLineEdit()
        self.ed_regiao_insp_us = QLineEdit()
        self.ed_espessura_us = QLineEdit()

        self.cbo_laudo_us = QComboBox()
        self.cbo_laudo_us.addItem("Aprovado (A)", "A")
        self.cbo_laudo_us.addItem("Reprovado (R)", "R")
        self.cbo_laudo_us.currentIndexChanged.connect(self._update_campos_reprovado_us)

        self.ed_tipo_desc_us = QLineEdit()
        self.ed_loc_desc_us = QLineEdit()
        self.ed_dim_desc_us = QLineEdit()

        self.lbl_foto_us2 = QLabel("Nenhum arquivo selecionado")
        self.lbl_foto_us3 = QLabel("Nenhum arquivo selecionado")
        self.btn_foto_us2 = QPushButton("Selecionar Foto US 2")
        self.btn_foto_us3 = QPushButton("Selecionar Foto US 3")
        self.btn_foto_us2.clicked.connect(self._selecionar_foto_us2)
        self.btn_foto_us3.clicked.connect(self._selecionar_foto_us3)

        form_us.addRow("Local do Ensaio (US)", self.ed_local_insp_us)
        form_us.addRow("Material", self.ed_material_us)
        form_us.addRow("Condição da Superfície (US)", self.ed_cond_superficial_us)
        form_us.addRow("Região Inspecionada", self.ed_regiao_insp_us)
        form_us.addRow("Espessura (mm)", self.ed_espessura_us)

        form_us.addRow("Laudo US (A/R)", self.cbo_laudo_us)
        form_us.addRow("Tipo de Descontinuidade (se R)", self.ed_tipo_desc_us)
        form_us.addRow("Localização (mm) (se R)", self.ed_loc_desc_us)
        form_us.addRow("Dimensão (mm) (se R)", self.ed_dim_desc_us)

        form_us.addRow(self.btn_foto_us2, self.lbl_foto_us2)
        form_us.addRow(self.btn_foto_us3, self.lbl_foto_us3)

        content_layout.addWidget(self.grp_us)

        # Deixa grupos escondidos inicialmente
        self.grp_lp.setVisible(False)
        self.grp_pm.setVisible(False)
        self.grp_us.setVisible(False)

        # Atualiza estado dos campos de reprovação
        self._update_campos_reprovado_lp()
        self._update_campos_reprovado_pm()
        self._update_campos_reprovado_us()

        # Conecta conteúdo ao scroll e adiciona ao layout principal
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # ====================================================
        # 6) BOTÕES FINAIS
        # ====================================================
        btns = QHBoxLayout()
        btn_ok = QPushButton("Gerar Relatório Único")
        btn_cancel = QPushButton("Fechar")
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)

        main_layout.addLayout(btns)

    # ========================================================
    #  UTILITÁRIOS
    # ========================================================

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

    # ---- seleção de fotos ----
    def _selecionar_foto_capa(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto da Capa", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto_capa_path = path
            self.lbl_foto_capa.setText(path)

    def _selecionar_foto_lp2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto LP 2", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto_lp_2 = path
            self.lbl_foto_lp2.setText(path)

    def _selecionar_foto_lp3(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto LP 3", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto_lp_3 = path
            self.lbl_foto_lp3.setText(path)

    def _selecionar_foto_pm2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto PM 2", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto_pm_2 = path
            self.lbl_foto_pm2.setText(path)

    def _selecionar_foto_us2(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto US 2", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto_us_2 = path
            self.lbl_foto_us2.setText(path)

    def _selecionar_foto_us3(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Foto US 3", "", "Imagens (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            self._foto_us_3 = path
            self.lbl_foto_us3.setText(path)

    # ---- laudo A/R ----
    def _update_campos_reprovado_lp(self):
        valor = self.cbo_laudo_lp.currentData()
        is_reprovado = (valor == "R")
        self.ed_tipo_desc_lp.setEnabled(is_reprovado)
        self.ed_loc_desc_lp.setEnabled(is_reprovado)
        self.ed_dim_desc_lp.setEnabled(is_reprovado)

    def _update_campos_reprovado_pm(self):
        valor = self.cbo_laudo_pm.currentData()
        is_reprovado = (valor == "R")
        self.ed_tipo_desc_pm.setEnabled(is_reprovado)
        self.ed_loc_desc_pm.setEnabled(is_reprovado)
        self.ed_dim_desc_pm.setEnabled(is_reprovado)

    def _update_campos_reprovado_us(self):
        valor = self.cbo_laudo_us.currentData()
        is_reprovado = (valor == "R")
        self.ed_tipo_desc_us.setEnabled(is_reprovado)
        self.ed_loc_desc_us.setEnabled(is_reprovado)
        self.ed_dim_desc_us.setEnabled(is_reprovado)

    # ---- mostrar / esconder grupos conforme checkbox ----
    def _toggle_lp(self, checked: bool):
        self.grp_lp.setVisible(checked)

    def _toggle_pm(self, checked: bool):
        self.grp_pm.setVisible(checked)

    def _toggle_us(self, checked: bool):
        self.grp_us.setVisible(checked)

    # ---- json helper ----
    def _preparar_para_json(self, dados: dict) -> dict:
        convertido = {}
        for k, v in dados.items():
            if isinstance(v, (date, datetime)):
                convertido[k] = v.isoformat()
            else:
                convertido[k] = v
        return convertido

    # ========================================================
    #  GERAÇÃO DO RELATÓRIO ÚNICO
    # ========================================================

    def _on_ok(self):
        numrel = self.ed_numrel.text().strip()
        if not numrel:
            QMessageBox.warning(self, "Atenção", "Número do Relatório é obrigatório.")
            return

        cliente_id = self.cb_cliente.currentData()
        if cliente_id is None:
            QMessageBox.warning(self, "Atenção", "Selecione um cliente.")
            return

        incluir_lp = self.chk_lp.isChecked()
        incluir_pm = self.chk_pm.isChecked()
        incluir_us = self.chk_us.isChecked()

        if not (incluir_lp or incluir_pm or incluir_us):
            QMessageBox.warning(self, "Atenção", "Selecione ao menos um tipo de ensaio (LP, PM ou US).")
            return

        # Validação de campos de descontinuidade se laudo = R
        if incluir_lp and self.cbo_laudo_lp.currentData() == "R":
            if not (self.ed_tipo_desc_lp.text().strip()
                    and self.ed_loc_desc_lp.text().strip()
                    and self.ed_dim_desc_lp.text().strip()):
                QMessageBox.warning(self, "Atenção", "Preencha os campos de descontinuidade do LP.")
                return

        if incluir_pm and self.cbo_laudo_pm.currentData() == "R":
            if not (self.ed_tipo_desc_pm.text().strip()
                    and self.ed_loc_desc_pm.text().strip()
                    and self.ed_dim_desc_pm.text().strip()):
                QMessageBox.warning(self, "Atenção", "Preencha os campos de descontinuidade do PM.")
                return

        if incluir_us and self.cbo_laudo_us.currentData() == "R":
            if not (self.ed_tipo_desc_us.text().strip()
                    and self.ed_loc_desc_us.text().strip()
                    and self.ed_dim_desc_us.text().strip()):
                QMessageBox.warning(self, "Atenção", "Preencha os campos de descontinuidade do US.")
                return

        # Data da inspeção
        data_qdate = self.dt_data_insp.date()
        data_py = date(data_qdate.year(), data_qdate.month(), data_qdate.day())

        session = get_session()
        try:
            cliente = session.get(Cliente, cliente_id)
            if not cliente:
                QMessageBox.critical(self, "Erro", "Cliente não encontrado.")
                return

            endereco_txt = ""
            if cliente.rua:
                endereco_txt = cliente.rua
                if cliente.numero:
                    endereco_txt += f", {cliente.numero}"

            # ---------------- DADOS COMUNS ----------------
            dados_comuns = {
                "NUMRELATORIO": numrel,
                "PECA_INSP": self.ed_peca.text().strip(),
                "NUM_DESENHO": self.ed_num_desenho.text().strip(),
                "QUANTIDADE": self.ed_quantidade.text().strip(),
                "LOCAL_INSP": self.ed_local_insp.text().strip(),
                "DATA_INSP": data_py,
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
            }

            # ---------------- LP ----------------
            dados_lp = None
            if incluir_lp:
                laudo_lp = self.cbo_laudo_lp.currentData()

                if laudo_lp == "A":
                    tipo_desc_lp = "Isento"
                    loc_desc_lp = "Isento"
                    dim_desc_lp = "*****"
                else:
                    tipo_desc_lp = self.ed_tipo_desc_lp.text().strip()
                    loc_desc_lp = self.ed_loc_desc_lp.text().strip()
                    dim_desc_lp = self.ed_dim_desc_lp.text().strip()

                dados_lp = {
                    "LOCAL_INSP": self.ed_local_insp_lp.text().strip() or dados_comuns["LOCAL_INSP"],
                    "FAB_PENETRANTE": self.ed_fab_pen.text().strip(),
                    "VAL_PENETRANTE": self.ed_val_pen.text().strip(),
                    "LOTE_PENETRANTE": self.ed_lote_pen.text().strip(),
                    "FAB_REVELADOR": self.ed_fab_rev.text().strip(),
                    "VAL_REVELADOR": self.ed_val_rev.text().strip(),
                    "LOTE_REVELADOR": self.ed_lote_rev.text().strip(),
                    "TEMPERATURA": self.ed_temperatura_lp.text().strip(),
                    "COND_SUPERFICIAL": self.ed_cond_superficial_lp.text().strip(),
                    "LAUDO": laudo_lp,
                    "LAUDO_EXTENSO": "APROVADO" if laudo_lp == "A" else "REPROVADO",
                    "TIPO_DESC": tipo_desc_lp,
                    "LOC_DESC": loc_desc_lp,
                    "DIM_DESC": dim_desc_lp,
                    "FOTO_2": self._foto_lp_2,
                    "FOTO_3": self._foto_lp_3,
                }

            # ---------------- PM ----------------
            dados_pm = None
            if incluir_pm:
                laudo_pm = self.cbo_laudo_pm.currentData()

                if laudo_pm == "A":
                    tipo_desc_pm = "Isento"
                    loc_desc_pm = "Ver Foto"
                    dim_desc_pm = "Isento"
                else:
                    tipo_desc_pm = self.ed_tipo_desc_pm.text().strip()
                    loc_desc_pm = self.ed_loc_desc_pm.text().strip()
                    dim_desc_pm = self.ed_dim_desc_pm.text().strip()

                dados_pm = {
                    "LOCAL_INSP": self.ed_local_insp_pm.text().strip() or dados_comuns["LOCAL_INSP"],
                    "FAB_PARTICULA": self.ed_fab_particula.text().strip(),
                    "VAL_PARTICULA": self.ed_val_particula.text().strip(),
                    "LOTE_PARTICULA": self.ed_lote_particula.text().strip(),
                    "TEMPERATURA": self.ed_temperatura_pm.text().strip(),
                    "COND_SUPERFICIAL": self.ed_cond_superficial_pm.text().strip(),
                    "LAUDO": laudo_pm,
                    "LAUDO_EXTENSO": "APROVADO" if laudo_pm == "A" else "REPROVADO",
                    "TIPO_DESC": tipo_desc_pm,
                    "LOC_DESC": loc_desc_pm,
                    "DIM_DESC": dim_desc_pm,
                    "FOTO_2": self._foto_pm_2,
                }

            # ---------------- US ----------------
            dados_us = None
            if incluir_us:
                laudo_us = self.cbo_laudo_us.currentData()

                if laudo_us == "A":
                    tipo_desc_us = "Isento"
                    loc_desc_us = "Ver Foto"
                    dim_desc_us = "Isento"
                else:
                    tipo_desc_us = self.ed_tipo_desc_us.text().strip()
                    loc_desc_us = self.ed_loc_desc_us.text().strip()
                    dim_desc_us = self.ed_dim_desc_us.text().strip()

                dados_us = {
                    "LOCAL_INSP": self.ed_local_insp_us.text().strip() or dados_comuns["LOCAL_INSP"],
                    "MATERIAL": self.ed_material_us.text().strip(),
                    "COND_SUPERFICIAL": self.ed_cond_superficial_us.text().strip(),
                    "REGIAO_INSP": self.ed_regiao_insp_us.text().strip(),
                    "ESPESSURA": self.ed_espessura_us.text().strip(),
                    "LAUDO": laudo_us,
                    "LAUDO_EXTENSO": "APROVADO" if laudo_us == "A" else "REPROVADO",
                    "TIPO_DESC": tipo_desc_us,
                    "LOC_DESC": loc_desc_us,
                    "DIM_DESC": dim_desc_us,
                    "FOTO_2": self._foto_us_2,
                    "FOTO_3": self._foto_us_3,
                }

            # ---------------- GERA RELATÓRIO ÚNICO ----------------
            docx_path, pdf_path = generate_end_combo_report(
                dados_comuns=dados_comuns,
                incluir_lp=incluir_lp,
                incluir_pm=incluir_pm,
                incluir_us=incluir_us,
                dados_lp=dados_lp,
                dados_pm=dados_pm,
                dados_us=dados_us,
                foto_capa=self._foto_capa_path,
            )

            # Tipo para histórico (usa o primeiro que estiver marcado na ordem US, LP, PM)
            tipo_nome = None
            if incluir_us:
                tipo_nome = "Ultrassom - US"
            elif incluir_lp:
                tipo_nome = "Líquido Penetrante - LP"
            elif incluir_pm:
                tipo_nome = "Partículas Magnéticas - PM"

            tipo = None
            if tipo_nome:
                tipo = (
                    session.query(TipoRelatorio)
                    .filter_by(nome=tipo_nome)
                    .first()
                )

            dados_json = self._preparar_para_json({
                "comuns": dados_comuns,
                "lp": dados_lp,
                "pm": dados_pm,
                "us": dados_us,
            })

            entrada = EntradaRelatorio(
                cliente_id=cliente.id,
                tipo_relatorio_id=tipo.id if tipo else None,
                relatorio_num=dados_comuns.get("NUMRELATORIO"),
                titulo_personalizado=f"Relatório {dados_comuns.get('NUMRELATORIO')}-END",
                dados_json=json.dumps(dados_json, ensure_ascii=False, indent=2, default=str),
                criado_em=datetime.now(),
                caminho_arquivo_gerado=docx_path,
            )
            session.add(entrada)
            session.commit()

            msg_pdf = f"\nPDF gerado em:\n{pdf_path}" if pdf_path else ""
            QMessageBox.information(
                self,
                "Sucesso",
                f"Relatório único gerado em:\n{docx_path}{msg_pdf}",
            )

        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erro", f"Falha ao gerar relatório combinado:\n{e}")
        finally:
            session.close()
