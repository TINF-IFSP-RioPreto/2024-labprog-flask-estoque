import uuid
from typing import Optional

from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base_mixin import BasicRepositoryMixin, TimeStampMixin
from src.modules import db


class Produto(db.Model, TimeStampMixin, BasicRepositoryMixin):
    __tablename__ = 'produtos'
    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True),
                                     primary_key=True,
                                     default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    preco: Mapped[DECIMAL] = mapped_column(DECIMAL(10, 2), default=0.00)
    estoque: Mapped[Integer] = mapped_column(Integer, nullable=False, default=0)
    ativo: Mapped[Boolean] = mapped_column(Boolean, default=True)

    categoria_id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True),
                                               ForeignKey('categorias.id'))

    foto_base64: Mapped[Optional[Text]] = mapped_column(Text,
                                                        nullable=True)
    foto_mime: Mapped[String] = mapped_column(String(64),
                                              nullable=True)
    possui_foto: Mapped[Boolean] = mapped_column(Boolean,
                                                 default=False)

    categoria = relationship('Categoria',
                             back_populates='lista_de_produtos')
