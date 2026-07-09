import os
from datetime import date

from flask import Flask

from .config import Config
from .extensions import csrf, db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config.setdefault('SQLALCHEMY_DATABASE_URI', Config.database_uri(app.instance_path))
    if test_config:
        app.config.update(test_config)

    for key in ('OFFICER_IMAGE_FOLDER', 'FAMILY_IMAGE_FOLDER', 'TESTIMONIAL_IMAGE_FOLDER'):
        os.makedirs(os.path.join(app.root_path, *app.config[key].split('/')), exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from .views import admin, auth, public
    app.register_blueprint(public.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp)

    from . import cli, content, helpers
    cli.register(app)

    @app.context_processor
    def inject_globals():
        return {
            # DB-backed pages (officers/families/testimonials) use these:
            'position_title': helpers.position_title,
            'static_image': helpers.static_image,
            # Static home/about pages still use the content.yaml filename convention:
            'photo_url': content.photo_url,
            'site_image': content.site_image,
            'current_year': date.today().year,
        }

    return app
