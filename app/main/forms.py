from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, NumberRange
from flask_wtf.file import FileField, FileAllowed


class EditItemForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=512)])
    price = FloatField('Price', validators=[DataRequired()])
    group_id = IntegerField('Group id', validators=[DataRequired()])  # TODO: dropdown list of group names
    image = FileField('image', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')


class EditGroupForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[Length(min=0, max=512)])
    image = FileField('image', validators=[FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField('Submit')


class EditUserRightsForm(FlaskForm):
    level = IntegerField('Rights level', validators=[DataRequired(),
            NumberRange(min=1, max=3, message='Rights level can be 1 min, 3 max')])
    submit = SubmitField('Submit')