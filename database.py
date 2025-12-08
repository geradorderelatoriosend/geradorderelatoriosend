
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Nome do arquivo do banco de dados
DB_FILE = "relatorios_end.db"

# Pasta onde está o código (aplicação)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Pasta de dados do usuário (ex.: C:\Users\Aline\AppData\Local\RLMetais)
APPDATA_DIR = os.path.join(
    os.environ.get("LOCALAPPDATA", BASE_DIR),
    "RLMetais"
)
os.makedirs(APPDATA_DIR, exist_ok=True)

DB_PATH = os.path.join(APPDATA_DIR, DB_FILE)

# Migra um banco antigo que esteja na pasta da aplicação, se existir
LEGACY_DB_PATH = os.path.join(BASE_DIR, DB_FILE)
if os.path.exists(LEGACY_DB_PATH) and not os.path.exists(DB_PATH):
    try:
        import shutil
        shutil.copy2(LEGACY_DB_PATH, DB_PATH)
    except Exception:
        pass

# Engine do SQLAlchemy
Engine = create_engine(
    f"sqlite:///{DB_PATH}",
    echo=False,
    future=True,
)

# Classe base para os modelos ORM
Base = declarative_base()

# Fábrica de sessões
SessionLocal = sessionmaker(bind=Engine, autoflush=False, autocommit=False)


def init_db() -> None:
    """Inicializa o banco de dados e garante o cadastro do tipo de relatório Ultrassom - US."""
    from models import Base, TipoRelatorio  # noqa: F401

    # Cria todas as tabelas
    Base.metadata.create_all(Engine)

    # Garante o cadastro do tipo de relatório Ultrassom
    from sqlalchemy import select
    session = SessionLocal()
    try:
        stmt = select(TipoRelatorio).where(TipoRelatorio.nome == "Ultrassom - US")
        existing = session.execute(stmt).scalar_one_or_none()
        if not existing:
            schema = {
                "campos": [
                    {"nome": "NUMRELATORIO", "rotulo": "Número do Relatório", "tipo": "texto"},
                    {"nome": "EMPRESA", "rotulo": "Empresa", "tipo": "texto"},
                    {"nome": "ENDERECO", "rotulo": "Endereço", "tipo": "texto"},
                    {"nome": "BAIRRO", "rotulo": "Bairro", "tipo": "texto"},
                    {"nome": "CIDADE", "rotulo": "Cidade", "tipo": "texto"},
                    {"nome": "ESTADO", "rotulo": "Estado", "tipo": "texto"},
                    {"nome": "CEP", "rotulo": "CEP", "tipo": "texto"},
                    {"nome": "CONTATO", "rotulo": "Contato", "tipo": "texto"},
                    {"nome": "DDD", "rotulo": "DDD", "tipo": "texto"},
                    {"nome": "FONE", "rotulo": "Telefone", "tipo": "texto"},
                    {"nome": "EMAIL", "rotulo": "E-mail", "tipo": "texto"},
                    {"nome": "PECA_INSP", "rotulo": "Peça Ensaiada", "tipo": "texto"},
                    {"nome": "NUM_DESENHO", "rotulo": "Número da Ordem de Produção", "tipo": "texto"},
                    {"nome": "QUANTIDADE", "rotulo": "Quantidade", "tipo": "inteiro"},
                    {"nome": "LOCAL_INSP", "rotulo": "Local do Ensaio", "tipo": "texto"},
                    {"nome": "DATA_INSP", "rotulo": "Data do Ensaio", "tipo": "data"},
                    {"nome": "MATERIAL", "rotulo": "Material", "tipo": "texto"},
                    {"nome": "COND_SUPERFICIAL", "rotulo": "Condição da Superfície", "tipo": "texto"},
                    {"nome": "REGIAO_INSP", "rotulo": "Região Inspecionada", "tipo": "texto"},
                    {"nome": "ESPESSURA", "rotulo": "Espessura", "tipo": "texto"},
                    {"nome": "FOTO_1", "rotulo": "Foto da Capa", "tipo": "arquivo"},
                    {"nome": "FOTO_2", "rotulo": "Foto 2 (Ultrassom)", "tipo": "arquivo"},
                    {"nome": "FOTO_3", "rotulo": "Foto 3 (Ultrassom)", "tipo": "arquivo"},
                    {"nome": "DATA_INSP_EXTENSO", "rotulo": "Data por extenso", "tipo": "gerado"},
                ]
            }
            template_path = os.path.join("templates", "US_TEMPLATE.docx")
            tr = TipoRelatorio(
                nome="Ultrassom - US",
                descricao="Relatório de Ensaio por Ultrassom (US) - RL Metais",
                schema_json=json.dumps(schema, ensure_ascii=False, indent=2),
                template_path=template_path,
            )
            session.add(tr)
            session.commit()
    finally:
        session.close()


def get_session():
    """Retorna uma nova sessão de banco de dados."""
    return SessionLocal()
# garantir registro da capa
CAPA_TEMPLATE_PATH = os.path.join("templates", "CAPA_TEMPLATE.docx")