from urllib.parse import urlsplit

import jwt
from flask import Blueprint, current_app, redirect, url_for, render_template, flash, request
from flask_login import current_user, login_user, login_required, logout_user
from flask_mailman import EmailMessage

from src.models.usuario import User
from src.modules import db
from src.forms.auth import ForgotPasswordForm, LoginForm, NewPasswordForm

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


@bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        flash("Não faz sentido dizer que esqueceu a senha estando logado...",
              category='warning')
        return redirect(url_for('index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        flash(f"Se houver uma conta com o email {form.email.data}, "
              f"você receberá um link para mudar a senha")

        usuario = User.get_by_email(form.email.data)
        if usuario is not None:
            # criar um token para o usuario mudar a senha
            payload = {"usuario": usuario.email_normalizado,
                       "operacao": "mudarsenha"}
            token = jwt.encode(payload,
                               current_app.config.get("SECRET_KEY"),
                               algorithm="HS256")
            current_app.logger.debug(token)
            link = 'http://127.0.0.1:5000/' + url_for("auth.new_password", token=token)
            # enviar o token por email
            body = render_template('email/forgot_password.jinja2',
                            nome=usuario.nome,
                            link=link)

            mensagem = EmailMessage(subject="Mudanca de senha",
                                    body=body,
                                    from_email="sistema@empresa.com.br",
                                    to=[usuario.email])
            mensagem.send()


        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.jinja2',
                           title="Esqueci minha senha",
                           form=form)


@bp.route('/new_password/<token>', methods=['GET', 'POST'])
def new_password(token):
    try:
        payload = jwt.decode(token,
                             key=current_app.config.get("SECRET_KEY"),
                             algorithms=['HS256'])
    except jwt.exceptions.PyJWTError:
        flash("Token invalido", category='danger')
        return redirect(url_for('index'))

    form = NewPasswordForm()
    if form.validate_on_submit():
        usuario = User.get_by_email(payload['usuario'])
        if usuario is None:
            flash("Usuario inexistente", category='danger')
            return redirect(url_for('index'))

        usuario.set_password(form.password.data)
        db.session.commit()
        flash(f"Senha para o usuario {payload['usuario']} alterada", category='success')
        return redirect(url_for('auth.login'))

    return render_template('auth/new_password.jinja2',
                           title="Criar nova senha",
                           form=form)
