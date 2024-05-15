import uuid
from sqlalchemy import String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.models.base_mixin import (BasicRepositoryMixin,
                                   TimeStampMixin)
from src.modules import db


class Categoria(db.Model, BasicRepositoryMixin, TimeStampMixin):
    __tablename__ = 'categorias'
    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True),
                                     primary_key=True,
                                     default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(128),
                                      nullable=False)
