from flask_wtf import FlaskForm
from wtforms import FloatField,StringField, IntegerField, SubmitField



class AddForm(FlaskForm):

    category = StringField('Category of Transaction:')
    description = StringField('Description of Transaction:')
    amount = FloatField('Amount of Transaction:')
    submit = SubmitField('Add Transaction')

class DelForm(FlaskForm):

    id = IntegerField('Id Number of Transaction to Remove:')
    submit = SubmitField('Remove Transaction')
