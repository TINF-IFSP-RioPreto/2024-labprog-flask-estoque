from urllib.parse import urlsplit

import pyotp
from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from markupsafe import Markup

from src.forms.auth import AskToResetPassword, LoginForm, ProfileForm, Read2FACodeForm, \
    RegistrationForm, SetNewPasswordForm
from src.models.usuario import User
from src.modules import db
from src.utils import timestamp

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
        if not usuario.email_validado:
            flash(Markup(f"Email ainda não confirmado. Precisa de um <a href=\""
                         f"{url_for('auth.revalida_email', user_id=usuario.id)}\""
                         f">novo email de confirmacao</a>?"), category='warning')
            return redirect(url_for('auth.login'))
        if usuario.usa_2fa:
            flash(f"Conclua o login para o usuário {usuario.email} digitando o "
                  f"código do segundo fator de autenticação", category='info')
            return redirect(url_for('auth.get2fa',
                                    user_id=usuario.id,
                                    remember_me=bool(form.remember_me.data),
                                    next=request.args.get('next')))
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


@bp.route('/revalida_email/<uuid:user_id>')
def revalida_email(user_id):
    usuario = User.get_by_id(user_id)
    if usuario:
        body = render_template('auth/email/reconfirmation-email.jinja2',
                               user=usuario,
                               token=usuario.create_jwt_token('validate_email'),
                               host=current_app.config.get('APP_BASE_URL'))
        if not usuario.send_email(subject="Revalide o seu email", body=body):
            current_app.logger.warning("Email de revalidação para o usuario %s não "
                                       "foi enviado", str(usuario.id))
        else:
            flash("Mensagem para validação do email enviada", category='info')
    next_page = request.args.get('next')
    if not next_page or urlsplit(next_page).netloc != '':
        next_page = url_for('index')
    return redirect(next_page)


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
    # token não é de reset_password
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
        flash(
            f"Se houver uma conta com o email {email}, uma mensagem será enviada com as "
            f"instruções para a troca da senha", category='info')
        if usuario:
            body = render_template('auth/email/password-reset-email.jinja2',
                                   user=usuario,
                                   token=usuario.create_jwt_token('reset_password'),
                                   host=current_app.config.get('APP_BASE_URL'))
            if not usuario.send_email(subject="Altere a sua senha", body=body):
                current_app.logger.warning("Email de reset de senha para o usuario %s "
                                           "não enviado", email)
            return redirect(url_for('auth.login'))
        current_app.logger.warning("Pedido de reset de senha para usuário inexistente (%s)",
                                   email)
        return redirect(url_for('auth.login'))
    return render_template('render_simple_slim_form.jinja2',
                           title="Esqueci minha senha",
                           form=form)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        usuario = User()
        usuario.nome = form.nome.data
        usuario.email = form.email.data
        usuario.set_password(form.password.data)
        usuario.email_validado = False
        usuario.ativo = True
        db.session.add(usuario)
        db.session.flush()
        db.session.refresh(usuario)
        body = render_template('auth/email/confirmation-email.jinja2',
                               user=usuario,
                               token=usuario.create_jwt_token('validate_email'),
                               host=current_app.config.get('APP_BASE_URL'))
        if not usuario.send_email(subject="Ative a sua conta",
                                  body=body):
            current_app.logger.warning("Email de ativação para o usuario %s não "
                                       "enviado", str(usuario.id))
        db.session.commit()
        flash("Cadastro efetuado com sucesso. Confirme o seu email antes de logar "
              "no sistema", category='success')
        return redirect(url_for('auth.login'))

    return render_template('render_simple_form.jinja2',
                           title="Cadastro de usuário",
                           form=form)


@bp.route('/valida_email/<token>')
def valida_email(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    usuario, action = User.verify_jwt_token(token)
    if usuario and not usuario.email_validado and action == 'validate_email':
        usuario.email_validado = True
        usuario.dta_validacao_email = timestamp()
        flash(f"Email {usuario.email} validado!", category='success')
        db.session.commit()
        return redirect(url_for('auth.login'))
    flash("Token inválido", category='warning')
    return redirect(url_for('auth.login'))


@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.nome = form.nome.data
        if form.usa_2fa.data:
            if not current_user.usa_2fa:
                current_user.otp_secret = pyotp.random_base32()
                db.session.commit()
                flash("Alterações efetuadas. Conclua a ativação do segundo fator de"
                      " autenticação", category='info')
                return redirect(url_for('auth.enable_2fa'))
        else:
            if current_user.usa_2fa:
                current_user.usa_2fa = False
                current_user.otp_secret = None
                current_user.ultimo_otp = None
                current_user.dta_ativacao_2fa = None
                body = render_template('auth/email/disable-2fa.jinja2',
                                       user=current_user)
                if not current_user.send_email(
                        subject="Desativação do segundo fator de autenticação",
                        body=body):
                    current_app.logger.warning("Email de desativação do 2FA para o usuario "
                                               "%s não foi enviado", str(current_user.id))
        db.session.commit()
        flash("Alterações efetuas", category='success')
    return render_template('auth/user.jinja2',
                           title="Perfil do usuário",
                           form=form)


@bp.route('enable_2fa', methods=['GET', 'POST'])
@login_required
def enable_2fa():
    if current_user.usa_2fa:
        flash("Configuração já efetuada. Para alterar, desative e reative o uso do "
              "segundo fator de autenticação", category='info')
        return redirect(url_for('auth.profile'))

    form = Read2FACodeForm()
    if request.method == 'POST' and form.is_submitted():
        if current_user.verify_totp(form.codigo.data):
            # noinspection PyBroadException
            try:
                current_user.usa_2fa = True
                current_user.dta_ativacao_2fa = timestamp()
                current_user.ultimo_otp = form.codigo.data
                db.session.commit()
                flash("Segundo fator de autenticação ativado", category='success')
                return redirect(url_for('auth.profile'))
            except Exception:
                current_user.usa_2fa = False
                current_user.otp_secret = None
                current_user.ultimo_otp = None
                current_user.dta_ativacao_2fa = None
                db.session.commit()
                flash("Problema na ativação do segundo fator de autenticação",
                      category='danger')
                return redirect(url_for('auth.profile'))
        else:  # codigo errado
            flash('O código informado está incorreto. Tente novamente.',
                  category='warning')
            return redirect(url_for('auth.enable_2fa'))

    return render_template('auth/enable_2fa.jinja2',
                           title="Ativação do segundo fator de autenticação",
                           form=form,
                           imagem=current_user.get_b64encoded_qr_totp_uri,
                           token=current_user.otp_secret_formatted)


@bp.route('/get2fa/<uuid:user_id>', methods=['GET', 'POST'])
def get2fa(user_id):
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    remember_me = request.args.get('remember_me')
    next_page = request.args.get('next')

    form = Read2FACodeForm()

    if form.validate_on_submit():
        usuario = User.get_by_id(user_id)

        if usuario is None or not usuario.usa_2fa:
            return redirect(url_for('auth.login'))

        token = str(form.codigo.data)
        if usuario.verify_totp(token):
            login_user(usuario, remember=bool(remember_me))
            usuario.ultimo_otp = token
            db.session.commit()
            if not next_page or urlsplit(next_page).netloc != '':
                next_page = url_for('index')
            flash(f"Usuario {usuario.email} logado", category='success')
            return redirect(next_page)
        # Codigo errado
        flash("Código incorreto. Tente novamente", category='warning')

    return render_template('render_simple_slim_form.jinja2',
                           title="Segundo fator de autenticação",
                           form=form)
