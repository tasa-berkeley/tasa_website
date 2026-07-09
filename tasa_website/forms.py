from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from .helpers import POSITIONS, SECTION_ORDER, position_section

_image_field = lambda label: FileField(
    label,
    validators=[Optional(), FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only (jpg, png, gif).')],
)


def _position_choices():
    """POSITIONS grouped into section optgroups so interns/roles are easy to pick."""
    groups = {}
    for i, title in enumerate(POSITIONS):
        groups.setdefault(position_section(i), []).append((i, title))
    return {section: groups[section] for section in SECTION_ORDER if section in groups}


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class OfficerForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    position = SelectField('Position', coerce=int, choices=_position_choices())
    major = StringField('Major', validators=[DataRequired(), Length(max=100)])
    year = StringField('Year (class standing)', validators=[DataRequired(), Length(max=20)])
    quote = TextAreaField('Quote (optional)', validators=[Optional()])
    description = TextAreaField('Description (optional)', validators=[Optional()])
    image = _image_field('Photo')


class FamilyForm(FlaskForm):
    family_name = StringField('Family name', validators=[DataRequired(), Length(max=100)])
    family_head1 = StringField('Family head 1', validators=[DataRequired(), Length(max=100)])
    family_head2 = StringField('Family head 2', validators=[DataRequired(), Length(max=100)])
    family_head_intern = StringField('Family head intern (optional)', validators=[Optional(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = _image_field('Family photo')


class TestimonialForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    position = StringField('Position(s)', validators=[DataRequired(), Length(max=200)])
    question = TextAreaField('Question', validators=[DataRequired()])
    response = TextAreaField('Response', validators=[DataRequired()])
    image = _image_field('Photo (optional)')
