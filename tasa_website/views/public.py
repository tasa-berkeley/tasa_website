from flask import Blueprint, render_template

from ..extensions import db
from ..helpers import officer_sections
from ..models import Family, Officer, Testimonial

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/officers')
def officers():
    all_officers = db.session.scalars(db.select(Officer)).all()
    return render_template('officers.html', sections=officer_sections(all_officers))


@bp.route('/families')
def families():
    all_families = db.session.scalars(db.select(Family).order_by(Family.family_name)).all()
    return render_template('families.html', families=all_families)


@bp.route('/testimonials')
def testimonials():
    all_testimonials = db.session.scalars(db.select(Testimonial).order_by(Testimonial.name)).all()
    return render_template('testimonials.html', testimonials=all_testimonials)


@bp.route('/join')
def join():
    return render_template('join.html')


@bp.route('/donate')
def donate():
    return render_template('donate.html')
