import json
import logging
import os
import sys

from flask import Flask, render_template

from src.modules import bootstrap, minify, db
from src.utils import existe_esquema


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

    with app.app_context():
        if not existe_esquema(app):
            app.logger.fatal("É necessário fazer a migração/upgrade do banco")
            sys.exit(1)

    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index.jinja',
                               title="Página principal")

    return app
