from datetime import date

from flask import Flask

from .config import Config


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    from .views import public
    app.register_blueprint(public.bp)

    from . import content

    @app.context_processor
    def inject_globals():
        return {
            'photo_url': content.photo_url,
            'site_image': content.site_image,
            'current_year': date.today().year,
        }

    return app
