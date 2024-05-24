import uuid
from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import mapped_column, relationship
from src.modules import db
from src.models.base_mixin import BasicRepositoryMixin, TimeStampMixin
class Produto(db.Model, BasicRepositoryMixin, TimeStampMixin):
    __tablename__ = 'produtos'
    id = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = mapped_column(String(100), nullable=False, index=True)
    preco = mapped_column(DECIMAL(10, 2), default=0.00, nullable=False)
    estoque = mapped_column(Integer, default=0)
    ativo = mapped_column(Boolean, default=True, nullable=False)
    possui_foto = mapped_column(Boolean, default=False, nullable=False)
    foto_base64 = mapped_column(Text, default=None, nullable=True)
    foto_mime = mapped_column(String(64), nullable=True, default=None)
    categoria_id = mapped_column(Uuid(as_uuid=True), ForeignKey('categorias.id'))

    categoria = relationship('Categoria', back_populates='lista_de_produtos')
