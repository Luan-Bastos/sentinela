from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Militar, Pelotao, Unidade, POSTOS_GRADUACAO, db

pessoal_bp = Blueprint("pessoal", __name__)


@pessoal_bp.route("/militares")
@login_required
def militares_lista():
    q = request.args.get("q", "").strip()
    query = Militar.query
    if q:
        like = f"%{q}%"
        query = query.filter(
            db.or_(Militar.nome_guerra.ilike(like), Militar.numero.ilike(like))
        )
    militares = query.order_by(Militar.nome_guerra).all()
    return render_template("pessoal/militares_lista.html", militares=militares, q=q)


@pessoal_bp.route("/militares/novo", methods=["GET", "POST"])
@login_required
def militares_novo():
    return _form_militar(militar=None)


@pessoal_bp.route("/militares/<int:militar_id>/editar", methods=["GET", "POST"])
@login_required
def militares_editar(militar_id):
    militar = Militar.query.get_or_404(militar_id)
    return _form_militar(militar=militar)


@pessoal_bp.route("/militares/<int:militar_id>/excluir", methods=["POST"])
@login_required
def militares_excluir(militar_id):
    militar = Militar.query.get_or_404(militar_id)
    militar.ativo = False
    db.session.commit()
    flash(f"{militar.identificacao} foi desativado.", "sucesso")
    return redirect(url_for("pessoal.militares_lista"))


def _form_militar(militar):
    unidades = Unidade.query.order_by(Unidade.sigla).all()
    pelotoes = Pelotao.query.order_by(Pelotao.nome).all()

    if request.method == "POST":
        dados = request.form
        if militar is None:
            militar = Militar()
            militar.username = dados["username"].strip()
            militar.set_password(dados.get("senha") or "123456")
            db.session.add(militar)

        militar.posto_grad = dados["posto_grad"]
        militar.numero = dados["numero"].strip()
        militar.nome_guerra = dados["nome_guerra"].strip()
        militar.nome_completo = dados["nome_completo"].strip()
        militar.cargo = dados.get("cargo", "").strip()
        militar.unidade_id = int(dados["unidade_id"])
        militar.pelotao_id = int(dados["pelotao_id"]) if dados.get("pelotao_id") else None

        db.session.commit()
        flash(f"{militar.identificacao} foi salvo.", "sucesso")
        return redirect(url_for("pessoal.militares_lista"))

    return render_template(
        "pessoal/militares_form.html",
        militar=militar,
        unidades=unidades,
        pelotoes=pelotoes,
        postos_graduacao=POSTOS_GRADUACAO,
    )
