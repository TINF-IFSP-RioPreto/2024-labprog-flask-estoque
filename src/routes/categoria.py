from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from src.forms.categoria import EditCategoriaForm, NovoCategoriaForm
from src.modules import db
from src.models.categoria import Categoria
import sqlalchemy as sa

bp = Blueprint('categoria', __name__, url_prefix='/categoria')


@bp.route('/', methods=['GET'])
def lista():
    sentenca = sa.select(Categoria).order_by(Categoria.nome)
    rset = db.session.execute(sentenca).scalars()

    return render_template('categoria/lista.jinja2',
                           rset=rset)


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = NovoCategoriaForm()
    if form.validate_on_submit():
        categoria = Categoria()
        categoria.nome = form.nome.data
        db.session.add(categoria)
        db.session.commit()
        flash(f"Categoria '{form.nome.data}' adicionada")
        return redirect(url_for('categoria.lista'))

    return render_template('categoria/add_edit.jinja2',
                           title="Nova categoria",
                           form=form)

@bp.route('/edit/<uuid:id_categoria>', methods=['GET', 'POST'])
@login_required
def edit(id_categoria):
    categoria = Categoria.get_by_id(id_categoria)
    if categoria is None:
        flash("Categoria inexistente", category='warning')
        return redirect(url_for('categoria.lista'))

    form = EditCategoriaForm(request.values, obj=categoria)
    if form.validate_on_submit():
        categoria.nome = form.nome.data
        db.session.commit()
        flash("Categoria alterada", category='success')
        return redirect(url_for('categoria.lista'))

    return render_template('categoria/add_edit.jinja2',
                           title="Alterar categoria", form=form)

@bp.route('/del/<uuid:id_categoria>', methods=['GET', 'POST'])
@login_required
def remove(id_categoria):
    categoria = Categoria.get_by_id(id_categoria)
    if categoria is None:
        flash("Categoria inexistente", category='warning')
        return redirect(url_for('categoria.lista'))

    db.session.delete(categoria)
    db.session.commit()
    flash("Categoria removida", category='success')
    return redirect(url_for('categoria.lista'))
