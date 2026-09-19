from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.models import Militar

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("principal.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        senha = request.form.get("senha", "")

        militar = Militar.query.filter_by(username=username).first()
        if militar and militar.ativo and militar.check_password(senha):
            login_user(militar)
            destino = request.args.get("next") or url_for("principal.index")
            return redirect(destino)

        flash("Usuário ou senha inválidos.", "erro")

    return render_template("login.html")


@auth_bp.route("/logoff")
@login_required
def logoff():
    logout_user()
    return redirect(url_for("auth.login"))
