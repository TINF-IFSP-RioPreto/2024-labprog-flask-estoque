import smtplib
import uuid
from base64 import b64encode
from hashlib import md5
from io import BytesIO
from time import time
from typing import Optional

import email_validator
import jwt
import pyotp
from flask import current_app
from flask_login import UserMixin
from flask_mailman import EmailMessage
from qrcode.main import QRCode
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

    usa_2fa: Mapped[Boolean] = mapped_column(Boolean, default=False)
    otp_secret: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, default="")
    ultimo_otp: Mapped[Optional[str]] = mapped_column(String(6), nullable=True, default="")
    dta_ativacao_2fa: Mapped[Optional[DateTime]] = mapped_column(DateTime, nullable=True)

    @property
    def otp_secret_formatted(self) -> str:
        return " ".join(self.otp_secret[i:i + 4] for i in range(0, len(self.otp_secret), 4))

    @property
    def get_b64encoded_qr_totp_uri(self) -> str:
        qr = QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.get_totp_uri, optimize=0)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buffer = BytesIO()
        img.save(buffer)
        return b64encode(buffer.getvalue()).decode('UTF-8')

    @property
    def get_totp_uri(self) -> str:
        otp = pyotp.totp.TOTP(self.otp_secret)
        return otp.provisioning_uri(name=self.email,
                                    issuer_name=current_app.config.get('APP_NAME'))

    def verify_totp(self, token) -> bool:
        totp = pyotp.TOTP(self.otp_secret)
        return totp.verify(token, valid_window=1)

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
        msg.extra_headers['Message-ID'] = \
            f"{str(uuid.uuid4())}@{current_app.config.get('APP_MTA_MESSAGEID')}"
        try:
            msg.send()
        except smtplib.SMTPException:
            return False
        else:
            return True
