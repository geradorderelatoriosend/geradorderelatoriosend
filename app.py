from flask import Flask

# Inicializa o Flask, criando a variável 'app' que o Gunicorn procura
app = Flask(__name__)

@app.route("/")
def hello_world():
    # A rota principal que será exibida no seu link do Render
    return "<p>Gerador de Relatórios RL Metais está ONLINE!</p>"

# Se precisar rodar localmente para testar:
if __name__ == "__main__":
    app.run(debug=True)