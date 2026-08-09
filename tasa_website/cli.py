"""Flask CLI commands: flask init-db | import-legacy | seed-testimonials | sync-officers |
seed-cabinet-from-officers | hash-password"""
import os
import sqlite3

import click
from flask import current_app
from flask.cli import with_appcontext
from PIL import Image
from werkzeug.security import generate_password_hash

from .extensions import db
from .helpers import (IMAGE_MAXSIZE, POSITIONS, create_file_paths, generate_random_filename,
                      position_title)
from .models import CabinetMember, Family, Officer, Testimonial


@click.command('init-db')
@click.option('--drop', is_flag=True, help='Drop all tables first (deletes ALL data).')
@with_appcontext
def init_db_command(drop):
    """Create the database tables."""
    if drop:
        click.confirm('This will delete ALL data in the database. Continue?', abort=True)
        db.drop_all()
    db.create_all()
    click.echo('Initialized the database.')


@click.command('import-legacy')
@click.argument('old_db_path', type=click.Path(exists=True, dir_okay=False))
@click.option('--wipe', is_flag=True, help='Delete existing officers/families before importing.')
@with_appcontext
def import_legacy_command(old_db_path, wipe):
    """Copy officers and families from a pre-2026 tasa_website.db file."""
    db.create_all()
    if wipe:
        Officer.query.delete()
        Family.query.delete()
    elif db.session.query(Officer.id).first() or db.session.query(Family.id).first():
        raise click.ClickException('Target tables are not empty. Re-run with --wipe to replace them.')

    old = sqlite3.connect(old_db_path)
    old.row_factory = sqlite3.Row
    officers = families = 0
    warnings = []
    try:
        for row in old.execute('SELECT * FROM officers'):
            position = int(row['position'])
            # Keep ALL officers, even ones whose position falls outside POSITIONS
            # (the site renders those as a generic 'Officer'). Never drop a row.
            if not 0 <= position < len(POSITIONS):
                warnings.append(f"officer '{row['name']}' has out-of-range position {position} "
                                f"(kept; shows as generic 'Officer' — fix via the admin panel)")
            db.session.add(Officer(
                name=row['name'], year=row['year'], major=row['major'],
                position=position, image_url=row['image_url'],
                quote=row['quote'] or '', description=row['description'] or '',
            ))
            officers += 1
        for row in old.execute('SELECT * FROM families'):
            db.session.add(Family(
                family_name=row['family_name'], family_head1=row['family_head1'],
                family_head2=row['family_head2'],
                family_head_intern=row['family_head_intern'] or None,
                description=row['description'], image_url=row['image_url'],
            ))
            families += 1
    finally:
        old.close()

    db.session.commit()
    click.echo(f'Imported {officers} officers and {families} families.')
    for line in warnings:
        click.echo(f'NOTE: {line}')


@click.command('seed-testimonials')
@click.option('--wipe', is_flag=True, help='Delete existing testimonials before seeding.')
@with_appcontext
def seed_testimonials_command(wipe):
    """Seed the testimonials table from content.yaml.

    Testimonials have no rows in the legacy production DB, so unlike officers/families
    (which come from `import-legacy`) they are seeded from content.yaml.
    """
    from . import content

    db.create_all()
    if wipe:
        Testimonial.query.delete()
    elif db.session.query(Testimonial.id).first():
        raise click.ClickException('Testimonials table is not empty. Re-run with --wipe to replace them.')

    folder = current_app.config['TESTIMONIAL_IMAGE_FOLDER']
    count = 0
    for t in content.testimonials():
        photo = t.get('photo')
        db.session.add(Testimonial(
            name=t['name'], position=t.get('position') or '',
            question=t.get('question') or '', response=t.get('response') or '',
            image_url=(folder + '/' + photo) if photo else None,
        ))
        count += 1
    db.session.commit()
    click.echo(f'Seeded {count} testimonials from content.yaml.')


@click.command('sync-officers')
@with_appcontext
def sync_officers_command():
    """Update existing officers' position/major/year from content.yaml (matched by name).

    The legacy production DB carries a year-stale roster (old titles/majors/class years,
    quotes, and bios). content.yaml holds the current roster, so this refreshes the
    position, major, year, quote, and bio fields, plus the display order (content.yaml
    list order). Photos in the DB are left untouched, and no rows are added or deleted —
    only matched officers are updated.
    """
    from . import content

    yaml_officers = {}
    order = 0
    for people in (content._load().get('officers') or {}).values():
        for person in (people or []):
            person = dict(person, _order=order)
            order += 1
            yaml_officers[person['name'].strip()] = person

    updated = unmatched = 0
    unknown_positions = set()
    for officer in db.session.scalars(db.select(Officer)):
        person = yaml_officers.get(officer.name.strip())
        if person is None:
            unmatched += 1
            continue
        pos = person.get('position')
        if pos in POSITIONS:
            officer.position = POSITIONS.index(pos)
        elif pos:
            unknown_positions.add(pos)  # leave position unchanged if not a known title
        officer.major = person.get('major') or officer.major
        officer.year = person.get('year') or officer.year
        officer.quote = person.get('quote') or ''
        officer.description = person.get('bio') or ''
        officer.display_order = person['_order']
        updated += 1

    db.session.commit()
    click.echo(f'Updated {updated} officers from content.yaml '
               f'({unmatched} DB officers had no content.yaml match, left as-is).')
    for pos in sorted(unknown_positions):
        click.echo(f"NOTE: position '{pos}' is not in helpers.POSITIONS; add it there to set that title.")


def _copy_officer_photo(officer):
    """Duplicate an officer's photo into the cabinet folder as its own file. Returns the url or None.

    Cabinet members own an independent copy so replacing/deleting a cabinet photo never touches the
    officer's file (deletion is path-based).
    """
    if not officer.image_url:
        return None
    src = os.path.join(current_app.root_path, *officer.image_url.split('/'))
    if not os.path.exists(src):
        return None
    file_url, file_path = create_file_paths(
        current_app.config['CABINET_IMAGE_FOLDER'], generate_random_filename('jpg'))
    img = Image.open(src)
    img.thumbnail(IMAGE_MAXSIZE)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    img.save(file_path, format='JPEG', quality=95, optimize=True, progressive=True)
    return file_url


@click.command('seed-cabinet-from-officers')
@click.option('--wipe', is_flag=True, help='Delete existing cabinet members before seeding.')
@with_appcontext
def seed_cabinet_from_officers_command(wipe):
    """Populate the cabinet alumni directory from the current officers roster (one-time convenience).

    Copies each officer in as a cabinet member (name, role from their position, major, bio) with an
    independent copy of their photo. Grad year / Instagram / email / LinkedIn / big are left blank to
    fill in through the /admin panel.
    """
    db.create_all()
    if wipe:
        CabinetMember.query.delete()
    elif db.session.query(CabinetMember.id).first():
        raise click.ClickException('cabinet_members is not empty. Re-run with --wipe to replace it.')

    count = 0
    for officer in db.session.scalars(db.select(Officer)):
        db.session.add(CabinetMember(
            name=officer.name,
            role=position_title(officer.position),
            major=officer.major or None,
            bio=officer.description or None,
            image_url=_copy_officer_photo(officer),
        ))
        count += 1
    db.session.commit()
    click.echo(f'Seeded {count} cabinet members from officers '
               '(fill in grad year, Instagram, email, LinkedIn, and bigs via /admin).')


@click.command('hash-password')
def hash_password_command():
    """Hash a password for the ADMIN_PASSWORD_HASH entry in .env."""
    password = click.prompt('Password', hide_input=True, confirmation_prompt=True)
    click.echo(generate_password_hash(password))


def register(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(import_legacy_command)
    app.cli.add_command(seed_testimonials_command)
    app.cli.add_command(sync_officers_command)
    app.cli.add_command(seed_cabinet_from_officers_command)
    app.cli.add_command(hash_password_command)
