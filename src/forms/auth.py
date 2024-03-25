import re

from flask import current_app
from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, EqualTo, ValidationError


class ValidaComplexidadeSenha:
    def validate_password(self, password):
        # Definição da complexidade da senha por expressões regulares
        expressoes = []
        min = current_app.config.get('PASSWORD_MIN', 8)
        max = current_app.config.get('PASSWORD_MAX', 64)
        expressoes.append(f'^(?=.{{{min},{max}}}$)')
        mensagem = f"A sua senha precisa ter entre {min} e {max} caracteres"

        upper = r'(?=.*[A-Z])'  # Pelo menos 1 letra maiúscula
        lower = r'(?=.*[a-z])'  # Pelo menos 1 letra minúscula
        number = r'(?=.*[0-9])'  # Pelo menos um número
        special = r"(?=.*[!@#\$%\&'\(\)*\+,\-./:;<=>?@\[\\\]^_`{|}~])"  # Pelo menos um caracter especial

        if current_app.config.get('PASSWORD_MAIUSCULA', False):
            expressoes.append(upper)
            mensagem = mensagem + ", letras maiúsculas"
        if current_app.config.get('PASSWORD_MINUSCULA', False):
            expressoes.append(lower)
            mensagem = mensagem + ", letras minúsculas"
        if current_app.config.get('PASSWORD_NUMERO', False):
            expressoes.append(number)
            mensagem = mensagem + ", números"
        if current_app.config.get('PASSWORD_SIMBOLO', False):
            expressoes.append(special)
            mensagem = mensagem + ", símbolos especiais"

        pattern = "".join(expressoes)
        print(password.data)
        print(pattern)
        # Trocar a última ocorrência de ', ' se houver por ' e ' na mensagem
        pos = mensagem.rfind(', ')
        if pos > -1: mensagem = mensagem[:pos] + ' e ' + mensagem[pos + 2:]

        print(mensagem)

        if not re.match(pattern, str(password.data)):
            raise ValidationError(mensagem)


class LoginForm(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email do cadastro"),
                                    Email(message="Informe um email válido",
                                          check_deliverability=False)])
    password = PasswordField("Senha",
                             validators=[InputRequired(message="É necessário digitar a senha")])
    remember_me = BooleanField("Permanecer conectado?", default=False)
    submit = SubmitField("Entrar")


class SetNewPasswordForm(FlaskForm, ValidaComplexidadeSenha):
    password = PasswordField("Nova senha",
                             validators=[InputRequired(message="É necessário escolher uma senha")])
    password2 = PasswordField("Confirme a nova senha",
                              validators=[InputRequired(message="É necessário repetir a nova senha"),
                                          EqualTo('password',
                                                  message="As senhão não são iguais")])
    submit = SubmitField("Cadastrar a nova senha")


class AskToResetPassword(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email para o qual"
                                                          " se deseja definir nova senha"),
                                    Email(message="Informe um email válido",
                                          check_deliverability=False)])
    submit = SubmitField("Redefinir a senha")


class RegistrationForm(FlaskForm, ValidaComplexidadeSenha):
    nome = StringField("Nome",
                       validators=[InputRequired(message="É obrigatório informar um nome para cadastro")])
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar um email para cadastro"),
                                    Email(message="Informe um email válido",
                                          check_deliverability=False)])
    password = PasswordField("Senha",
                             validators=[InputRequired(message="É necessário escolher uma senha")])
    password2 = PasswordField("Confirme a senha",
                              validators=[InputRequired(message="É necessário repetir a senha"),
                                          EqualTo('password',
                                                  message="As senhas não são iguais")])
    submit = SubmitField("Adicionar usuário")

    def validate_email(self, email):
        from src.models.usuario import User
        user = User.get_by_email(email.data)
        if user:
            raise ValidationError("Este email já está cadastrado")
