from flask import Blueprint, render_template

from .. import content

bp = Blueprint('public', __name__)


@bp.route('/')
def index():
    return render_template('index.html')


@bp.route('/about')
def about():
    return render_template('about.html')


@bp.route('/officers')
def officers():
    return render_template('officers.html', sections=content.officer_sections())


@bp.route('/families')
def families():
    return render_template('families.html', families=content.families())


@bp.route('/testimonials')
def testimonials():
    return render_template('testimonials.html', testimonials=content.testimonials())


@bp.route('/join')
def join():
    return render_template('join.html')
