from datetime import date

from flask import Blueprint, render_template
from flask_login import login_required

from app.models import Escala, Militar, OrdemServico

principal_bp = Blueprint("principal", __name__)


@principal_bp.route("/")
@login_required
def index():
    hoje = date.today()
    escaladas_hoje = Escala.query.filter_by(data=hoje).count()
    total_militares = Militar.query.filter_by(ativo=True).count()
    ultimas_os = (
        OrdemServico.query.order_by(OrdemServico.data.desc()).limit(5).all()
    )
    return render_template(
        "principal.html",
        escaladas_hoje=escaladas_hoje,
        total_militares=total_militares,
        ultimas_os=ultimas_os,
    )


@principal_bp.route("/sobre")
@login_required
def sobre():
    return render_template("sobre.html")
