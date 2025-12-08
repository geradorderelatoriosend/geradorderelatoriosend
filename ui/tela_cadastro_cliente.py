from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QHBoxLayout, QListWidget, QListWidgetItem
)

from database import get_session
from models import Cliente


class CadastroClienteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Cadastro de Clientes")
        self.resize(700, 400)

        layout = QHBoxLayout(self)

        # Lista de clientes (lado esquerdo)
        self.lista = QListWidget()
        self.lista.itemSelectionChanged.connect(self.carregar_cliente)
        layout.addWidget(self.lista, 1)

        # Painel de formulário (lado direito)
        form_widget = QDialog()
        form_layout = QVBoxLayout(form_widget)

        form = QFormLayout()

        self.ed_razao = QLineEdit()
        self.ed_contato = QLineEdit()
        self.ed_cnpj = QLineEdit()
        self.ed_ie = QLineEdit()
        self.ed_rua = QLineEdit()
        self.ed_numero = QLineEdit()
        self.ed_bairro = QLineEdit()
        self.ed_cidade = QLineEdit()
        self.ed_uf = QLineEdit()
        self.ed_cep = QLineEdit()
        self.ed_ddd = QLineEdit()
        self.ed_fone = QLineEdit()
        self.ed_email = QLineEdit()

        form.addRow("Razão Social *", self.ed_razao)
        form.addRow("Contato", self.ed_contato)
        form.addRow("CNPJ", self.ed_cnpj)
        form.addRow("I.E.", self.ed_ie)
        form.addRow("Rua", self.ed_rua)
        form.addRow("Número", self.ed_numero)
        form.addRow("Bairro", self.ed_bairro)
        form.addRow("Cidade", self.ed_cidade)
        form.addRow("UF", self.ed_uf)
        form.addRow("CEP", self.ed_cep)
        form.addRow("DDD", self.ed_ddd)
        form.addRow("Telefone", self.ed_fone)
        form.addRow("E-mail", self.ed_email)

        form_layout.addLayout(form)

        # Botões inferiores
        btns = QHBoxLayout()
        btn_novo = QPushButton("Novo")
        btn_salvar = QPushButton("Salvar")
        btn_excluir = QPushButton("Excluir")   # <-- Alterado aqui

        btn_novo.clicked.connect(self.novo_cliente)
        btn_salvar.clicked.connect(self.salvar_cliente)
        btn_excluir.clicked.connect(self.excluir_cliente)

        btns.addWidget(btn_novo)
        btns.addWidget(btn_salvar)
        btns.addWidget(btn_excluir)

        form_layout.addLayout(btns)

        layout.addWidget(form_widget, 2)

        # Controle
        self.cliente_atual_id = None
        self.carregar_lista()

    # ---------------------------------------------------------
    # LÓGICA
    # ---------------------------------------------------------

    def carregar_lista(self):
        self.lista.clear()
        session = get_session()
        try:
            clientes = session.query(Cliente).order_by(Cliente.razao_social.asc()).all()
            for c in clientes:
                item = QListWidgetItem(c.razao_social)
                item.setData(256, c.id)
                self.lista.addItem(item)
        finally:
            session.close()

    def carregar_cliente(self):
        itens = self.lista.selectedItems()
        if not itens:
            return
        item = itens[0]
        cliente_id = item.data(256)

        session = get_session()
        try:
            c = session.get(Cliente, cliente_id)
            if not c:
                return

            self.cliente_atual_id = c.id
            self.ed_razao.setText(c.razao_social or "")
            self.ed_contato.setText(c.contato or "")
            self.ed_cnpj.setText(c.cnpj or "")
            self.ed_ie.setText(c.ie or "")
            self.ed_rua.setText(c.rua or "")
            self.ed_numero.setText(c.numero or "")
            self.ed_bairro.setText(c.bairro or "")
            self.ed_cidade.setText(c.cidade or "")
            self.ed_uf.setText(c.uf or "")
            self.ed_cep.setText(c.cep or "")
            self.ed_ddd.setText(c.ddd or "")
            self.ed_fone.setText(c.telefone or "")
            self.ed_email.setText(c.email or "")
        finally:
            session.close()

    def novo_cliente(self):
        self.cliente_atual_id = None
        self.ed_razao.clear()
        self.ed_contato.clear()
        self.ed_cnpj.clear()
        self.ed_ie.clear()
        self.ed_rua.clear()
        self.ed_numero.clear()
        self.ed_bairro.clear()
        self.ed_cidade.clear()
        self.ed_uf.clear()
        self.ed_cep.clear()
        self.ed_ddd.clear()
        self.ed_fone.clear()
        self.ed_email.clear()

    def salvar_cliente(self):
        razao = self.ed_razao.text().strip()
        if not razao:
            QMessageBox.warning(self, "Atenção", "Razão Social é obrigatória.")
            return

        session = get_session()
        try:
            if self.cliente_atual_id:
                c = session.get(Cliente, self.cliente_atual_id)
            else:
                c = Cliente()
                session.add(c)

            c.razao_social = razao
            c.contato = self.ed_contato.text().strip() or None
            c.cnpj = self.ed_cnpj.text().strip() or None
            c.ie = self.ed_ie.text().strip() or None
            c.rua = self.ed_rua.text().strip() or None
            c.numero = self.ed_numero.text().strip() or None
            c.bairro = self.ed_bairro.text().strip() or None
            c.cidade = self.ed_cidade.text().strip() or None
            c.uf = self.ed_uf.text().strip() or None
            c.cep = self.ed_cep.text().strip() or None
            c.ddd = self.ed_ddd.text().strip() or None
            c.telefone = self.ed_fone.text().strip() or None
            c.email = self.ed_email.text().strip() or None

            session.commit()
            self.cliente_atual_id = c.id

            self.carregar_lista()
            QMessageBox.information(self, "Sucesso", "Cliente salvo com sucesso.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao salvar cliente:\n{e}")
        finally:
            session.close()

    # ---------------------------------------------------------
    # ❌ FUNÇÃO DE EXCLUSÃO
    # ---------------------------------------------------------
    def excluir_cliente(self):
        if not self.cliente_atual_id:
            QMessageBox.warning(self, "Atenção", "Selecione um cliente para excluir.")
            return

        resposta = QMessageBox.question(
            self,
            "Excluir Cliente",
            "Tem certeza que deseja excluir este cliente?\nEssa ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No
        )

        if resposta != QMessageBox.Yes:
            return

        session = get_session()
        try:
            c = session.get(Cliente, self.cliente_atual_id)
            if not c:
                QMessageBox.warning(self, "Erro", "Cliente não encontrado.")
                return

            # Excluir
            session.delete(c)
            session.commit()

            # Limpar campos e atualizar lista
            self.novo_cliente()
            self.carregar_lista()

            QMessageBox.information(self, "Sucesso", "Cliente excluído com sucesso.")
        except Exception as e:
            session.rollback()
            QMessageBox.critical(self, "Erro", f"Erro ao excluir cliente:\n{e}")
        finally:
            session.close()
