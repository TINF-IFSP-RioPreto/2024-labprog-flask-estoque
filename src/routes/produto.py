from base64 import b64encode

from flask import abort, Blueprint, flash, redirect, render_template, request, Response, url_for
from flask_login import login_required
from werkzeug.exceptions import NotFound

from src.forms.produto import ProdutoForm
from src.models.categoria import Categoria
from src.models.produto import Produto
from src.modules import db

bp = Blueprint('produto', __name__, url_prefix="/produto")


@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    if Categoria.is_empty():
        flash("Impossível adicionar produto. Adcione pelo menos uma categoria",
              category='warning')
        return redirect(url_for('categoria.add'))

    form = ProdutoForm()
    form.submit.label.text = "Adicionar produto"
    categorias = db.session.execute(db.select(Categoria).order_by(Categoria.nome)).scalars()
    form.categoria.choices = [(str(i.id), i.nome) for i in categorias]
    if form.validate_on_submit():
        produto = Produto(nome = form.nome.data, preco = form.preco.data,
                          ativo = form.ativo.data, estoque = form.estoque.data)
        if form.foto.data:
            produto.possui_foto = True
            produto.foto_base64 = (b64encode(request.files[form.foto.name].read()).
                                   decode('ascii'))
            produto.foto_mime = request.files[form.foto.name].mimetype
        else:
            produto.possui_foto = False
            produto.foto_base64 = None
            produto.foto_mime = None
        categoria = Categoria.get_by_id(form.categoria.data)
        if categoria is None:
            flash("Categoria inexistente!", category='danger')
            return redirect(url_for('produto.add'))
        produto.categoria = categoria
        db.session.add(produto)
        db.session.commit()
        flash("Produto adicionado!")
        return redirect(url_for('index'))

    return render_template('produto/add.jinja2', form=form,
                           title="Adicionar novo produto")


@bp.route('/edit/<uuid:produto_id>', methods=['GET', 'POST'])
@login_required
def edit(produto_id):
    produto = Produto.get_by_id(produto_id)
    if produto is None:
        flash("Produto inexistente", category='danger')
        return redirect(url_for('produto.lista'))

    form = ProdutoForm(obj=produto)
    form.submit.label.text = "Alterar produto"
    categorias = db.session.execute(db.select(Categoria).order_by(Categoria.nome)).scalars()
    form.categoria.choices = [(str(i.id), i.nome) for i in categorias]
    if form.validate_on_submit():
        produto.nome = form.nome.data
        produto.preco = form.preco.data
        produto.estoque = form.estoque.data
        produto.ativo = form.ativo.data
        categoria = Categoria.get_by_id(form.categoria.data)
        if form.removerfoto.data:
            produto.possui_foto = False
            produto.foto_mime = None
            produto.foto_base64 = None
        elif form.foto.data:
            produto.possui_foto = True
            produto.foto_base64 = (b64encode(request.files[form.foto.name].read()).
                                   decode('ascii'))
            produto.foto_mime = request.files[form.foto.name].mimetype
        if categoria is None:
            flash("Categoria inexistente!", category='danger')
            return redirect(url_for('produto.lista'))
        produto.categoria = categoria
        db.session.commit()
        flash("Produto alterado", category='success')
        return redirect(url_for('produto.lista'))

    form.categoria.process_data(str(produto.categoria_id))
    return render_template('produto/edit.jinja2', form=form,
                           title="Alterar um produto",
                           produto=produto)


@bp.route('/delete/<uuid:produto_id>', methods=['GET'])
@login_required
def delete(produto_id):
    produto = Produto.get_by_id(produto_id)
    if produto is None:
        flash("Produto inexistente", category='danger')
        return redirect(url_for('produto.lista'))

    db.session.delete(produto)
    db.session.commit()
    flash("Produto removido!", category='success')
    return redirect(url_for('produto.lista'))


@bp.route('/lista', methods=['GET', 'POST'])
@bp.route('/', methods=['GET', 'POST'])
def lista():
    page = request.args.get('page', type=int, default=1)
    pp = request.args.get('pp', type=int, default=25)

    sentenca = db.select(Produto).order_by(Produto.nome)

    try:
        rset = db.paginate(sentenca, page=page, per_page=pp, error_out=True)
    except NotFound:
        flash(f"Não temos produtos na página {page}. Apresentando página 1")
        page = 1
        rset = db.paginate(sentenca, page=page, per_page=pp, error_out=False)

    return render_template('produto/lista.jinja2',
                           title="Lista de produtos",
                           rset=rset,
                           page=page,
                           pp=pp)

@bp.route('/imagem/<uuid:id_produto>', methods=['GET'])
def imagem(id_produto):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return abort(404)
    conteudo, tipo = produto.imagem
    return Response(conteudo, mimetype=tipo)

@bp.route('/thumbnail/<uuid:id_produto>/<int:size>', methods=['GET'])
@bp.route('/thumbnail/<uuid:id_produto>', methods=['GET'])
def thumbnail(id_produto, size=128):
    produto = Produto.get_by_id(id_produto)
    if produto is None:
        return abort(404)
    conteudo, tipo = produto.thumbnail(size)
    return Response(conteudo, mimetype=tipo)
