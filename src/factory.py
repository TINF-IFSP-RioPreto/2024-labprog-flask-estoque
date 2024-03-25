import json
import logging
import os
import sys
import uuid

from flask import Flask, render_template
from flask_login import user_logged_in

import src.routes.auth
from src.models.usuario import User
from src.modules import bootstrap, minify, db, csrf, login, mail
from src.utils import existe_esquema, timestamp, as_localtime


def create_app(config_filename: str = 'config.dev.json') -> Flask:
    app = Flask(__name__,
                instance_relative_config=True,
                static_folder='static',
                template_folder='templates')

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.logger.setLevel(logging.DEBUG)

    app.logger.debug("Configurando a aplicação a partir do arquivo '%s'" % (config_filename))
    try:
        app.config.from_file(config_filename, load=json.load)
    except FileNotFoundError:
        app.logger.fatal("O arquivo de configuração '%s' não existe" % (config_filename))
        sys.exit(1)

    app.logger.debug("Registrando as extensões")
    bootstrap.init_app(app)
    minificar = app.config.get("MINIFY", False)
    if minificar:
        minify.init_app(app)
    db.init_app(app)
    csrf.init_app(app)
    login.init_app(app)
    login.login_view = 'auth.login'
    login.login_message = "É necessário estar logado para acessar esta funcionalidade"
    login.login_message_category = 'warning'
    login.session_protection = 'strong'
    mail.init_app(app)

    @login.user_loader
    def load_user(user_id):
        try:
            auth_id = uuid.UUID(str(user_id))
        except ValueError:
            return None
        return User.get_by_id(auth_id)

    @user_logged_in.connect_via(app)
    def update_login_details(sender_app, user):
        agora = timestamp()

        login_anterior, login_atual = user.dta_acesso_atual, agora
        user.dta_acesso_atual = login_atual
        user.dta_ultimo_acesso = login_anterior or login_atual

    with app.app_context():
        if not existe_esquema(app):
            app.logger.fatal("É necessário fazer a migração/upgrade do banco")
            sys.exit(1)

        if User.is_empty():
            usuarios = [
                {'nome': "Administrador",
                 'email': app.config.get('DEFAULT_ADMIN_EMAIL', 'admin@admin.com.br'),
                 'senha': app.config.get('DEFAULT_ADMIN_PASSWORD', "123456"),
                 'ativo': True
                 },
                {
                    'nome': "Usuário",
                    'email': app.config.get('DEFAULT_USER_EMAIL', 'user@user.com.br'),
                    'senha': app.config.get('DEFAULT_USER_PASSWORD', "123"),
                    'ativo': False
                }
            ]
            for usuario in usuarios:
                app.logger.info("Adicionando usuário (%s:%s)" % (usuario.get('email'), usuario.get('senha')))
                novo_usuario = User()
                novo_usuario.nome = usuario.get('nome')
                novo_usuario.email = usuario.get('email')
                novo_usuario.set_password(usuario.get('senha'))
                novo_usuario.email_validado = True
                novo_usuario.ativo = usuario.get('ativo')
                novo_usuario.dta_validacao_email = timestamp()
                db.session.add(novo_usuario)
                db.session.commit()

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index.jinja',
                               title="Página principal")

    app.logger.debug("Registrando as blueprints")
    app.register_blueprint(src.routes.auth.bp)

    # Formatando as datas para horário local
    # https://stackoverflow.com/q/65359968
    app.jinja_env.filters['as_localtime'] = as_localtime

    return app
