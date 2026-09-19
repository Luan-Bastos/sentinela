import calendar
from datetime import date, datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Escala, Militar, Missao, Pelotao, PostoServico, Unidade, agora_utc, db

servicos_bp = Blueprint("servicos", __name__)


def _data_da_query():
    bruto = request.args.get("data")
    if bruto:
        try:
            return datetime.strptime(bruto, "%Y-%m-%d").date()
        except ValueError:
            pass
    return date.today()


@servicos_bp.route("/previsao")
@login_required
def previsao_diaria():
    dia = _data_da_query()
    unidade_id = request.args.get("unidade_id", type=int)
    pelotao_id = request.args.get("pelotao_id", type=int)
    responsavel_id = request.args.get("responsavel_id", type=int)

    query = Escala.query.filter_by(data=dia).join(Militar, Escala.militar_id == Militar.id)
    if unidade_id:
        query = query.filter(Militar.unidade_id == unidade_id)
    if pelotao_id:
        query = query.filter(Militar.pelotao_id == pelotao_id)
    if responsavel_id:
        query = query.filter(Escala.responsavel_id == responsavel_id)

    escalas = query.join(PostoServico).order_by(PostoServico.tipo.desc(), PostoServico.nome).all()
    externo = [e for e in escalas if e.posto.tipo == "Externo"]
    interno = [e for e in escalas if e.posto.tipo == "Interno"]
    missoes = Missao.query.filter_by(data=dia).all()

    cal = calendar.Calendar(firstweekday=6)  # domingo primeiro, como no calendário original
    semanas = cal.monthdatescalendar(dia.year, dia.month)

    primeiro_dia_mes = dia.replace(day=1)
    mes_anterior = (primeiro_dia_mes - timedelta(days=1)).replace(day=1)
    ultimo_dia_mes = calendar.monthrange(dia.year, dia.month)[1]
    mes_seguinte = (dia.replace(day=ultimo_dia_mes) + timedelta(days=1)).replace(day=1)

    return render_template(
        "servicos/previsao_diaria.html",
        dia=dia,
        externo=externo,
        interno=interno,
        missoes=missoes,
        semanas=semanas,
        mes_anterior=mes_anterior,
        mes_seguinte=mes_seguinte,
        unidades=Unidade.query.order_by(Unidade.sigla).all(),
        pelotoes=Pelotao.query.order_by(Pelotao.nome).all(),
        responsaveis=Militar.query.filter_by(ativo=True).order_by(Militar.nome_guerra).all(),
        filtro_unidade=unidade_id,
        filtro_pelotao=pelotao_id,
        filtro_responsavel=responsavel_id,
    )


@servicos_bp.route("/previsao/gerar", methods=["POST"])
@login_required
def gerar_previsao():
    """Rascunho automático: para cada posto ativo sem escala na data, escolhe
    o militar apto (mesma unidade do posto, quando informado) que está há
    mais tempo sem ser escalado — um rodízio simples de justiça de fila."""
    dia = _data_da_query()
    ja_escalados = {e.posto_id for e in Escala.query.filter_by(data=dia).all()}
    postos_pendentes = PostoServico.query.filter_by(ativo=True).filter(
        ~PostoServico.id.in_(ja_escalados) if ja_escalados else True
    ).all()

    criadas = 0
    for posto in postos_pendentes:
        ultimo_por_militar = (
            db.session.query(Escala.militar_id, db.func.max(Escala.data))
            .group_by(Escala.militar_id)
            .all()
        )
        ultima_data = {m: d for m, d in ultimo_por_militar}
        candidatos = Militar.query.filter_by(ativo=True).all()
        if not candidatos:
            continue
        escolhido = min(candidatos, key=lambda m: ultima_data.get(m.id, date.min))
        db.session.add(Escala(data=dia, posto_id=posto.id, militar_id=escolhido.id))
        criadas += 1

    db.session.commit()
    if criadas:
        flash(f"Previsão gerada: {criadas} posto(s) preenchido(s) automaticamente.", "sucesso")
    else:
        flash("Não havia postos pendentes para gerar.", "aviso")
    return redirect(url_for("servicos.previsao_diaria", data=dia.isoformat()))


@servicos_bp.route("/escala/nova", methods=["GET", "POST"])
@login_required
def escala_nova():
    dia = _data_da_query()
    if request.method == "POST":
        db.session.add(Escala(
            data=dia,
            posto_id=int(request.form["posto_id"]),
            militar_id=int(request.form["militar_id"]),
            responsavel_id=int(request.form.get("responsavel_id")) if request.form.get("responsavel_id") else None,
        ))
        db.session.commit()
        flash("Escala adicionada.", "sucesso")
        return redirect(url_for("servicos.previsao_diaria", data=dia.isoformat()))

    return render_template(
        "servicos/escala_form.html",
        dia=dia,
        escala=None,
        postos=PostoServico.query.filter_by(ativo=True).order_by(PostoServico.nome).all(),
        militares=Militar.query.filter_by(ativo=True).order_by(Militar.nome_guerra).all(),
    )


@servicos_bp.route("/escala/<int:escala_id>/editar", methods=["GET", "POST"])
@login_required
def escala_editar(escala_id):
    escala = Escala.query.get_or_404(escala_id)
    if request.method == "POST":
        escala.posto_id = int(request.form["posto_id"])
        escala.militar_id = int(request.form["militar_id"])
        escala.responsavel_id = int(request.form.get("responsavel_id")) if request.form.get("responsavel_id") else None
        db.session.commit()
        flash("Escala atualizada.", "sucesso")
        return redirect(url_for("servicos.previsao_diaria", data=escala.data.isoformat()))

    return render_template(
        "servicos/escala_form.html",
        dia=escala.data,
        escala=escala,
        postos=PostoServico.query.filter_by(ativo=True).order_by(PostoServico.nome).all(),
        militares=Militar.query.filter_by(ativo=True).order_by(Militar.nome_guerra).all(),
    )


@servicos_bp.route("/escala/<int:escala_id>/excluir", methods=["POST"])
@login_required
def escala_excluir(escala_id):
    escala = Escala.query.get_or_404(escala_id)
    dia = escala.data
    db.session.delete(escala)
    db.session.commit()
    flash("Escala removida.", "sucesso")
    return redirect(url_for("servicos.previsao_diaria", data=dia.isoformat()))


@servicos_bp.route("/escala/<int:escala_id>/notificar", methods=["POST"])
@login_required
def escala_notificar(escala_id):
    escala = Escala.query.get_or_404(escala_id)
    escala.notificado_em = agora_utc()
    db.session.commit()
    return redirect(url_for("servicos.previsao_diaria", data=escala.data.isoformat()))


@servicos_bp.route("/escala/<int:escala_id>/confirmar", methods=["POST"])
@login_required
def escala_confirmar(escala_id):
    escala = Escala.query.get_or_404(escala_id)
    escala.confirmado_em = agora_utc()
    db.session.commit()
    return redirect(url_for("servicos.previsao_diaria", data=escala.data.isoformat()))


@servicos_bp.route("/missao/nova", methods=["GET", "POST"])
@login_required
def missao_nova():
    dia = _data_da_query()
    if request.method == "POST":
        db.session.add(Missao(
            data=dia,
            local=request.form["local"].strip(),
            militar_id=int(request.form["militar_id"]),
        ))
        db.session.commit()
        flash("Missão adicionada.", "sucesso")
        return redirect(url_for("servicos.previsao_diaria", data=dia.isoformat()))

    return render_template(
        "servicos/missao_form.html",
        dia=dia,
        militares=Militar.query.filter_by(ativo=True).order_by(Militar.nome_guerra).all(),
    )


@servicos_bp.route("/missao/<int:missao_id>/excluir", methods=["POST"])
@login_required
def missao_excluir(missao_id):
    missao = Missao.query.get_or_404(missao_id)
    dia = missao.data
    db.session.delete(missao)
    db.session.commit()
    return redirect(url_for("servicos.previsao_diaria", data=dia.isoformat()))
