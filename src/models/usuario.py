import uuid
from hashlib import md5
from typing import Optional

import email_validator
from flask_login import UserMixin
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid, String, Boolean, DateTime
from werkzeug.security import generate_password_hash, check_password_hash

from src.models.base_mixin import TimeStampMixin, BasicRepositoryMixin
from src.modules import db


class User(db.Model, TimeStampMixin, UserMixin, BasicRepositoryMixin):
    __tablename__ = 'usuarios'

    id: Mapped[Uuid] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome: Mapped[str] = mapped_column(String(60), nullable=False)
    email_normalizado: Mapped[str] = mapped_column(String(256), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    email_validado: Mapped[Boolean] = mapped_column(Boolean, default=False)
    dta_validacao_email: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    dta_ultimo_acesso: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)
    dta_acesso_atual: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    ativo: Mapped[Boolean] = mapped_column(Boolean, default=False)

    @property
    def is_active(self):
        return self.ativo

    @property
    def email(self):
        return self.email_normalizado

    # noinspection PyTypeChecker
    @email.setter
    def email(self, value):
        self.email_normalizado = email_validator.validate_email(value, check_deliverability=False).normalized.lower()

    def url_gravatar(self, size=32):
        digest = md5(self.email.encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    # noinspection PyTypeChecker
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) -> bool:
        return check_password_hash(self.password_hash, password)

    @classmethod
    def get_by_email(cls, email):
        user_email = email_validator.validate_email(email, check_deliverability=False).normalized.lower()
        return cls.get_first_or_none_by('email_normalizado', user_email)
