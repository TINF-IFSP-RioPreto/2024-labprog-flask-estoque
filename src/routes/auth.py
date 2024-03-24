from urllib.parse import urlsplit

from flask import Blueprint, redirect, url_for, render_template, flash, request, current_app
from flask_login import current_user, login_user, login_required, logout_user

from src.models.usuario import User
from src.modules import db
from src.forms.auth import LoginForm, SetNewPasswordForm, AskToResetPassword

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

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    usuario, action = User.verify_jwt_token(token)
    if usuario is None:
        flash("Usuário inválido no token", category='warning')
        return redirect(url_for('index'))
    if action == 'reset_password':
        form = SetNewPasswordForm()
        if form.validate_on_submit():
            usuario.set_password(form.password.data)
            db.session.commit()
            flash("Sua senha foi redefinida com sucesso", category='success')
            return redirect(url_for('auth.login'))
        return render_template('render_simple_slim_form.jinja2',
                               title="Escolha uma nova senha",
                               form=form)
    else:
        flash("Token inválido para mudança de senha", category='warning')
        return redirect(url_for('index'))

@bp.route('/new_password', methods=['GET', 'POST'])
def new_password():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = AskToResetPassword()
    if form.validate_on_submit():
        email = form.email.data
        usuario = User.get_by_email(email)
        flash(f"Se houver uma conta com o email {email}, uma mensagem será enviada com as instruções "
              f"para a troca da senha", category='info')
        if usuario:
            body = render_template('auth/email/password-reset-email.jinja2',
                                   user=usuario,
                                   token=usuario.create_jwt_token('reset_password'),
                                   host=current_app.config.get('APP_BASE_URL'))
            if not usuario.send_email(subject="Altere a sua senha", body=body):
                current_app.logger.warning("Email de reset de senha para o usuario %s não enviado" % (email))
            return redirect(url_for('auth.login'))
        current_app.logger.warning("Pedido de reset de senha para usuário inexistente (%s)" % (email))
        return redirect(url_for('auth.login'))
    return render_template('render_simple_slim_form.jinja2',
                           title="Esqueci minha senha",
                           form=form)
