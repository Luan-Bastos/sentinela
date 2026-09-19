"""
Modelo de dados do Sentinela.

Reconstrução livre a partir de uma única tela real do sistema original
(Previsão Diária / escala do dia). As entidades Unidade, Pelotao,
PostoServico, Escala e Missao refletem o que aparecia nessa tela.
OrdemServico e as tabelas de apoio em Utilitário foram desenhadas do zero
para cobrir os módulos que só existiam como itens de menu na captura
original, sem uma tela de referência real.
"""
from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def agora_utc():
    """datetime UTC "naive" (sem tzinfo) — mantém consistência com o restante
    do app, que não trabalha com fusos horários."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Unidade(db.Model):
    """Subunidade (SU) — ex.: 'Bia C Sl', '1ª Bia O Sl', 'PO'."""

    __tablename__ = "unidades"

    id = db.Column(db.Integer, primary_key=True)
    sigla = db.Column(db.String(30), nullable=False, unique=True)
    nome = db.Column(db.String(120), nullable=False)

    pelotoes = db.relationship("Pelotao", backref="unidade", lazy=True)
    militares = db.relationship("Militar", backref="unidade", lazy=True)

    def __repr__(self):
        return f"<Unidade {self.sigla}>"


class Pelotao(db.Model):
    """Pelotão / Seção dentro de uma unidade."""

    __tablename__ = "pelotoes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    unidade_id = db.Column(db.Integer, db.ForeignKey("unidades.id"), nullable=False)

    militares = db.relationship("Militar", backref="pelotao", lazy=True)

    def __repr__(self):
        return f"<Pelotao {self.nome}>"


POSTOS_GRADUACAO = [
    "Sd EP", "Sd EV", "Cb EP", "Cb EV", "3º Sgt", "2º Sgt", "1º Sgt",
    "Subten", "Asp", "2º Ten", "1º Ten", "Cap", "Maj", "Ten Cel", "Cel",
]


class Militar(UserMixin, db.Model):
    """Uma pessoa cadastrada no sistema — é também o usuário de login."""

    __tablename__ = "militares"

    id = db.Column(db.Integer, primary_key=True)
    posto_grad = db.Column(db.String(20), nullable=False)
    numero = db.Column(db.String(10), nullable=False)  # nº de identificação, ex.: "0451"
    nome_guerra = db.Column(db.String(60), nullable=False)
    nome_completo = db.Column(db.String(150), nullable=False)
    cargo = db.Column(db.String(80))

    unidade_id = db.Column(db.Integer, db.ForeignKey("unidades.id"), nullable=False)
    pelotao_id = db.Column(db.Integer, db.ForeignKey("pelotoes.id"), nullable=True)

    username = db.Column(db.String(40), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, senha):
        self.password_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.password_hash, senha)

    @property
    def identificacao(self):
        """Ex.: 'Sd EP 0451 SILVA' — como o nome aparece nas escalas."""
        return f"{self.posto_grad} {self.numero} {self.nome_guerra.upper()}"

    def __repr__(self):
        return f"<Militar {self.identificacao}>"


class PostoServico(db.Model):
    """Catálogo de postos de serviço (ex.: 'Gd Paiol', 'Sentinela')."""

    __tablename__ = "postos_servico"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(80), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # Externo / Interno
    contingente = db.Column(db.Integer, default=0)  # nº de militares aptos a esse posto
    ativo = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<PostoServico {self.nome} ({self.tipo})>"


class Escala(db.Model):
    """Um militar escalado em um posto, em uma data específica."""

    __tablename__ = "escalas"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, index=True)
    posto_id = db.Column(db.Integer, db.ForeignKey("postos_servico.id"), nullable=False)
    militar_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=False)
    responsavel_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=True)

    escalado_em = db.Column(db.DateTime, default=agora_utc)
    notificado_em = db.Column(db.DateTime, nullable=True)
    confirmado_em = db.Column(db.DateTime, nullable=True)

    posto = db.relationship("PostoServico")
    militar = db.relationship("Militar", foreign_keys=[militar_id])
    responsavel = db.relationship("Militar", foreign_keys=[responsavel_id])

    @property
    def gdh_escalado(self):
        return _para_gdh(self.escalado_em)

    @property
    def gdh_notificado(self):
        return _para_gdh(self.notificado_em)

    @property
    def gdh_confirmado(self):
        return _para_gdh(self.confirmado_em)

    def __repr__(self):
        return f"<Escala {self.posto.nome if self.posto else '?'} {self.data}>"


class Missao(db.Model):
    """Missões do dia — tabela separada das escalas de posto fixo."""

    __tablename__ = "missoes"

    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False, index=True)
    local = db.Column(db.String(150), nullable=False)
    militar_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=False)
    ciente_em = db.Column(db.DateTime, nullable=True)

    militar = db.relationship("Militar")


class OrdemServico(db.Model):
    """Ordem de Serviço (OS) — comunicado/documento oficial do dia."""

    __tablename__ = "ordens_servico"

    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(20), nullable=False)
    data = db.Column(db.Date, nullable=False, index=True)
    assunto = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    publicado_por_id = db.Column(db.Integer, db.ForeignKey("militares.id"), nullable=False)
    criado_em = db.Column(db.DateTime, default=agora_utc)

    publicado_por = db.relationship("Militar")


def _para_gdh(dt):
    """Formata um datetime no padrão militar GDH: DDHHMMMESAA (ex.: 211736AGO25)."""
    if not dt:
        return None
    meses = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN",
             "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    return f"{dt.day:02d}{dt.hour:02d}{dt.minute:02d}{meses[dt.month - 1]}{dt.year % 100:02d}"
