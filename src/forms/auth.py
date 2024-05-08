from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email


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
