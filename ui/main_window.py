import os

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSizePolicy,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtGui import QPixmap, Qt

from ui.tela_relatorio_end import RelatorioEndDialog
from ui.tela_cadastro_cliente import CadastroClienteDialog
from config_relatorios import set_output_dir, get_output_dir


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gerador de Relatórios - RL Metais")
        self.resize(900, 600)

        central = QWidget()
        layout = QVBoxLayout(central)

        # -------------------- LOGO RL METAIS --------------------
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)

        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.abspath(os.path.join(base_dir, "..", "rlmetais_logo.png"))

        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            pix = pix.scaledToWidth(350, Qt.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("RL METAIS\nAnálises e Testes de Metais")
            self.logo_label.setStyleSheet("font-size: 20px; font-weight: bold;")

        layout.addWidget(self.logo_label)

        # -------------------- BOTÕES PRINCIPAIS --------------------
        btn_cliente = QPushButton("Cadastrar / Editar Cliente")
        btn_novo_end = QPushButton("Novo Relatório END (LP / PM / US)")
        btn_definir_pasta = QPushButton("Definir pasta dos relatórios")

        for b in (btn_cliente, btn_novo_end, btn_definir_pasta):
            b.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        botoes_container = QWidget()
        botoes_layout = QVBoxLayout(botoes_container)
        botoes_layout.setAlignment(Qt.AlignHCenter)
        botoes_layout.addWidget(btn_cliente)
        botoes_layout.addWidget(btn_novo_end)
        botoes_layout.addWidget(btn_definir_pasta)

        layout.addWidget(botoes_container)

        btn_cliente.clicked.connect(self.abrir_cadastro_cliente)
        btn_novo_end.clicked.connect(self.novo_relatorio_end)
        btn_definir_pasta.clicked.connect(self.definir_pasta_relatorios)

        self.setCentralWidget(central)

    def abrir_cadastro_cliente(self):
        dlg = CadastroClienteDialog(self)
        dlg.exec()

    def novo_relatorio_end(self):
        dlg = RelatorioEndDialog(self)
        dlg.exec()

    def definir_pasta_relatorios(self):
        pasta_atual = get_output_dir()
        nova_pasta = QFileDialog.getExistingDirectory(
            self,
            "Selecione a pasta para salvar os relatórios",
            pasta_atual,
        )
        if nova_pasta:
            set_output_dir(nova_pasta)
            QMessageBox.information(
                self,
                "Pasta definida",
                f"Pasta padrão dos relatórios definida como:\n{nova_pasta}",
            )
