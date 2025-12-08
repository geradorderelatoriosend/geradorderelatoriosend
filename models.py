
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from database import Base


class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(Integer, primary_key=True)
    razao_social = Column(String, nullable=False)
    contato = Column(String, nullable=True)
    cnpj = Column(String, nullable=True, unique=False)
    ie = Column(String, nullable=True)

    rua = Column(String, nullable=True)
    numero = Column(String, nullable=True)
    bairro = Column(String, nullable=True)
    cidade = Column(String, nullable=True)
    uf = Column(String, nullable=True)
    cep = Column(String, nullable=True)

    ddd = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    email = Column(String, nullable=True)

    ultima_inspecao = Column(Date, nullable=True)

    entradas_relatorio = relationship("EntradaRelatorio", back_populates="cliente")

    def __repr__(self) -> str:
        return f"<Cliente(id={self.id}, razao_social='{self.razao_social}')>"


class TipoRelatorio(Base):
    __tablename__ = "tipos_relatorio"

    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False, unique=True)
    descricao = Column(String, nullable=True)
    schema_json = Column(Text, nullable=False)
    template_path = Column(String, nullable=True)

    entradas = relationship("EntradaRelatorio", back_populates="tipo_relatorio")

    def __repr__(self) -> str:
        return f"<TipoRelatorio(id={self.id}, nome='{self.nome}')>"


class EntradaRelatorio(Base):
    __tablename__ = "entradas_relatorio"

    id = Column(Integer, primary_key=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=True)
    tipo_relatorio_id = Column(Integer, ForeignKey("tipos_relatorio.id"), nullable=False)

    relatorio_num = Column(String, nullable=True)
    titulo_personalizado = Column(String, nullable=True)
    dados_json = Column(Text, nullable=True)
    caminho_arquivo_gerado = Column(String, nullable=True)
    criado_em = Column(DateTime, default=datetime.now)

    cliente = relationship("Cliente", back_populates="entradas_relatorio")
    tipo_relatorio = relationship("TipoRelatorio", back_populates="entradas")

    def __repr__(self) -> str:
        return f"<EntradaRelatorio(id={self.id}, num='{self.relatorio_num}', tipo_id={self.tipo_relatorio_id})>"
