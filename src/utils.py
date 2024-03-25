import datetime
from pathlib import Path

import pytz


def existe_esquema(app) -> bool:
    # Se estivéssmos com um SGBD, poderíamos consultar os metadados para ver
    # se o esquema do banco existe, com algo como (mariaDB)
    # SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = '<nome>'
    # No caso do SQLite, vamos apenas verificar se existe ou não o arquivo no
    # sistema de arquivos
    arquivo = Path(app.instance_path) / Path(app.config.get('SQLITE_DB_NAME', 'application_db.sqlite3'))
    return arquivo.is_file()
    # configurar o alembic
    #   alembic init instance/migrations
    # configurar o alembic.ini
    #   [alembic]
    #   sqlalchemy.url = sqlite+pysqlite:///instance/application_db.sqlite3
    # ajustar o env.py
    #   from src.modules import Base
    #   target_metadata = Base.metada


def timestamp():
    return datetime.datetime.now(tz=pytz.timezone('UTC'))


# Formatando as datas para horário local
# https://stackoverflow.com/q/65359968
def as_localtime(data_em_utc) -> str | datetime.date:
    from flask import current_app
    if not data_em_utc:
        return "Sem data"
    tz = current_app.config.get('TIMEZONE', 'UTC')
    try:
        formato = '%Y-%m-%d, %H:%M'
        utc = pytz.timezone('UTC')
        data_em_utc = utc.localize(data_em_utc)
        data_local = data_em_utc.astimezone(pytz.timezone(tz))
        return data_local.strftime(formato)
    except Exception as e:
        current_app.logger.warning("as_localtime: Exception %s" % (e))
        return data_em_utc
