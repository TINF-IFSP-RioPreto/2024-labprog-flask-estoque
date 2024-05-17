from flask_wtf import FlaskForm
from wtforms.fields.simple import StringField, SubmitField
from wtforms.validators import DataRequired


class NovoEditCategoriaForm(FlaskForm):
    nome = StringField("Nome da categoria",
                       validators=[DataRequired("É obrigatório indicar o nome da categoria")])

    submit = SubmitField()
    
