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

import config_relatorios

# Pasta temporária para salvar relatórios na nuvem
TEMP_DIR = os.path.join(os.getcwd(), "temp_reports")
os.makedirs(TEMP_DIR, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave")

# ------------------ AUTENTICAÇÃO SIMPLES ------------------ #

# Por enquanto, credenciais fixas
VALID_EMAIL = "admin@rlmetais.com.br"
VALID_PASSWORD = "123456"


def login_required(view_func):
    """Decorator simples para proteger rotas."""
    from functools import wraps

    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_email" not in session:
            return redirect(url_for("login"))
        return view_func(*args, **kwargs)

    return wrapped


@app.route("/")
def index():
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if email == VALID_EMAIL and password == VALID_PASSWORD:
            session["user_email"] = email
            return redirect(url_for("dashboard"))
        else:
            error = "E-mail ou senha inválidos."

    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/clientes")
@login_required
def clientes_form():
    # Por enquanto, só pra não quebrar.
    return "<h3>Tela de Cadastro / Edição de Cliente (em construção)</h3>"


@app.route("/relatorio_end")
@login_required
def relatorio_end_form():
    # Depois vamos colocar o formulário igual ao desktop aqui.
    return "<h3>Novo Relatório END (LP / PM / US) - em construção</h3>"


@app.route("/config_pasta")
@login_required
def config_pasta_relatorios():
    # Essa tela depois vira a configuração da pasta de saída / storage.
    return "<h3>Definir pasta dos relatórios (em construção)</h3>"


# ------------------ GERAÇÃO DE RELATÓRIO ------------------ #

@app.route("/gerar", methods=["POST", "GET"])
@login_required
def gerar_relatorio():
    """
    Rota que chama a função gerar_relatorio_principal
    e devolve o arquivo .docx gerado.
    Aceita POST (a partir do botão do painel) e GET (teste direto).
    """
    # Nome do arquivo final
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_arquivo_final = f"RELATORIO_{timestamp}.docx"
    caminho_final = os.path.join(TEMP_DIR, nome_arquivo_final)

    try:
        # Chama a função que você criou no config_relatorios.py
        config_relatorios.gerar_relatorio_principal(caminho_final)
    except Exception as e:
        return f"Erro na Geração do Relatório: {e}", 500

    try:
        return send_file(
            caminho_final,
            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            ),
            as_attachment=True,
            download_name=nome_arquivo_final,
        )
    except Exception as e:
        return f"Erro ao enviar arquivo: {e}", 500


if __name__ == "__main__":
    # Para rodar localmente se quiser
    app.run(debug=True)
