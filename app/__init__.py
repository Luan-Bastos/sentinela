import os

from flask import Flask
from flask_login import LoginManager

from app.models import db, Militar

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para continuar."
login_manager.login_message_category = "aviso"


def _database_uri(app):
    """Usa DATABASE_URL do ambiente (Render/Heroku etc.) quando existir;
    senão cai para o SQLite local, do jeito que já funcionava."""
    url = os.environ.get("DATABASE_URL")
    if url:
        # Alguns provedores ainda entregam "postgres://" — o SQLAlchemy 2.x
        # exige o prefixo "postgresql://".
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return "sqlite:///" + os.path.join(app.instance_path, "sentinela.db")


def create_app(auto_seed=True):
    app = Flask(__name__, instance_relative_config=True)
    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "dev-sentinela-secret-troque-em-producao"),
        SQLALCHEMY_DATABASE_URI=_database_uri(app),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        db.create_all()
        if auto_seed and Militar.query.count() == 0:
            from seed import popular_dados
            popular_dados(recriar_tabelas=False)

    from app.auth import auth_bp
    from app.principal import principal_bp
    from app.pessoal import pessoal_bp
    from app.servicos import servicos_bp
    from app.utilitario import utilitario_bp
    from app.ordens import ordens_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(principal_bp)
    app.register_blueprint(pessoal_bp, url_prefix="/pessoal")
    app.register_blueprint(servicos_bp, url_prefix="/pessoal/servicos")
    app.register_blueprint(utilitario_bp, url_prefix="/utilitario")
    app.register_blueprint(ordens_bp, url_prefix="/os")

    @app.context_processor
    def inject_globals():
        from datetime import date
        return {"hoje": date.today()}

    return app


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Militar, int(user_id))
