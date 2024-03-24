from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Email, EqualTo


class LoginForm(FlaskForm):
    email = StringField("Email",
                        validators=[InputRequired(message="É obrigatório informar o email do cadastro"),
                                    Email(message="Informe um email válido",
                                          check_deliverability=False)])
    password = PasswordField("Senha",
                             validators=[InputRequired(message="É necessário digitar a senha")])
    remember_me = BooleanField("Permanecer conectado?", default=False)
    submit = SubmitField("Entrar")


class SetNewPasswordForm(FlaskForm):
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
