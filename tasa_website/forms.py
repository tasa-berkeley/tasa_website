from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import IntegerField, PasswordField, SelectField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

from .helpers import POSITIONS, SEASONS, SECTION_ORDER, position_section

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


class CabinetForm(FlaskForm):
    # `big_id` choices are populated per-request in the admin view (0 == "no big"); Instagram
    # and LinkedIn are normalized in the view before saving.
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    grad_year = IntegerField('Graduation year (optional)',
                             validators=[Optional(), NumberRange(min=1950, max=2100)])
    role = StringField('Role / position(s) (optional)', validators=[Optional(), Length(max=200)])
    major = StringField('Major (optional)', validators=[Optional(), Length(max=120)])
    intern_season = SelectField('Intern class — season', choices=[('', '—')] + [(s, s) for s in SEASONS],
                                default='', validators=[Optional()])
    intern_year = IntegerField('Intern class — year', validators=[Optional(), NumberRange(min=1950, max=2100)])
    instagram = StringField('Instagram handle or URL (optional)', validators=[Optional(), Length(max=200)])
    email = StringField('Email (optional)', validators=[Optional(), Length(max=255)])
    linkedin = StringField('LinkedIn URL or handle (optional)', validators=[Optional(), Length(max=255)])
    bio = TextAreaField('Bio (optional)', validators=[Optional()])
    big_id = SelectField('Big (optional)', coerce=int, default=0)
    image = _image_field('Photo (optional)')
