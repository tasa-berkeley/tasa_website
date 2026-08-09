from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for

from ..extensions import db
from ..forms import CabinetForm, FamilyForm, OfficerForm, TestimonialForm
from ..helpers import (POSITIONS, SEASONS, cabinet_descendant_ids, delete_image,
                       normalize_instagram, normalize_linkedin, save_image, semester_sort_key)
from ..majors import MAJOR_CATEGORIES
from ..models import CabinetMember, CabinetTerm, Family, Officer, Testimonial
from .auth import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Columns each list page may be sorted by (query key -> model column).
_OFFICER_SORTS = {'name': Officer.name, 'position': Officer.position,
                  'major': Officer.major, 'year': Officer.year}
_FAMILY_SORTS = {'family_name': Family.family_name}
_TESTIMONIAL_SORTS = {'name': Testimonial.name, 'position': Testimonial.position}
_CABINET_SORTS = {'name': CabinetMember.name, 'grad_year': CabinetMember.grad_year,
                  'role': CabinetMember.role}


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
        'cabinet': db.session.query(CabinetMember.id).count(),
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


# --- Cabinet alumni (big/little lineage) --------------------------------

def _big_choices(exclude_id=None):
    """(value, label) options for the 'big' select — every member except `exclude_id`, plus a blank."""
    members = db.session.scalars(db.select(CabinetMember).order_by(CabinetMember.name)).all()
    choices = [(0, '— None (top of a lineage) —')]
    for m in members:
        if m.id == exclude_id:
            continue
        choices.append((m.id, m.name if m.grad_year is None else f'{m.name} ({m.grad_year})'))
    return choices


def _apply_cabinet_form(member, form):
    """Copy validated form fields onto `member`. Returns an error message, or None on success."""
    big_id = form.big_id.data or None
    if big_id and member.id is not None and (
            big_id == member.id or big_id in cabinet_descendant_ids(member)):
        return 'A member cannot be their own big, or the big of one of their own littles.'
    member.name = form.name.data.strip()
    member.grad_year = form.grad_year.data
    member.role = (form.role.data or '').strip() or None
    member.major = (form.major.data or '').strip() or None
    member.intern_season = form.intern_season.data or None
    member.intern_year = form.intern_year.data
    member.instagram = normalize_instagram(form.instagram.data)
    member.email = (form.email.data or '').strip() or None
    member.linkedin = normalize_linkedin(form.linkedin.data)
    member.bio = (form.bio.data or '').strip() or None
    member.big_id = big_id
    return None


def _apply_cabinet_terms(member):
    """Replace `member.terms` from the submitted term_* arrays (blank/invalid rows are skipped)."""
    terms = []
    for pos, season, year in zip(request.form.getlist('term_position[]'),
                                 request.form.getlist('term_season[]'),
                                 request.form.getlist('term_year[]')):
        pos, year = (pos or '').strip(), (year or '').strip()
        if not pos or not year:
            continue
        try:
            pos_i, yr = int(pos), int(year)
        except ValueError:
            continue
        if not (0 <= pos_i < len(POSITIONS)):
            continue
        terms.append(CabinetTerm(position=pos_i, season=season if season in SEASONS else 'Fall', year=yr))
    member.terms = terms   # cascade delete-orphan removes rows dropped from the form


def _term_rows_from_request():
    """Re-render helper: the submitted term rows (preserves input when the form fails validation)."""
    rows = []
    for pos, season, year in zip(request.form.getlist('term_position[]'),
                                 request.form.getlist('term_season[]'),
                                 request.form.getlist('term_year[]')):
        if (pos or '').strip() or (year or '').strip():
            rows.append({'position': pos, 'season': season or 'Fall', 'year': year})
    return rows


def _term_rows_from_member(member):
    ordered = sorted(member.terms, key=lambda t: semester_sort_key(t.season, t.year))
    return [{'position': str(t.position), 'season': t.season, 'year': t.year} for t in ordered]


@bp.route('/alumni')
@login_required
def alumni():
    all_members, sort, direction = _sorted(CabinetMember, _CABINET_SORTS, CabinetMember.name)
    return render_template('admin/alumni.html', members=all_members,
                           current_sort=sort, current_dir=direction)


@bp.route('/alumni/new', methods=('GET', 'POST'))
@login_required
def new_alumni():
    form = CabinetForm()
    form.big_id.choices = _big_choices()
    if form.validate_on_submit():
        member = CabinetMember()
        error = _apply_cabinet_form(member, form)
        if error:
            flash(error, 'error')
        else:
            if form.image.data:
                member.image_url = save_image(form.image.data, current_app.config['CABINET_IMAGE_FOLDER'])
            db.session.add(member)
            _apply_cabinet_terms(member)
            db.session.commit()
            flash(f'Added {member.name}.', 'success')
            return redirect(url_for('admin.alumni'))
    term_rows = _term_rows_from_request() if request.method == 'POST' else []
    return render_template('admin/alumni_form.html', form=form, member=None, term_rows=term_rows,
                           positions=list(enumerate(POSITIONS)), seasons=SEASONS,
                           major_categories=MAJOR_CATEGORIES)


@bp.route('/alumni/<int:member_id>/edit', methods=('GET', 'POST'))
@login_required
def edit_alumni(member_id):
    member = db.get_or_404(CabinetMember, member_id)
    form = CabinetForm(obj=member)
    form.big_id.choices = _big_choices(exclude_id=member.id)
    if request.method == 'GET':
        form.big_id.data = member.big_id or 0
    if form.validate_on_submit():
        error = _apply_cabinet_form(member, form)
        if error:
            flash(error, 'error')
        else:
            _replace_image(member, form, 'CABINET_IMAGE_FOLDER')
            _apply_cabinet_terms(member)
            db.session.commit()
            flash(f'Updated {member.name}.', 'success')
            return redirect(url_for('admin.alumni'))
    term_rows = _term_rows_from_request() if request.method == 'POST' else _term_rows_from_member(member)
    return render_template('admin/alumni_form.html', form=form, member=member, term_rows=term_rows,
                           positions=list(enumerate(POSITIONS)), seasons=SEASONS,
                           major_categories=MAJOR_CATEGORIES)


@bp.route('/alumni/<int:member_id>/delete', methods=('POST',))
@login_required
def delete_alumni(member_id):
    member = db.get_or_404(CabinetMember, member_id)
    for little in member.littles:   # re-parent littles to roots; never cascade-delete the subtree
        little.big_id = None
    delete_image(member.image_url)
    db.session.delete(member)
    db.session.commit()
    flash(f'Deleted {member.name}.', 'success')
    return redirect(url_for('admin.alumni'))
