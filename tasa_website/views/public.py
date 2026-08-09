from flask import Blueprint, render_template

from ..extensions import db
from ..helpers import cabinet_member_dict, officer_sections
from ..models import CabinetMember, Family, Officer, Testimonial

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


@bp.route('/alumni')
def alumni():
    all_members = db.session.scalars(db.select(CabinetMember).order_by(CabinetMember.name)).all()
    members = [cabinet_member_dict(m) for m in all_members]
    # Distinct graduation years, newest first, for the filter dropdown.
    grad_years = sorted({m.grad_year for m in all_members if m.grad_year is not None}, reverse=True)
    return render_template('alumni.html', members=members, grad_years=grad_years)


@bp.route('/join')
def join():
    return render_template('join.html')


@bp.route('/donate')
def donate():
    return render_template('donate.html')
