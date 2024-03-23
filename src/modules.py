from flask_bootstrap import Bootstrap5
from flask_minify import Minify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # Se houver atributos comuns a todas as classes,
    # eles seriam adicionados aqui
    pass


bootstrap = Bootstrap5()
minify = Minify()
db = SQLAlchemy(model_class=Base,
                disable_autonaming=True)
