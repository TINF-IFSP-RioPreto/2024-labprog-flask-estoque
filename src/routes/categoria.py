import sqlalchemy as sa
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from src.forms.categoria import NovoEditCategoriaForm
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


@bp.route('/novo', methods=['GET', 'POST'])
@login_required
def novo():
    form = NovoEditCategoriaForm()
    form.submit.label.text = "Adicionar"
    if form.validate_on_submit():
        categoria = Categoria()
        categoria.nome = form.nome.data
        db.session.add(categoria)
        db.session.commit()
        flash(f"Categoria \"{form.nome.data}\" adicionada", category='success')
        return redirect(url_for('categorias.lista'))

    return render_template('render_simple_slim_form.jinja2',
                           title="Adicionar nova categoria",
                           form=form)


@bp.route('/edit/<uuid:id_categoria>', methods=['GET', 'POST'])
@login_required
def edit(id_categoria):
    categoria = Categoria.get_by_id(id_categoria)
    if categoria is None:
        flash("Categoria inexistente", category='warning')
        return redirect(url_for('categorias.lista'))

    form = NovoEditCategoriaForm(request.values, obj=categoria)
    form.submit.label.text = "Alterar"

    if form.validate_on_submit():
        old = categoria.nome
        categoria.nome = form.nome.data
        db.session.commit()
        flash(f"Categoria alterada de \"{old}\" para \"{form.nome.data}\"",
              category='success')
        return redirect(url_for('categorias.lista'))

    return render_template('render_simple_slim_form.jinja2',
                           title="Alterar categoria",
                           form=form)


@bp.route('/remove/<uuid:id_categoria>', methods=['GET'])
@login_required
def remove(id_categoria):
    categoria = Categoria.get_by_id(id_categoria)
    if categoria is None:
        flash("Categorias inexistente", category='warning')
        return redirect(url_for('categorias.lista'))

    old = categoria.nome
    db.session.delete(categoria)
    db.session.commit()
    flash(f"Categoria \"{old}\" removida", category='success')
    return redirect(url_for('categorias.lista'))
