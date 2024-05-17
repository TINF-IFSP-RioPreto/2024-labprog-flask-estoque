import sqlalchemy as sa
from flask import Blueprint, render_template

from src.models.categoria import Categoria
from src.modules import db

bp = Blueprint('categorias', __name__, url_prefix='/categoria')


@bp.route('/lista', methods=['GET'])
@bp.route('/', methods=['GET'])
def lista():
    sentenca = sa.select(Categoria)
    sentenca = sentenca.order_by(Categoria.nome)

    rset = db.session.execute(sentenca).scalars()

    return render_template('categoria/lista.jinja2',
                           title="Lista de categorias",
                           rset=rset)
