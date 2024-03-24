import smtplib
import uuid
from time import time
from hashlib import md5
from typing import Optional

import email_validator
import jwt
from flask import current_app
from flask_login import UserMixin
from flask_mailman import EmailMessage
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

    def create_jwt_token(self, action: str, expires_in: int = 600) -> str:
        payload = {
            'user': str(self.id),
            'action': action.lower(),
            'exp': time() + expires_in
        }
        return jwt.encode(payload=payload,
                          key=current_app.config.get('SECRET_KEY'),
                          algorithm='HS256')

    @staticmethod
    def verify_jwt_token(token):
        try:
            payload = jwt.decode(token,
                                 key=current_app.config.get('SECRET_KEY'),
                                 algorithms=['HS256'])
        except jwt.exceptions.PyJWTError as e:
            current_app.logger.error("JWT Token validation: %s" % (e))
            return None, None
        try:
            user_id = uuid.UUID(payload.get('user', None))
            action = payload.get('action', None)
        except ValueError:
            return None, None
        return User.get_by_id(user_id), action

    def send_email(self, subject: str = "Mensagem do sistema", body: str = "") -> bool:
        msg = EmailMessage()
        msg.to = [self.email]
        msg.subject = f"[{current_app.config.get('APP_NAME')}] {subject}"
        msg.body = body
        msg.extra_headers['Message-ID'] =\
            f"{str(uuid.uuid4())}@{current_app.config.get('APP_MTA_MESSAGEID')}"
        try:
            msg.send()
        except smtplib.SMTPException:
            return False
        else:
            return True
