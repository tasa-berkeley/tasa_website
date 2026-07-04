"""Flask CLI commands: flask init-db | import-legacy | hash-password"""
import sqlite3

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from .extensions import db
from .helpers import POSITIONS
from .models import Family, Officer


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
    skipped = []
    try:
        for row in old.execute('SELECT * FROM officers'):
            position = int(row['position'])
            if not 0 <= position < len(POSITIONS):
                skipped.append(f"officer '{row['name']}' has out-of-range position {position}")
                continue
            db.session.add(Officer(
                name=row['name'], year=int(row['year']), major=row['major'],
                position=position, image_url=row['image_url'],
                quote=row['quote'] or None, description=row['description'] or None,
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
    for line in skipped:
        click.echo(f'SKIPPED: {line}')


@click.command('hash-password')
def hash_password_command():
    """Hash a password for the ADMIN_PASSWORD_HASH entry in .env."""
    password = click.prompt('Password', hide_input=True, confirmation_prompt=True)
    click.echo(generate_password_hash(password))


def register(app):
    app.cli.add_command(init_db_command)
    app.cli.add_command(import_legacy_command)
    app.cli.add_command(hash_password_command)
