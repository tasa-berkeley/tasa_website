import os
from datetime import date

from flask import Flask, render_template, request

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

    # Uploaded photos get random per-upload filenames (helpers.save_image), so a replaced
    # photo always gets a new url -> safe to cache forever ("immutable"). This stops reloads
    # of the officer/family photo grids from re-bursting OCF's nginx rate limiter. The
    # site/ and placeholders/ folders keep stable, edited-in-place names, so they are
    # excluded and keep Flask's default (revalidate).
    _uploaded_image_dirs = tuple(
        '/' + app.config[key].strip('/') + '/'
        for key in ('OFFICER_IMAGE_FOLDER', 'FAMILY_IMAGE_FOLDER', 'TESTIMONIAL_IMAGE_FOLDER')
    )

    @app.after_request
    def cache_uploaded_images(response):
        if request.path.startswith(_uploaded_image_dirs):
            response.cache_control.no_cache = None   # clear Flask static's default no-cache
            response.cache_control.public = True
            response.cache_control.max_age = 31536000  # 1 year
            response.cache_control.immutable = True
        return response

    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(error):
        return render_template('500.html'), 500

    return app
