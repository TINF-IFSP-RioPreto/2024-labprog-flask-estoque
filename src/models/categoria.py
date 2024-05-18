import uuid

from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base_mixin import BasicRepositoryMixin, TimeStampMixin
from src.modules import db


class Categoria(db.Model, BasicRepositoryMixin, TimeStampMixin):
    __tablename__ = 'categorias'

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True),
                                     primary_key=True,
                                     default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60),
                                      index=True,
                                      nullable=False)

    lista_de_produtos = relationship('Produto',
                                     back_populates='categoria',
                                     lazy='select',
                                     cascade='all, delete-orphan')
