from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Pelotao, PostoServico, Unidade, db

utilitario_bp = Blueprint("utilitario", __name__)


# --- Unidades ---------------------------------------------------------

@utilitario_bp.route("/unidades", methods=["GET", "POST"])
@login_required
def unidades():
    if request.method == "POST":
        db.session.add(Unidade(
            sigla=request.form["sigla"].strip(),
            nome=request.form["nome"].strip(),
        ))
        db.session.commit()
        flash("Unidade cadastrada.", "sucesso")
        return redirect(url_for("utilitario.unidades"))

    return render_template("utilitario/unidades.html", unidades=Unidade.query.order_by(Unidade.sigla).all())


@utilitario_bp.route("/unidades/<int:unidade_id>/excluir", methods=["POST"])
@login_required
def unidade_excluir(unidade_id):
    unidade = Unidade.query.get_or_404(unidade_id)
    if unidade.militares:
        flash("Essa unidade tem militares vinculados e não pode ser removida.", "erro")
    else:
        db.session.delete(unidade)
        db.session.commit()
        flash("Unidade removida.", "sucesso")
    return redirect(url_for("utilitario.unidades"))


# --- Pelotões / Seções --------------------------------------------------

@utilitario_bp.route("/pelotoes", methods=["GET", "POST"])
@login_required
def pelotoes():
    if request.method == "POST":
        db.session.add(Pelotao(
            nome=request.form["nome"].strip(),
            unidade_id=int(request.form["unidade_id"]),
        ))
        db.session.commit()
        flash("Pelotão/Seção cadastrado.", "sucesso")
        return redirect(url_for("utilitario.pelotoes"))

    return render_template(
        "utilitario/pelotoes.html",
        pelotoes=Pelotao.query.order_by(Pelotao.nome).all(),
        unidades=Unidade.query.order_by(Unidade.sigla).all(),
    )


@utilitario_bp.route("/pelotoes/<int:pelotao_id>/excluir", methods=["POST"])
@login_required
def pelotao_excluir(pelotao_id):
    pelotao = Pelotao.query.get_or_404(pelotao_id)
    if pelotao.militares:
        flash("Esse pelotão/seção tem militares vinculados e não pode ser removido.", "erro")
    else:
        db.session.delete(pelotao)
        db.session.commit()
        flash("Pelotão/Seção removido.", "sucesso")
    return redirect(url_for("utilitario.pelotoes"))


# --- Postos de serviço ----------------------------------------------------

@utilitario_bp.route("/postos", methods=["GET", "POST"])
@login_required
def postos():
    if request.method == "POST":
        db.session.add(PostoServico(
            nome=request.form["nome"].strip(),
            tipo=request.form["tipo"],
            contingente=int(request.form.get("contingente") or 0),
        ))
        db.session.commit()
        flash("Posto de serviço cadastrado.", "sucesso")
        return redirect(url_for("utilitario.postos"))

    return render_template("utilitario/postos.html", postos=PostoServico.query.order_by(PostoServico.tipo, PostoServico.nome).all())


@utilitario_bp.route("/postos/<int:posto_id>/alternar", methods=["POST"])
@login_required
def posto_alternar(posto_id):
    posto = PostoServico.query.get_or_404(posto_id)
    posto.ativo = not posto.ativo
    db.session.commit()
    return redirect(url_for("utilitario.postos"))
