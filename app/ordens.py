from datetime import date, datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import OrdemServico, db

ordens_bp = Blueprint("ordens", __name__)


@ordens_bp.route("/")
@login_required
def lista():
    ordens = OrdemServico.query.order_by(OrdemServico.data.desc(), OrdemServico.id.desc()).all()
    return render_template("os/lista.html", ordens=ordens)


@ordens_bp.route("/nova", methods=["GET", "POST"])
@login_required
def nova():
    if request.method == "POST":
        bruto = request.form.get("data")
        data_os = datetime.strptime(bruto, "%Y-%m-%d").date() if bruto else date.today()
        db.session.add(OrdemServico(
            numero=request.form["numero"].strip(),
            data=data_os,
            assunto=request.form["assunto"].strip(),
            conteudo=request.form["conteudo"].strip(),
            publicado_por_id=current_user.id,
        ))
        db.session.commit()
        flash("Ordem de Serviço publicada.", "sucesso")
        return redirect(url_for("ordens.lista"))

    return render_template("os/form.html", os=None, hoje=date.today())


@ordens_bp.route("/<int:os_id>")
@login_required
def detalhe(os_id):
    ordem = OrdemServico.query.get_or_404(os_id)
    return render_template("os/detalhe.html", os=ordem)


@ordens_bp.route("/<int:os_id>/excluir", methods=["POST"])
@login_required
def excluir(os_id):
    ordem = OrdemServico.query.get_or_404(os_id)
    db.session.delete(ordem)
    db.session.commit()
    flash("Ordem de Serviço removida.", "sucesso")
    return redirect(url_for("ordens.lista"))
