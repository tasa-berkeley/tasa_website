from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..forms import FamilyForm, OfficerForm, TestimonialForm
from ..helpers import delete_image, save_image
from ..models import Family, Officer, Testimonial
from .auth import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Columns each list page may be sorted by (query key -> model column).
_OFFICER_SORTS = {'name': Officer.name, 'position': Officer.position,
                  'major': Officer.major, 'year': Officer.year}
_FAMILY_SORTS = {'family_name': Family.family_name}
_TESTIMONIAL_SORTS = {'name': Testimonial.name, 'position': Testimonial.position}


def _sorted(model, allowed, *default_order):
    """Build an ordered select for `model`, honoring ?sort=&dir= against an allow-list."""
    sort = request.args.get('sort')
    direction = request.args.get('dir', 'asc')
    if direction not in ('asc', 'desc'):
        direction = 'asc'
    col = allowed.get(sort)
    query = db.select(model)
    if col is not None:
        query = query.order_by(col.desc() if direction == 'desc' else col.asc())
    else:
        sort = None
        query = query.order_by(*default_order)
    return db.session.scalars(query).all(), sort, direction


@bp.route('/')
@login_required
def dashboard():
    counts = {
        'officers': db.session.query(Officer.id).count(),
        'families': db.session.query(Family.id).count(),
        'testimonials': db.session.query(Testimonial.id).count(),
    }
    return render_template('admin/dashboard.html', counts=counts)


def _replace_image(entity, form, folder_key):
    """Save a newly uploaded image (if any) and return True if one was set."""
    if not form.image.data:
        return False
    delete_image(entity.image_url)
    entity.image_url = save_image(form.image.data, current_app.config[folder_key])
    return True


# --- Officers -----------------------------------------------------------

@bp.route('/officers')
@login_required
def officers():
    all_officers, sort, direction = _sorted(
        Officer, _OFFICER_SORTS, Officer.position, Officer.display_order, Officer.name)
    return render_template('admin/officers.html', officers=all_officers,
                           current_sort=sort, current_dir=direction)


@bp.route('/officers/new', methods=('GET', 'POST'))
@login_required
def new_officer():
    form = OfficerForm()
    if form.validate_on_submit():
        if not form.image.data:
            form.image.errors.append('A photo is required.')
        else:
            officer = Officer(
                name=form.name.data, year=form.year.data, major=form.major.data,
                position=form.position.data, quote=form.quote.data or '',
                description=form.description.data or '',
                display_order=(db.session.scalar(db.func.max(Officer.display_order)) or 0) + 1,
                image_url=save_image(form.image.data, current_app.config['OFFICER_IMAGE_FOLDER']),
            )
            db.session.add(officer)
            db.session.commit()
            flash(f'Added officer {officer.name}.', 'success')
            return redirect(url_for('admin.officers'))
    return render_template('admin/officer_form.html', form=form, officer=None)


@bp.route('/officers/<int:officer_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_officer(officer_id):
    officer = db.get_or_404(Officer, officer_id)
    form = OfficerForm(obj=officer)
    if form.validate_on_submit():
        officer.name = form.name.data
        officer.year = form.year.data
        officer.major = form.major.data
        officer.position = form.position.data
        officer.quote = form.quote.data or ''
        officer.description = form.description.data or ''
        _replace_image(officer, form, 'OFFICER_IMAGE_FOLDER')
        db.session.commit()
        flash(f'Updated officer {officer.name}.', 'success')
        return redirect(url_for('admin.officers'))
    return render_template('admin/officer_form.html', form=form, officer=officer)


@bp.route('/officers/<int:officer_id>/delete', methods=('POST',))
@login_required
def delete_officer(officer_id):
    officer = db.get_or_404(Officer, officer_id)
    delete_image(officer.image_url)
    db.session.delete(officer)
    db.session.commit()
    flash(f'Deleted officer {officer.name}.', 'success')
    return redirect(url_for('admin.officers'))


# --- Families -----------------------------------------------------------

@bp.route('/families')
@login_required
def families():
    all_families, sort, direction = _sorted(Family, _FAMILY_SORTS, Family.family_name)
    return render_template('admin/families.html', families=all_families,
                           current_sort=sort, current_dir=direction)


@bp.route('/families/new', methods=('GET', 'POST'))
@login_required
def new_family():
    form = FamilyForm()
    if form.validate_on_submit():
        if not form.image.data:
            form.image.errors.append('A family photo is required.')
        else:
            family = Family(
                family_name=form.family_name.data,
                family_head1=form.family_head1.data,
                family_head2=form.family_head2.data,
                family_head_intern=form.family_head_intern.data or None,
                description=form.description.data,
                image_url=save_image(form.image.data, current_app.config['FAMILY_IMAGE_FOLDER']),
            )
            db.session.add(family)
            db.session.commit()
            flash(f'Added family {family.family_name}.', 'success')
            return redirect(url_for('admin.families'))
    return render_template('admin/family_form.html', form=form, family=None)


@bp.route('/families/<int:family_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_family(family_id):
    family = db.get_or_404(Family, family_id)
    form = FamilyForm(obj=family)
    if form.validate_on_submit():
        family.family_name = form.family_name.data
        family.family_head1 = form.family_head1.data
        family.family_head2 = form.family_head2.data
        family.family_head_intern = form.family_head_intern.data or None
        family.description = form.description.data
        _replace_image(family, form, 'FAMILY_IMAGE_FOLDER')
        db.session.commit()
        flash(f'Updated family {family.family_name}.', 'success')
        return redirect(url_for('admin.families'))
    return render_template('admin/family_form.html', form=form, family=family)


@bp.route('/families/<int:family_id>/delete', methods=('POST',))
@login_required
def delete_family(family_id):
    family = db.get_or_404(Family, family_id)
    delete_image(family.image_url)
    db.session.delete(family)
    db.session.commit()
    flash(f'Deleted family {family.family_name}.', 'success')
    return redirect(url_for('admin.families'))


# --- Testimonials -------------------------------------------------------

@bp.route('/testimonials')
@login_required
def testimonials():
    all_testimonials, sort, direction = _sorted(Testimonial, _TESTIMONIAL_SORTS, Testimonial.name)
    return render_template('admin/testimonials.html', testimonials=all_testimonials,
                           current_sort=sort, current_dir=direction)


@bp.route('/testimonials/new', methods=('GET', 'POST'))
@login_required
def new_testimonial():
    form = TestimonialForm()
    if form.validate_on_submit():
        testimonial = Testimonial(
            name=form.name.data, position=form.position.data,
            question=form.question.data, response=form.response.data,
        )
        if form.image.data:
            testimonial.image_url = save_image(form.image.data, current_app.config['TESTIMONIAL_IMAGE_FOLDER'])
        db.session.add(testimonial)
        db.session.commit()
        flash(f'Added testimonial from {testimonial.name}.', 'success')
        return redirect(url_for('admin.testimonials'))
    return render_template('admin/testimonial_form.html', form=form, testimonial=None)


@bp.route('/testimonials/<int:testimonial_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_testimonial(testimonial_id):
    testimonial = db.get_or_404(Testimonial, testimonial_id)
    form = TestimonialForm(obj=testimonial)
    if form.validate_on_submit():
        testimonial.name = form.name.data
        testimonial.position = form.position.data
        testimonial.question = form.question.data
        testimonial.response = form.response.data
        _replace_image(testimonial, form, 'TESTIMONIAL_IMAGE_FOLDER')
        db.session.commit()
        flash(f'Updated testimonial from {testimonial.name}.', 'success')
        return redirect(url_for('admin.testimonials'))
    return render_template('admin/testimonial_form.html', form=form, testimonial=testimonial)


@bp.route('/testimonials/<int:testimonial_id>/delete', methods=('POST',))
@login_required
def delete_testimonial(testimonial_id):
    testimonial = db.get_or_404(Testimonial, testimonial_id)
    delete_image(testimonial.image_url)
    db.session.delete(testimonial)
    db.session.commit()
    flash(f'Deleted testimonial from {testimonial.name}.', 'success')
    return redirect(url_for('admin.testimonials'))
