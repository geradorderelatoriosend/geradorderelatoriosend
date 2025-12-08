from flask import (
    Flask,
    send_file,
    request,
    render_template,
    redirect,
    url_for,
    session,
)
import os
from datetime import datetime

from database import get_session
from models import Cliente

import config_relatorios

app = Flask(__name__)
app.secret_key = "super_secret_key"  # TODO trocar depois

# =====================================================
# LOGIN
# =====================================================

VALID_EMAIL = "admin@admin.com"
VALID_PASSWORD = "123456"


def login_required(view):
    def wrapped(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped.__name__ = view.__name__
    return wrapped


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == VALID_EMAIL and password == VALID_PASSWORD:
            session["email"] = email
            return redirect(url_for("dashboard"))
        else:
            error = "Usuário ou senha inválidos"
    return render_template("login.html", error=error)

@app.route("/clientes", methods=["GET", "POST"])
@login_required
def clientes_form():
    """
    Tela de Cadastro / Edição de Clientes (versão web).
    - GET: lista clientes e, se tiver cliente_id na querystring, carrega esse cliente no formulário
    - POST: trata botões Novo / Salvar / Excluir
    """
    session_db = get_session()

    try:
        # ------------------------------
        # 1) Tratamento das ações (POST)
        # ------------------------------
        if request.method == "POST":
            acao = request.form.get("acao")
            cliente_id = request.form.get("cliente_id")

            # Campos do formulário
            dados = {
                "razao_social": request.form.get("razao_social") or "",
                "contato": request.form.get("contato") or "",
                "cnpj": request.form.get("cnpj") or "",
                "ie": request.form.get("ie") or "",
                "rua": request.form.get("rua") or "",
                "numero": request.form.get("numero") or "",
                "bairro": request.form.get("bairro") or "",
                "cidade": request.form.get("cidade") or "",
                "uf": request.form.get("uf") or "",
                "cep": request.form.get("cep") or "",
                "ddd": request.form.get("ddd") or "",
                "telefone": request.form.get("telefone") or "",
                "email": request.form.get("email") or "",
            }

            # 👉 NOVO: limpa o formulário (não mexe em banco)
            if acao == "novo":
                return redirect(url_for("clientes_form"))

            # 👉 SALVAR: cria ou atualiza
            if acao == "salvar":
                if cliente_id:  # atualizar existente
                    cli = session_db.get(Cliente, int(cliente_id))
                    if cli:
                        for campo, valor in dados.items():
                            setattr(cli, campo, valor)
                else:  # novo cliente
                    cli = Cliente(**dados)
                    session_db.add(cli)

                session_db.commit()
                # volta para a tela com o cliente recém-salvo selecionado
                return redirect(url_for("clientes_form", cliente_id=cli.id))

            # 👉 EXCLUIR: apaga o cliente atual
            if acao == "excluir" and cliente_id:
                cli = session_db.get(Cliente, int(cliente_id))
                if cli:
                    session_db.delete(cli)
                    session_db.commit()
                return redirect(url_for("clientes_form"))

        # --------------------------------------
        # 2) GET normal: carrega lista + cliente
        # --------------------------------------
        clientes = session_db.query(Cliente).order_by(Cliente.razao_social).all()

        cliente_atual = None
        cliente_id_get = request.args.get("cliente_id")
        if cliente_id_get:
            cliente_atual = session_db.get(Cliente, int(cliente_id_get))

        return render_template(
            "clientes.html",
            clientes=clientes,
            cliente_atual=cliente_atual,
        )

    finally:
        session_db.close()


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =====================================================
# DASHBOARD
# =====================================================

@app.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")

