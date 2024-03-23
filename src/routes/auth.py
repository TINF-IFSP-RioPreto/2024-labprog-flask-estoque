from urllib.parse import urlsplit

from flask import Blueprint, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_user, login_required, logout_user

from src.models.usuario import User
from src.modules import db
from src.forms.auth import LoginForm

bp = Blueprint('auth', __name__, url_prefix='/admin/user')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        usuario = User.get_by_email(form.email.data)

        if usuario is None or not usuario.check_password(form.password.data):
            flash("Email ou senha incorretos", category='warning')
            return redirect(url_for('auth.login'))
        if not usuario.ativo:
            flash("Usuário está impedido de acessar o sistema. Procure um adminstrador",
                  category='danger')
            return redirect(url_for('auth.login'))
        login_user(usuario, remember=form.remember_me.data)
        db.session.commit()
        flash(f"Usuario {usuario.email} logado", category='success')
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)

    return render_template('auth/login.jinja2',
                           title="Dados de acesso",
                           form=form)


@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Sessão encerrada", category='success')
    return redirect(url_for('index'))
