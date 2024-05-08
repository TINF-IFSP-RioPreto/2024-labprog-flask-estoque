from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import EqualTo, InputRequired, Email


class LoginForm(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email do cadastro"),
                                    Email(message="Informe um email válido",
                                          check_deliverability=False)])
    password = PasswordField("Senha",
                             validators=[InputRequired(message="É necessário digitar a senha")])
    remember_me = BooleanField("Permanecer conectado?", default=False)
    submit = SubmitField("Entrar")


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email"),
                                    Email(message="Informe um email válido",
                                          check_deliverability=False)])
    submit = SubmitField("Pedir nova senha")


class NewPasswordForm(FlaskForm):
    password = PasswordField("Digite a nova senha",
                             validators=[InputRequired(message="É necessário digitar a senha")])
    password2 = PasswordField("Digite novamente a nova senha",
                             validators=[InputRequired(message="É necessário digitar a senha"),
                                         EqualTo('password',
                                                 message="As senhas precisam ser iguais")])
    submit = SubmitField("Mudar a senha")
